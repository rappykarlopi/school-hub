"""
LBYCPG3 – Computer Engineering Enlistment and Scheduler System
admin.py  |  Phase 2: Django Admin Auto-Generation
Covers 100% of the Administrator functional requirements out of the box.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Sum, Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import (
    User, Faculty, Student, Subject,
    Room, AcademicTerm, Schedule, Enrollment,
)


# ─────────────────────────────────────────────
#  Inline helpers
# ─────────────────────────────────────────────

class FacultyInline(admin.StackedInline):
    model  = Faculty
    extra  = 1
    max_num = 1
    can_delete = False
    verbose_name_plural = "Faculty Profile"
    fields = ("first_name", "last_name", "department", "max_teaching_load")


class StudentInline(admin.StackedInline):
    model  = Student
    extra  = 1
    max_num = 1
    can_delete = False
    verbose_name_plural = "Student Profile"
    fields = ("student_number", "first_name", "last_name", "program")


class EnrollmentInline(admin.TabularInline):
    model       = Enrollment
    extra       = 0
    fields      = ("schedule", "status", "enrolled_at")
    readonly_fields = ("enrolled_at",)
    show_change_link = True


# ─────────────────────────────────────────────
#  1. USER ADMIN
# ─────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Extends the built-in UserAdmin to expose the role field."""

    # Add role to the fieldsets (edit page)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("LBYCPG3 Role", {"fields": ("role",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("LBYCPG3 Role", {"fields": ("role",)}),
    )

    list_display  = ("username", "email", "role", "is_active", "is_staff", "date_joined")
    list_filter   = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering      = ("username",)

    def get_fieldsets(self, request, obj=None):
        """
        Faculty/Student accounts don't need Django's is_staff/is_superuser/
        groups/user_permissions section — that's only relevant for
        `admin`-role accounts that actually log into this admin site.
        Once the user is saved (obj exists) and isn't an admin, drop that
        whole fieldset so the follow-up screen only shows what matters:
        personal info, role, and the Faculty/Student profile below it.
        """
        fieldsets = super().get_fieldsets(request, obj)

        if obj is not None and obj.role != User.Role.ADMIN:
            fieldsets = tuple(
                (name, opts)
                for name, opts in fieldsets
                if "groups" not in opts.get("fields", ())
                and "user_permissions" not in opts.get("fields", ())
            )

        return fieldsets

    # Conditionally show the appropriate inline.
    #
    # On the Add page (obj is None) the User doesn't have a role committed
    # yet, so no profile inline is shown there. response_add() below
    # immediately redirects the admin into the Change page right after
    # the User is created — and THAT page shows exactly the one inline
    # matching the role just chosen (Faculty or Student), ready to fill
    # in. No second manual lookup required.
    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.role == User.Role.FACULTY:
            return [FacultyInline]
        if obj.role == User.Role.STUDENT:
            return [StudentInline]
        return []

    def response_add(self, request, obj, post_url_continue=None):
        """
        After creating a new User, skip the changelist and go straight to
        the Change page for that user whenever a profile row (Faculty or
        Student) still needs to be filled in — so the admin lands right
        on the correct, decluttered form instead of hunting for the
        record again.

        "Save and add another" / "Save and continue editing" keep their
        normal Django behavior.
        """
        if "_addanother" not in request.POST and "_continue" not in request.POST:
            profile_required = obj.role in (User.Role.FACULTY, User.Role.STUDENT)
            profile_exists = (
                (obj.role == User.Role.FACULTY and Faculty.objects.filter(user=obj).exists())
                or (obj.role == User.Role.STUDENT and Student.objects.filter(user=obj).exists())
            )
            if profile_required and not profile_exists:
                self.message_user(
                    request,
                    f"User '{obj}' was created. Now complete the "
                    f"{obj.get_role_display()} profile below.",
                )
                opts = self.model._meta
                redirect_url = reverse(
                    f"admin:{opts.app_label}_{opts.model_name}_change",
                    args=(obj.pk,),
                    current_app=self.admin_site.name,
                )
                return HttpResponseRedirect(redirect_url)

        return super().response_add(request, obj, post_url_continue)


# ─────────────────────────────────────────────
#  2. FACULTY ADMIN
# ─────────────────────────────────────────────

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display  = ("last_name", "first_name", "department", "max_teaching_load", "user")
    list_filter   = ("department",)
    search_fields = ("last_name", "first_name", "department", "user__username")
    ordering      = ("last_name", "first_name")
    autocomplete_fields = ("user",)

    fieldsets = (
        ("Personal Information", {
            "fields": ("user", "first_name", "last_name", "department")
        }),
        ("Teaching Load", {
            "fields": ("max_teaching_load",)
        }),
    )


# ─────────────────────────────────────────────
#  3. STUDENT ADMIN
# ─────────────────────────────────────────────

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display     = ("student_number", "last_name", "first_name", "program", "user")
    list_filter      = ("program",)
    search_fields    = ("student_number", "last_name", "first_name", "user__username")
    ordering         = ("student_number",)
    autocomplete_fields = ("user",)
    inlines          = [EnrollmentInline]

    fieldsets = (
        ("Personal Information", {
            "fields": ("user", "student_number", "first_name", "last_name", "program")
        }),
    )


# ─────────────────────────────────────────────
#  4. SUBJECT ADMIN
# ─────────────────────────────────────────────

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display  = (
        "subject_code", "subject_title", "units",
        "term_number",
        "prerequisite_type", "prerequisite",
    )
    list_filter   = ("term_number", "units", "prerequisite_type")
    search_fields = ("subject_code", "subject_title")
    ordering      = ("term_number", "subject_code")
    autocomplete_fields = ("prerequisite",)

    fieldsets = (
        (None, {
            "fields": ("subject_code", "subject_title", "units")
        }),
        ("Curriculum Placement", {
            "fields": ("term_number",),
            "description": (
                "Determines when this subject is offered and which students can enlist in it. "
                "Only administrators may change this value."
            ),
        }),
        ("Prerequisites", {
            "fields": ("prerequisite_type", "prerequisite")
        }),
    )


# ─────────────────────────────────────────────
#  5. ROOM ADMIN
# ─────────────────────────────────────────────

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display  = ("room_name", "capacity")
    search_fields = ("room_name",)
    ordering      = ("room_name",)


# ─────────────────────────────────────────────
#  6. ACADEMIC TERM ADMIN
# ─────────────────────────────────────────────

@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display  = ("term_name", "term_number", "is_active_badge", "created_at")
    list_filter   = ("term_number", "is_active")
    search_fields = ("term_name",)
    ordering      = ("-created_at",)
    actions       = ["make_active"]

    fieldsets = (
        (None, {
            "fields": ("term_name", "term_number", "is_active"),
            "description": (
                "term_number determines which Subjects (by their own term_number) "
                "students will see and be able to enlist in on the Enlist Subjects page."
            ),
        }),
    )

    @admin.display(description="Active?", boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#16a34a;font-weight:bold;">✔ Active</span>')
        return format_html('<span style="color:#9ca3af;">Inactive</span>')

    @admin.action(description="Set selected term as the ACTIVE term (deactivates all others)")
    def make_active(self, request, queryset):
        # Only one active term at a time
        AcademicTerm.objects.all().update(is_active=False)
        count = queryset.update(is_active=True)
        if count > 1:
            # If multiple were selected, keep only the first alphabetically active
            first = queryset.order_by("term_name").first()
            queryset.exclude(pk=first.pk).update(is_active=False)
        self.message_user(request, "Active term updated successfully.")


# ─────────────────────────────────────────────
#  7. SCHEDULE ADMIN  (Subject Offering)
# ─────────────────────────────────────────────

class SlotUtilizationFilter(admin.SimpleListFilter):
    title        = "slot utilization"
    parameter_name = "slots"

    def lookups(self, request, model_admin):
        return [
            ("full",      "Full (0 slots)"),
            ("almost",    "Almost Full (≤5 slots)"),
            ("available", "Has Available Slots"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "full":
            return queryset.filter(available_slots=0)
        if self.value() == "almost":
            return queryset.filter(available_slots__lte=5)
        if self.value() == "available":
            return queryset.filter(available_slots__gt=0)
        return queryset


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display  = (
        "term", "subject", "faculty", "room",
        "day", "time_start", "time_end",
        "total_slots", "available_slots", "slot_bar",
    )
    list_filter   = ("term", "day", "faculty__department", SlotUtilizationFilter)
    search_fields = (
        "subject__subject_code", "subject__subject_title",
        "faculty__last_name", "room__room_name",
    )
    autocomplete_fields = ("term", "subject", "faculty", "room")
    ordering      = ("term", "day", "time_start")

    fieldsets = (
        ("Offering", {
            "fields": ("term", "subject", "faculty", "room")
        }),
        ("Time Slot", {
            "fields": ("day", "time_start", "time_end")
        }),
        ("Capacity", {
            "fields": ("total_slots", "available_slots")
        }),
    )

    @admin.display(description="Fill Rate")
    def slot_bar(self, obj):
        if obj.total_slots == 0:
            return "—"
        pct   = int((1 - obj.available_slots / obj.total_slots) * 100)
        color = "#16a34a" if pct < 75 else "#f59e0b" if pct < 95 else "#dc2626"
        return format_html(
            '<div style="background:#e5e7eb;border-radius:4px;width:90px;height:10px;">'
            '<div style="background:{};width:{}%;height:10px;border-radius:4px;"></div>'
            '</div><small style="color:{}">{} filled</small>',
            color, pct, color, f"{pct}%",
        )


# ─────────────────────────────────────────────
#  8. ENROLLMENT ADMIN
# ─────────────────────────────────────────────

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display  = (
        "student", "subject_code", "schedule_time",
        "status_badge", "enrolled_at",
    )
    list_filter   = ("status", "schedule__term", "schedule__subject__subject_code")
    search_fields = (
        "student__student_number",
        "student__last_name",
        "schedule__subject__subject_code",
        "schedule__subject__subject_title",
    )
    autocomplete_fields = ("student", "schedule")
    readonly_fields = ("enrolled_at",)
    ordering      = ("-enrolled_at",)

    fieldsets = (
        ("Enrollment Record", {
            "fields": ("student", "schedule", "status", "enrolled_at")
        }),
    )

    @admin.display(description="Subject", ordering="schedule__subject__subject_code")
    def subject_code(self, obj):
        return obj.schedule.subject.subject_code

    @admin.display(description="Schedule")
    def schedule_time(self, obj):
        s = obj.schedule
        return f"{s.get_day_display()} {s.time_start:%H:%M}–{s.time_end:%H:%M} @ {s.room.room_name}"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        if obj.status == Enrollment.Status.CONFIRMED:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;padding:2px 8px;'
                'border-radius:9999px;font-size:0.75rem;font-weight:600;">Confirmed</span>'
            )
        return format_html(
            '<span style="background:#fef9c3;color:#854d0e;padding:2px 8px;'
            'border-radius:9999px;font-size:0.75rem;font-weight:600;">In Cart</span>'
        )


# ─────────────────────────────────────────────
#  Admin site branding
# ─────────────────────────────────────────────

admin.site.site_header  = "LBYCPG3 Enlistment System"
admin.site.site_title   = "LBYCPG3 Admin"
admin.site.index_title  = "System Administration Panel"