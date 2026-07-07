"""
LBYCPG3 – Computer Engineering Enlistment and Scheduler System
models.py  |  Phase 1: Database Architecture
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


# ─────────────────────────────────────────────
#  1. CUSTOM USER  (Role-Based)
# ─────────────────────────────────────────────

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN   = "admin",   "Admin"
        FACULTY = "faculty", "Faculty"
        STUDENT = "student", "Student"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # ── helpers ──────────────────────────────
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_faculty(self):
        return self.role == self.Role.FACULTY

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT


# ─────────────────────────────────────────────
#  2. FACULTY PROFILE
# ─────────────────────────────────────────────

class Faculty(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name="faculty_profile")
    first_name       = models.CharField(max_length=80)
    last_name        = models.CharField(max_length=80)
    department       = models.CharField(max_length=120)
    max_teaching_load = models.PositiveSmallIntegerField(
        default=21,
        help_text="Maximum units this faculty member may teach per term.",
    )

    class Meta:
        verbose_name = "Faculty"
        verbose_name_plural = "Faculty Members"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def current_load(self, term):
        """Sum of units for confirmed + cart schedules in the given term."""
        return (
            Schedule.objects.filter(faculty=self, term=term)
            .aggregate(total=models.Sum("subject__units"))["total"] or 0
        )


# ─────────────────────────────────────────────
#  3. STUDENT PROFILE
# ─────────────────────────────────────────────

class Student(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    student_number = models.CharField(max_length=20, unique=True)
    first_name     = models.CharField(max_length=80)
    last_name      = models.CharField(max_length=80)
    program        = models.CharField(max_length=120, default="BS Computer Engineering")

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.student_number} – {self.last_name}, {self.first_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def confirmed_subjects(self, term):
        """Returns subjects the student has *confirmed* enrollments in for a term."""
        return Subject.objects.filter(
            schedule__enrollment__student=self,
            schedule__term=term,
            schedule__enrollment__status=Enrollment.Status.CONFIRMED,
        )


# ─────────────────────────────────────────────
#  4. SUBJECT
# ─────────────────────────────────────────────

class Subject(models.Model):
    class PrerequisiteType(models.TextChoices):
        HARD = "hard", "Hard prerequisite"
        SOFT = "soft", "Soft prerequisite"
        CO_REQUISITE = "co_requisite", "Co-requisite"

    subject_code  = models.CharField(max_length=20, unique=True)
    subject_title = models.CharField(max_length=200)
    units         = models.PositiveSmallIntegerField(default=3)
    prerequisite_type = models.CharField(
        max_length=20,
        choices=PrerequisiteType.choices,
        default=PrerequisiteType.HARD,
        help_text="How this prerequisite rule should be enforced.",
    )
    prerequisite  = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="unlocks",
        help_text="Related subject used for prerequisite or co-requisite rules.",
    )

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ["subject_code"]

    def __str__(self):
        return f"{self.subject_code} – {self.subject_title}"


# ─────────────────────────────────────────────
#  5. ROOM
# ─────────────────────────────────────────────

class Room(models.Model):
    room_name = models.CharField(max_length=60, unique=True)
    capacity  = models.PositiveSmallIntegerField(default=40)

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"
        ordering = ["room_name"]

    def __str__(self):
        return f"{self.room_name} (cap: {self.capacity})"


# ─────────────────────────────────────────────
#  6. ACADEMIC TERM
# ─────────────────────────────────────────────

class AcademicTerm(models.Model):
    term_name    = models.CharField(max_length=60, unique=True)
    is_active    = models.BooleanField(
        default=False,
        help_text="Only one term should be active at a time. "
                  "Setting this True does NOT auto-deactivate others – manage via admin.",
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Academic Term"
        verbose_name_plural = "Academic Terms"
        ordering = ["-created_at"]

    def __str__(self):
        status = " ✓ ACTIVE" if self.is_active else ""
        return f"{self.term_name}{status}"


# ─────────────────────────────────────────────
#  7. SCHEDULE  (Subject Offering)
# ─────────────────────────────────────────────

class Schedule(models.Model):
    class Day(models.TextChoices):
        MONDAY    = "MON", "Monday"
        TUESDAY   = "TUE", "Tuesday"
        WEDNESDAY = "WED", "Wednesday"
        THURSDAY  = "THU", "Thursday"
        FRIDAY    = "FRI", "Friday"
        SATURDAY  = "SAT", "Saturday"

    term            = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE, related_name="schedules")
    subject         = models.ForeignKey(Subject,      on_delete=models.CASCADE, related_name="schedules")
    faculty         = models.ForeignKey(Faculty,      on_delete=models.CASCADE, related_name="schedules")
    room            = models.ForeignKey(Room,         on_delete=models.CASCADE, related_name="schedules")
    day             = models.CharField(max_length=3, choices=Day.choices)
    time_start      = models.TimeField()
    time_end        = models.TimeField()
    total_slots     = models.PositiveSmallIntegerField(default=40)
    available_slots = models.PositiveSmallIntegerField(default=40)

    class Meta:
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"
        ordering = ["term", "day", "time_start"]
        # ── DB-level double-booking guards ───────────────────
        constraints = [
            # A room cannot host two classes at the same time on the same day in the same term
            models.UniqueConstraint(
                fields=["term", "room", "day", "time_start", "time_end"],
                name="unique_room_slot",
            ),
            # A faculty member cannot teach two classes at the same time
            models.UniqueConstraint(
                fields=["term", "faculty", "day", "time_start", "time_end"],
                name="unique_faculty_slot",
            ),
        ]

    def __str__(self):
        return (
            f"{self.subject.subject_code} | {self.get_day_display()} "
            f"{self.time_start:%H:%M}–{self.time_end:%H:%M} | "
            f"{self.room.room_name}"
        )

    def clean(self):
        """
        Overlap check for room and faculty at the model level.
        Catches cases that slip past the unique_together (e.g., partially overlapping times).
        Overlap condition:  start_A < end_B  AND  end_A > start_B
        """
        if not (self.time_start and self.time_end):
            return
        if self.time_start >= self.time_end:
            raise ValidationError("time_start must be before time_end.")

        base_qs = Schedule.objects.filter(
            term=self.term,
            day=self.day,
            time_start__lt=self.time_end,
            time_end__gt=self.time_start,
        )
        if self.pk:
            base_qs = base_qs.exclude(pk=self.pk)

        if base_qs.filter(room=self.room).exists():
            raise ValidationError(
                f"Room '{self.room}' already has a class during this time slot on {self.get_day_display()}."
            )
        if base_qs.filter(faculty=self.faculty).exists():
            raise ValidationError(
                f"Faculty '{self.faculty}' already has a class during this time slot on {self.get_day_display()}."
            )

    @property
    def time_range(self):
        return f"{self.time_start:%I:%M %p} – {self.time_end:%I:%M %p}"

    @property
    def is_full(self):
        return self.available_slots <= 0


# ─────────────────────────────────────────────
#  8. ENROLLMENT
# ─────────────────────────────────────────────

class Enrollment(models.Model):
    class Status(models.TextChoices):
        CART      = "Cart",      "In Cart"
        CONFIRMED = "Confirmed", "Confirmed"

    student     = models.ForeignKey(Student,  on_delete=models.CASCADE, related_name="enrollments")
    schedule    = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="enrollments")
    status      = models.CharField(max_length=12, choices=Status.choices, default=Status.CART)
    enrolled_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        # A student cannot enroll in the exact same schedule offering twice
        unique_together = [("student", "schedule")]
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student} → {self.schedule} [{self.status}]"

    # ── Comprehensive Validation Engine ──────────────────────────────────────

    def _has_subject_history(self, subject, *, term=None, passed_only=False):
        qs = Enrollment.objects.filter(student=self.student, schedule__subject=subject)
        if term is not None:
            qs = qs.filter(schedule__term=term)
        if passed_only:
            qs = qs.filter(status=self.Status.CONFIRMED)
        else:
            qs = qs.filter(status__in=[self.Status.CONFIRMED, self.Status.CART])
        return qs.exists()

    @classmethod
    def validate_cart(cls, student, term, cart_items):
        """Validate a set of cart enrollments before confirmation."""
        errors = []

        confirmed_enrollments = list(
            cls.objects.filter(student=student, schedule__term=term, status=cls.Status.CONFIRMED)
            .select_related("schedule__subject")
        )
        confirmed_subject_ids = {item.schedule.subject_id for item in confirmed_enrollments}
        planned_subject_ids = {item.schedule.subject_id for item in cart_items}

        def overlaps(first, second):
            return (
                first.schedule.day == second.schedule.day
                and first.schedule.time_start < second.schedule.time_end
                and first.schedule.time_end > second.schedule.time_start
            )

        for item in cart_items:
            subject = item.schedule.subject

            if subject.id in confirmed_subject_ids:
                errors.append(
                    f"You already have '{subject.subject_code}' confirmed for this term."
                )

            if item.schedule.available_slots <= 0:
                errors.append(
                    f"No available slots remaining for '{subject.subject_code}'."
                )

            prereq = subject.prerequisite
            if prereq is not None:
                if subject.prerequisite_type == Subject.PrerequisiteType.HARD:
                    if prereq.id not in confirmed_subject_ids and prereq.id not in planned_subject_ids:
                        errors.append(
                            f"Hard prerequisite not met: You must have completed '{prereq}' "
                            f"before enrolling in '{subject}'."
                        )
                elif subject.prerequisite_type == Subject.PrerequisiteType.SOFT:
                    if prereq.id not in confirmed_subject_ids and prereq.id not in planned_subject_ids:
                        errors.append(
                            f"Soft prerequisite not met: You must have taken '{prereq}' "
                            f"before enrolling in '{subject}'."
                        )
                elif subject.prerequisite_type == Subject.PrerequisiteType.CO_REQUISITE:
                    if prereq.id not in confirmed_subject_ids and prereq.id not in planned_subject_ids:
                        errors.append(
                            f"Co-requisite not met: You must enroll in '{prereq}' "
                            f"alongside '{subject}' in the same term."
                        )

            for other_item in cart_items:
                if other_item.pk == item.pk:
                    continue
                if other_item.schedule.subject_id == subject.id:
                    errors.append(
                        f"You already have '{subject.subject_code}' in your current selection."
                    )
                    break
                if overlaps(item, other_item):
                    errors.append(
                        f"Schedule conflict on {item.schedule.get_day_display()}: "
                        f"'{other_item.schedule.subject.subject_code}' overlaps with '{subject.subject_code}'."
                    )
                    break

            for confirmed_item in confirmed_enrollments:
                if overlaps(item, confirmed_item):
                    errors.append(
                        f"Schedule conflict on {item.schedule.get_day_display()}: "
                        f"'{confirmed_item.schedule.subject.subject_code}' overlaps with '{subject.subject_code}'."
                    )
                    break

        return errors

    def clean(self):
        errors = {}

        # Guard: schedule must exist before we can validate
        if not hasattr(self, "schedule") or self.schedule_id is None:
            return
        if not hasattr(self, "student") or self.student_id is None:
            return

        # ── 1. Prerequisite / Co-requisite check ─────────────────────────
        subject = self.schedule.subject
        prereq  = subject.prerequisite

        if prereq is not None:
            if subject.prerequisite_type == Subject.PrerequisiteType.HARD:
                if not self._has_subject_history(prereq, passed_only=True):
                    errors["schedule"] = (
                        f"Hard prerequisite not met: You must have completed '{prereq}' "
                        f"before enrolling in '{subject}'."
                    )
            elif subject.prerequisite_type == Subject.PrerequisiteType.SOFT:
                if not self._has_subject_history(prereq):
                    errors["schedule"] = (
                        f"Soft prerequisite not met: You must have taken '{prereq}' "
                        f"before enrolling in '{subject}'."
                    )

        # ── 2. Duplicate subject check ────────────────────────────────────
        # Prevent adding the same subject twice in the same term (different section)
        same_subject_qs = Enrollment.objects.filter(
            student=self.student,
            schedule__term=self.schedule.term,
            schedule__subject=subject,
        )
        if self.pk:
            same_subject_qs = same_subject_qs.exclude(pk=self.pk)

        if same_subject_qs.exists():
            errors.setdefault("schedule", (
                f"You already have '{subject.subject_code}' in your cart or schedule for this term."
            ))

        # ── 3. Slot availability (only when confirming) ───────────────────
        if self.status == self.Status.CONFIRMED and self.schedule.available_slots <= 0:
            errors["status"] = (
                f"No available slots remaining for '{subject.subject_code}' – "
                f"this section is full."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Always run full validation before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
