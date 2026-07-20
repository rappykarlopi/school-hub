"""
LBYCPG3 – Computer Engineering Enlistment and Scheduler System
views.py  |  Phase 3: Core Views & Engine Workflows

Flow coverage:
  - Role-aware Login / Logout
  - Student:  Dashboard → Browse Subjects → Add to Cart → Confirm Enlistment → Print
  - Faculty:  Dashboard → Schedule Grid → Class List
  - Shared:   Error helpers, access guards
"""

from io import BytesIO

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    AcademicTerm, Enrollment, Faculty,
    Schedule, Student, Subject, User,
)


# ─────────────────────────────────────────────
#  Access Guard Decorators
# ─────────────────────────────────────────────

def student_required(view_fn):
    """Allow only authenticated Students."""
    @login_required(login_url="login")
    def wrapper(request, *args, **kwargs):
        if not request.user.is_student:
            messages.error(request, "This area is for students only.")
            return redirect("login")
        try:
            request.student = request.user.student_profile
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found. Contact the administrator.")
            return redirect("login")
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


def faculty_required(view_fn):
    """Allow only authenticated Faculty."""
    @login_required(login_url="login")
    def wrapper(request, *args, **kwargs):
        if not request.user.is_faculty:
            messages.error(request, "This area is for faculty members only.")
            return redirect("login")
        try:
            request.faculty = request.user.faculty_profile
        except Faculty.DoesNotExist:
            messages.error(request, "Faculty profile not found. Contact the administrator.")
            return redirect("login")
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


# ─────────────────────────────────────────────
#  Utility: Active Term Resolver
# ─────────────────────────────────────────────

def _get_active_term():
    """Return the currently active AcademicTerm or None."""
    return AcademicTerm.objects.filter(is_active=True).first()


# ═════════════════════════════════════════════
#  AUTH VIEWS
# ═════════════════════════════════════════════

def login_view(request):
    """
    Custom login that redirects based on user.role:
      admin   → /admin/
      faculty → /faculty/dashboard/
      student → /student/dashboard/
    """
    if request.user.is_authenticated:
        return _role_redirect(request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user     = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return _role_redirect(user)

        messages.error(request, "Invalid username or password. Please try again.")

    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


def _role_redirect(user):
    """Return the appropriate redirect response for a given user's role."""
    if user.is_admin or user.is_staff:
        return redirect("/admin/")
    if user.is_faculty:
        return redirect("faculty_dashboard")
    if user.is_student:
        return redirect("student_dashboard")
    return redirect("login")


# ═════════════════════════════════════════════
#  STUDENT VIEWS  –  10-Step Enlistment Flow
# ═════════════════════════════════════════════

# ── Step 1-2: Login + Select Term (term auto-resolved from active term) ──────

@student_required
def student_dashboard(request):
    """
    Student home page.
    Displays confirmed enrollments, cart, and total units summary.
    """
    student = request.student
    term    = _get_active_term()

    cart_enrollments = []
    confirmed_enrollments = []
    total_confirmed_units = 0
    total_cart_units = 0

    if term:
        confirmed_enrollments = (
            Enrollment.objects
            .filter(student=student, schedule__term=term, status=Enrollment.Status.CONFIRMED)
            .select_related("schedule__subject", "schedule__room", "schedule__faculty")
            .order_by("schedule__day", "schedule__time_start")
        )
        cart_enrollments = (
            Enrollment.objects
            .filter(student=student, schedule__term=term, status=Enrollment.Status.CART)
            .select_related("schedule__subject", "schedule__room", "schedule__faculty")
            .order_by("schedule__day", "schedule__time_start")
        )
        total_confirmed_units = sum(e.schedule.subject.units for e in confirmed_enrollments)
        total_cart_units      = sum(e.schedule.subject.units for e in cart_enrollments)

    context = {
        "student":               student,
        "term":                  term,
        "confirmed_enrollments": confirmed_enrollments,
        "cart_enrollments":      cart_enrollments,
        "total_confirmed_units": total_confirmed_units,
        "total_cart_units":      total_cart_units,
    }
    return render(request, "core/student/dashboard.html", context)


# ── Steps 3-4: View Available Subjects & Select ──────────────────────────────

@student_required
def subject_list(request):
    """
    Shows all Schedule offerings for the active term.
    Supports search by subject code / title / faculty name.
    Marks offerings already in the student's cart or confirmed.
    """
    student  = request.student
    term     = _get_active_term()
    schedules = Schedule.objects.none()
    enrolled_schedule_ids = set()

    query = request.GET.get("q", "").strip()

    if term:
        schedules = (
            Schedule.objects
            .filter(term=term, subject__term_number=term.term_number)
            .select_related("subject", "faculty", "room", "term")
            .order_by("subject__subject_code", "day", "time_start")
        )

        if query:
            schedules = schedules.filter(
                Q(subject__subject_code__icontains=query)
                | Q(subject__subject_title__icontains=query)
                | Q(faculty__last_name__icontains=query)
                | Q(faculty__first_name__icontains=query)
            )

        enrolled_schedule_ids = set(
            Enrollment.objects
            .filter(student=student, schedule__term=term)
            .values_list("schedule_id", flat=True)
        )

    context = {
        "term":                  term,
        "schedules":             schedules,
        "enrolled_schedule_ids": enrolled_schedule_ids,
        "query":                 query,
        "term_number":           term.get_term_number_display() if term else None,
    }
    return render(request, "core/student/subject_list.html", context)


# ── Step 5-6: Prerequisite + Conflict Check → Add to Cart ───────────────────

@student_required
@require_POST
def add_to_cart(request, schedule_id):
    """
    Instantiates an Enrollment with status='Cart'.
    The Enrollment.clean() method handles:
      • Prerequisite validation
      • Duplicate subject detection
      • Time-overlap conflict detection
    """
    student  = request.student
    term     = _get_active_term()

    if not term:
        messages.error(request, "No active enrollment term. Contact the administrator.")
        return redirect("subject_list")

    schedule = get_object_or_404(Schedule, pk=schedule_id, term=term)

    # Prevent re-adding something already in cart / confirmed
    if Enrollment.objects.filter(student=student, schedule=schedule).exists():
        messages.warning(request, f"'{schedule.subject.subject_code}' is already in your cart or enrolled list.")
        return redirect("subject_list")

    enrollment = Enrollment(
        student=student,
        schedule=schedule,
        status=Enrollment.Status.CART,
    )

    try:
        enrollment.full_clean(exclude={"schedule"})
        enrollment.save()
        messages.success(
            request,
            f"✓ '{schedule.subject.subject_code} – {schedule.subject.subject_title}' "
            f"added to your cart."
        )
    except ValidationError as exc:
        for field, errs in (exc.message_dict.items() if hasattr(exc, "message_dict") else [("__all__", exc.messages)]):
            for msg in (errs if isinstance(errs, list) else [errs]):
                messages.error(request, str(msg))

    return redirect("subject_list")


# ── Step 6b: Remove from Cart ────────────────────────────────────────────────

@student_required
@require_POST
def remove_from_cart(request, enrollment_id):
    """Delete a cart-status enrollment."""
    student    = request.student
    enrollment = get_object_or_404(
        Enrollment, pk=enrollment_id,
        student=student,
        status=Enrollment.Status.CART,
    )
    subject_code = enrollment.schedule.subject.subject_code
    enrollment.delete()
    messages.success(request, f"'{subject_code}' removed from your cart.")
    return redirect("student_dashboard")


# ── Steps 7-10: Confirm Enlistment ──────────────────────────────────────────

@student_required
@require_POST
def confirm_enlistment(request):
    """
    Atomically confirms all 'Cart' enrollments for the active term.

    For each cart item:
      1. Re-check available_slots > 0 (inside a SELECT FOR UPDATE lock)
      2. Decrement available_slots
      3. Flip status → 'Confirmed'
      4. Cascade saves atomically

    If ANY slot runs out, the entire transaction rolls back.
    """
    student = request.student
    term    = _get_active_term()

    if not term:
        messages.error(request, "No active enrollment term.")
        return redirect("student_dashboard")

    cart_items = list(
        Enrollment.objects.filter(
            student=student,
            schedule__term=term,
            status=Enrollment.Status.CART,
        ).select_related("schedule__subject")
    )

    if not cart_items:
        messages.warning(request, "Your cart is empty. Add subjects before confirming.")
        return redirect("student_dashboard")

    validation_errors = Enrollment.validate_cart(student, term, cart_items)
    if validation_errors:
        for msg in validation_errors:
            messages.error(request, msg)
        return redirect("student_dashboard")

    confirmed_codes = []
    errors          = []

    try:
        with transaction.atomic():
            for item in cart_items:
                # Lock the Schedule row to prevent race conditions
                schedule = (
                    Schedule.objects
                    .select_for_update()
                    .get(pk=item.schedule_id)
                )

                if schedule.available_slots <= 0:
                    # Roll back everything if any subject is full
                    raise ValidationError(
                        f"'{schedule.subject.subject_code}' has no more available slots. "
                        f"Your enlistment was NOT saved. Remove the full subject and try again."
                    )

                schedule.available_slots -= 1
                schedule.save(update_fields=["available_slots"])

                item.status      = Enrollment.Status.CONFIRMED
                item.enrolled_at = timezone.now()
                # Skip full_clean here: we already validated on add_to_cart;
                # we're only changing status & enrolled_at, not the schedule link.
                Enrollment.objects.filter(pk=item.pk).update(
                    status=Enrollment.Status.CONFIRMED,
                    enrolled_at=item.enrolled_at,
                )
                confirmed_codes.append(schedule.subject.subject_code)

    except ValidationError as exc:
        for msg in exc.messages:
            messages.error(request, msg)
        return redirect("student_dashboard")

    subjects_str = ", ".join(confirmed_codes)
    messages.success(
        request,
        f"✓ Enlistment confirmed for: {subjects_str}. "
        f"You may now print your enrollment form."
    )
    return redirect("enrollment_form")


# ── Step 10: Print Enrollment Form ──────────────────────────────────────────


def _get_enrollment_form_context(request):
    student = request.student
    term = _get_active_term()

    confirmed = []
    total_units = 0

    if term:
        confirmed = (
            Enrollment.objects
            .filter(student=student, schedule__term=term, status=Enrollment.Status.CONFIRMED)
            .select_related("schedule__subject", "schedule__faculty", "schedule__room")
            .order_by("schedule__day", "schedule__time_start")
        )
        total_units = sum(e.schedule.subject.units for e in confirmed)

    return {
        "student": student,
        "term": term,
        "confirmed": confirmed,
        "total_units": total_units,
        "now": timezone.now(),
    }


@student_required
def enrollment_form(request):
    """
    Renders a printable enrollment form showing all confirmed subjects
    for the active term.
    """
    context = _get_enrollment_form_context(request)
    return render(request, "core/student/enrollment_form.html", context)


@student_required
def enrollment_form_pdf(request):
    """Generate an official-looking PDF enrollment form for download."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    context = _get_enrollment_form_context(request)
    student = context["student"]
    term = context["term"]
    confirmed = context["confirmed"]
    total_units = context["total_units"]
    now = context["now"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#1e3a8a"),
        leading=22,
        alignment=TA_LEFT,
    )
    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#334155"),
        leading=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        leading=13,
    )
    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        leading=11,
    )

    story = []
    story.append(Paragraph("ENROLLMENT FORM", title_style))
    story.append(Paragraph("Computer Engineering Department", body_style))
    story.append(Paragraph("De La Salle University Manila", small_style))
    story.append(Spacer(1, 0.2 * inch))

    info_data = [
        [Paragraph("Student Name", heading_style), Paragraph(student.full_name, body_style)],
        [Paragraph("Student Number", heading_style), Paragraph(student.student_number, body_style)],
        [Paragraph("Program", heading_style), Paragraph(student.program, body_style)],
        [Paragraph("Academic Term", heading_style), Paragraph(term.term_name if term else "—", body_style)],
        [Paragraph("Date Generated", heading_style), Paragraph(now.strftime("%B %d, %Y %I:%M %p"), body_style)],
    ]
    info_table = Table(info_data, colWidths=[1.8 * inch, 4.8 * inch])
    info_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(info_table)
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Enrolled Subjects", heading_style))

    if confirmed:
        table_data = [[
            Paragraph("#", heading_style),
            Paragraph("Code", heading_style),
            Paragraph("Subject Title", heading_style),
            Paragraph("Schedule", heading_style),
            Paragraph("Room", heading_style),
            Paragraph("Faculty", heading_style),
            Paragraph("Term", heading_style),
            Paragraph("Units", heading_style),
        ]]

        for index, enrollment in enumerate(confirmed, start=1):
            table_data.append([
                Paragraph(str(index), body_style),
                Paragraph(enrollment.schedule.subject.subject_code, body_style),
                Paragraph(enrollment.schedule.subject.subject_title, body_style),
                Paragraph(
                    f"{enrollment.schedule.get_day_display()}\n{enrollment.schedule.time_start.strftime('%I:%M %p')} – {enrollment.schedule.time_end.strftime('%I:%M %p')}",
                    body_style,
                ),
                Paragraph(enrollment.schedule.room.room_name, body_style),
                Paragraph(enrollment.schedule.faculty.full_name, body_style),
                Paragraph(enrollment.schedule.subject.get_term_number_display(), body_style),
                Paragraph(str(enrollment.schedule.subject.units), body_style),
            ])

        subject_table = Table(
            table_data,
            colWidths=[0.35 * inch, 0.7 * inch, 1.85 * inch, 1.05 * inch, 0.7 * inch, 1.0 * inch, 0.6 * inch, 0.45 * inch],
        )
        subject_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (-1, -1), (-1, -1), colors.HexColor("#f8fafc")),
            ])
        )
        story.append(subject_table)
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"<b>Total Units:</b> {total_units}",
                heading_style,
            )
        )
    else:
        story.append(Paragraph("No confirmed enrollments found for this term.", body_style))

    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph("Student Signature _________________________", small_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Adviser Signature _________________________", small_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Registrar Signature _________________________", small_style))

    doc.build(story)

    pdf_value = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_value, content_type="application/pdf")
    response["Content-Disposition"] = (
        f"attachment; filename=enrollment-form-{student.student_number}.pdf"
    )
    return response


# ── Weekly Schedule View ─────────────────────────────────────────────────────

@student_required
def student_schedule(request):
    """
    Displays a weekly schedule grid for the student's confirmed enrollments
    in the active term.
    """
    student = request.student
    term    = _get_active_term()

    days_order = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
    day_labels = {
        "MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday",
        "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday",
    }

    # Build day → list of enrollments mapping
    schedule_by_day = {day: [] for day in days_order}

    if term:
        enrollments = (
            Enrollment.objects
            .filter(student=student, schedule__term=term, status=Enrollment.Status.CONFIRMED)
            .select_related("schedule__subject", "schedule__faculty", "schedule__room")
            .order_by("schedule__time_start")
        )
        for enr in enrollments:
            schedule_by_day[enr.schedule.day].append(enr)

    context = {
        "term":           term,
        "schedule_by_day": schedule_by_day,
        "days_order":     days_order,
        "day_labels":     day_labels,
    }
    return render(request, "core/student/schedule.html", context)


# ═════════════════════════════════════════════
#  FACULTY VIEWS
# ═════════════════════════════════════════════

@faculty_required
def faculty_dashboard(request):
    """
    Faculty home page.
    Shows teaching load summary and quick stats for the active term.
    """
    faculty = request.faculty
    term    = _get_active_term()

    schedules = []
    total_units = 0

    if term:
        schedules = (
            Schedule.objects
            .filter(faculty=faculty, term=term)
            .select_related("subject", "room")
            .order_by("day", "time_start")
        )
        total_units = sum(s.subject.units for s in schedules)

    context = {
        "faculty":    faculty,
        "term":       term,
        "schedules":  schedules,
        "total_units": total_units,
    }
    return render(request, "core/faculty/dashboard.html", context)


@faculty_required
def faculty_schedule(request):
    """
    Detailed weekly schedule grid for the logged-in faculty member.
    """
    faculty = request.faculty
    term    = _get_active_term()

    days_order = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
    day_labels = {
        "MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday",
        "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday",
    }

    schedule_by_day = {day: [] for day in days_order}

    if term:
        schedules = (
            Schedule.objects
            .filter(faculty=faculty, term=term)
            .select_related("subject", "room")
            .order_by("time_start")
        )
        for s in schedules:
            schedule_by_day[s.day].append(s)

    context = {
        "faculty":         faculty,
        "term":            term,
        "schedule_by_day": schedule_by_day,
        "days_order":      days_order,
        "day_labels":      day_labels,
    }
    return render(request, "core/faculty/schedule.html", context)


@faculty_required
def faculty_class_list(request):
    """
    Shows all Schedule sections assigned to the faculty for the active term,
    with the full list of confirmed enrolled students per section.
    Supports filtering by specific schedule section.
    """
    faculty = request.faculty
    term    = _get_active_term()

    sections = []

    if term:
        raw_sections = (
            Schedule.objects
            .filter(faculty=faculty, term=term)
            .select_related("subject", "room")
            .order_by("subject__subject_code", "day", "time_start")
        )

        for sec in raw_sections:
            enrolled_students = (
                Enrollment.objects
                .filter(schedule=sec, status=Enrollment.Status.CONFIRMED)
                .select_related("student")
                .order_by("student__last_name", "student__first_name")
            )
            sections.append({
                "schedule":  sec,
                "students":  enrolled_students,
                "count":     enrolled_students.count(),
            })

    context = {
        "faculty":  faculty,
        "term":     term,
        "sections": sections,
    }
    return render(request, "core/faculty/class_list.html", context)
