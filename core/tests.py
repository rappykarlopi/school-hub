import json
from datetime import time

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import AcademicTerm, Faculty, Room, Schedule, Subject, User


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
