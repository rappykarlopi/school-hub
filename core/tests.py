import json
from datetime import time

from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import AcademicTerm, Enrollment, Faculty, Room, Schedule, Student, Subject, User


class DuplicateClassCreationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            password="admin1234",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        faculty_user = User.objects.create_user(
            username="faculty1",
            password="faculty1234",
            role=User.Role.FACULTY,
        )
        other_faculty_user = User.objects.create_user(
            username="faculty2",
            password="faculty1234",
            role=User.Role.FACULTY,
        )
        self.faculty = Faculty.objects.create(
            user=faculty_user,
            first_name="Maria",
            last_name="Santos",
            department="Computer Engineering",
        )
        self.other_faculty = Faculty.objects.create(
            user=other_faculty_user,
            first_name="Jose",
            last_name="Reyes",
            department="Computer Engineering",
        )
        self.room = Room.objects.create(room_name="GK101", capacity=40)
        self.other_room = Room.objects.create(room_name="GK102", capacity=40)
        self.term = AcademicTerm.objects.create(
            term_name="AY 2025-2026 Term 3",
            term_number=3,
            is_active=True,
        )
        self.subject = Subject.objects.create(
            subject_code="LBYCPG3",
            subject_title="CPE Integrative Project III",
            units=2,
            term_number=3,
        )

    def _create_schedule(self):
        return Schedule.objects.create(
            term=self.term,
            subject=self.subject,
            faculty=self.faculty,
            room=self.room,
            day=Schedule.Day.MONDAY,
            time_start=time(7, 30),
            time_end=time(9, 0),
            total_slots=40,
            available_slots=40,
        )

    def test_schedule_full_clean_rejects_duplicate_subject_offering(self):
        self._create_schedule()
        duplicate = Schedule(
            term=self.term,
            subject=self.subject,
            faculty=self.other_faculty,
            room=self.other_room,
            day=Schedule.Day.MONDAY,
            time_start=time(7, 30),
            time_end=time(9, 0),
            total_slots=40,
            available_slots=40,
        )

        with self.assertRaisesMessage(ValidationError, Schedule.DUPLICATE_CLASS_MESSAGE):
            duplicate.full_clean()

    def test_database_constraint_rejects_racing_duplicate_subject_offering(self):
        self._create_schedule()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Schedule.objects.create(
                    term=self.term,
                    subject=self.subject,
                    faculty=self.other_faculty,
                    room=self.other_room,
                    day=Schedule.Day.MONDAY,
                    time_start=time(7, 30),
                    time_end=time(9, 0),
                    total_slots=40,
                    available_slots=40,
                )

    def test_create_class_api_returns_conflict_for_duplicate(self):
        self._create_schedule()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("create_class"),
            data=json.dumps({
                "term_id": self.term.pk,
                "subject_id": self.subject.pk,
                "faculty_id": self.other_faculty.pk,
                "room_id": self.other_room.pk,
                "day": Schedule.Day.MONDAY,
                "time_start": "07:30",
                "time_end": "09:00",
                "total_slots": 40,
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {"success": False, "message": Schedule.DUPLICATE_CLASS_MESSAGE},
        )


class UnitLimitTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username="student1",
            password="student1234",
            role=User.Role.STUDENT,
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_number="20240001",
            first_name="Juan",
            last_name="Dela Cruz",
        )
        self.term = AcademicTerm.objects.create(
            term_name="AY 2025-2026 Term 3",
            term_number=3,
            is_active=True,
        )
        self.faculty = Faculty.objects.create(
            user=User.objects.create_user(
                username="faculty3",
                password="faculty1234",
                role=User.Role.FACULTY,
            ),
            first_name="Ana",
            last_name="Lopez",
            department="Computer Engineering",
        )
        self.room = Room.objects.create(room_name="GK201", capacity=40)

        self.confirmed_subject = Subject.objects.create(
            subject_code="LBYCONF",
            subject_title="Confirmed Subject",
            units=20,
            term_number=3,
        )
        self.cart_subject = Subject.objects.create(
            subject_code="LBYCART",
            subject_title="Cart Subject",
            units=3,
            term_number=3,
        )
        self.new_subject = Subject.objects.create(
            subject_code="LBYNEW",
            subject_title="New Subject",
            units=2,
            term_number=3,
        )

        self.confirmed_schedule = Schedule.objects.create(
            term=self.term,
            subject=self.confirmed_subject,
            faculty=self.faculty,
            room=self.room,
            day=Schedule.Day.MONDAY,
            time_start=time(7, 0),
            time_end=time(8, 30),
            total_slots=40,
            available_slots=40,
        )
        self.cart_schedule = Schedule.objects.create(
            term=self.term,
            subject=self.cart_subject,
            faculty=self.faculty,
            room=self.room,
            day=Schedule.Day.TUESDAY,
            time_start=time(9, 0),
            time_end=time(10, 30),
            total_slots=40,
            available_slots=40,
        )
        self.new_schedule = Schedule.objects.create(
            term=self.term,
            subject=self.new_subject,
            faculty=self.faculty,
            room=self.room,
            day=Schedule.Day.WEDNESDAY,
            time_start=time(11, 0),
            time_end=time(12, 30),
            total_slots=40,
            available_slots=40,
        )

        Enrollment.objects.create(
            student=self.student,
            schedule=self.confirmed_schedule,
            term=self.term,
            subject=self.confirmed_subject,
            status=Enrollment.Status.CONFIRMED,
        )
        Enrollment.objects.create(
            student=self.student,
            schedule=self.cart_schedule,
            term=self.term,
            subject=self.cart_subject,
            status=Enrollment.Status.CART,
        )

    def test_add_to_cart_rejects_when_confirmed_and_cart_units_exceed_max(self):
        self.client.force_login(self.student_user)

        response = self.client.post(reverse("add_to_cart", args=[self.new_schedule.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Enrollment.objects.filter(
                student=self.student,
                schedule=self.new_schedule,
                status=Enrollment.Status.CART,
            ).exists()
        )

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Exceeded Maximum Unit" in str(message) for message in messages_list))

    def test_confirm_enlistment_rejects_when_confirmed_and_cart_units_exceed_max(self):
        self.client.force_login(self.student_user)

        response = self.client.post(reverse("confirm_enlistment"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Enrollment.objects.filter(
                student=self.student,
                schedule=self.cart_schedule,
                status=Enrollment.Status.CART,
            ).count(),
            1,
        )

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Cannot confirm enlistment" in str(message) for message in messages_list))
