"""
seed_data.py
Run once to populate the database with demo data for LBYCPG3.

Usage (from project root):
    python manage.py shell < seed_data.py
  OR
    python manage.py runscript seed_data   (if django-extensions installed)
"""

import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "enlistment.settings")
django.setup()

from django.contrib.auth import get_user_model
from core.models import Faculty, Student, Subject, Room, AcademicTerm, Schedule, Enrollment
from datetime import time

User = get_user_model()

print("⚡ Seeding LBYCPG3 demo data...")

# ── 1. Admin User ─────────────────────────────────────────────────────────────
admin, _ = User.objects.get_or_create(username="admin", defaults={
    "role": User.Role.ADMIN,
    "is_staff": True,
    "is_superuser": True,
    "email": "admin@dlsu.edu.ph",
    "first_name": "System",
    "last_name": "Administrator",
})
admin.set_password("admin1234")
admin.save()
print(f"  ✓ Admin user: admin / admin1234")

# ── 2. Faculty Users ───────────────────────────────────────────────────────────
faculty_data = [
    ("faculty1", "Maria",   "Santos",   "Computer Engineering"),
    ("faculty2", "Jose",    "Reyes",    "Computer Engineering"),
    ("faculty3", "Ricardo", "Cruz",     "Mathematics"),
    ("faculty4", "Raphael", "Santiago", "Mathematics"),
]
created_faculty = []
for username, fname, lname, dept in faculty_data:
    u, _ = User.objects.get_or_create(username=username, defaults={
        "role":  User.Role.FACULTY,
        "email": f"{username}@dlsu.edu.ph",
        "first_name": fname,
        "last_name":  lname,
    })
    u.set_password("faculty1234")
    u.save()

    f, _ = Faculty.objects.get_or_create(user=u, defaults={
        "first_name": fname,
        "last_name":  lname,
        "department": dept,
        "max_teaching_load": 21,
    })
    created_faculty.append(f)
    print(f"  ✓ Faculty: {username} / faculty1234  ({fname} {lname})")

# ── 3. Student Users ───────────────────────────────────────────────────────────
student_data = [
    ("student1", "122001001", "Ana",   "Dela Cruz"),
    ("student2", "122001002", "Marco", "Bautista"),
    ("student3", "122001003", "Lena",  "Garcia"),
]
created_students = []
for username, snum, fname, lname in student_data:
    u, _ = User.objects.get_or_create(username=username, defaults={
        "role":  User.Role.STUDENT,
        "email": f"{username}@dlsu.edu.ph",
        "first_name": fname,
        "last_name":  lname,
    })
    u.set_password("student1234")
    u.save()

    s, _ = Student.objects.get_or_create(user=u, defaults={
        "student_number": snum,
        "first_name": fname,
        "last_name":  lname,
        "program": "BS Computer Engineering",
    })
    created_students.append(s)
    print(f"  ✓ Student: {username} / student1234  ({fname} {lname}, {snum})")

# (code, title, units, prereq_code, prereq_type, term_number)
# term_number is the curriculum placement set by the admin and implements
# the trimestral enlistment restriction.
subjects_data = [
    ("CMPDESN", "Computer Design",              3, None,       "hard",         3),
    ("CMPE30A", "Computer Engineering I",       3, None,       "hard",         1),
    ("CMPE30B", "Computer Engineering II",      3, "CMPE30A",  "hard",         2),
    ("LBYCPG3", "CPE Integrative Project III",  2, "CMPE30B",  "hard",         3),
    ("ENGMATH1","Engineering Mathematics I",     3, None,       "hard",        1),
    ("ENGMATH2","Engineering Mathematics II",    3, "ENGMATH1", "hard",        2),
    ("DATASRUC", "Data Structures",             3, "CMPE30A",  "soft",         1),
    ("ENGTREP", "Engineering Entrepreneurship", 3, None,       "hard",         1),
    ("CMPE30AL", "Computer Engineering I Lab",  1, "CMPE30A",  "co_requisite", 1),
]
subj_map = {}
for code, title, units, prereq_code, prereq_type, term_number in subjects_data:
    subj, _ = Subject.objects.get_or_create(subject_code=code, defaults={
        "subject_title": title,
        "units": units,
        "prerequisite_type": prereq_type,
        "term_number": term_number,
    })
    subj_map[code] = subj

# Assign prerequisites in a second pass (after all subjects exist)
for code, title, units, prereq_code, prereq_type, term_number in subjects_data:
    if prereq_code:
        subj = subj_map[code]
        subj.prerequisite = subj_map[prereq_code]
        subj.prerequisite_type = prereq_type
        subj.save(update_fields=["prerequisite", "prerequisite_type"])

print(f"  ✓ {len(subjects_data)} subjects created/verified")

rooms_data = [
    ("GK101", 40), ("GK102", 40), ("GK103", 40),
    ("LS202", 35), ("LS203", 35),
    ("AG1901", 50),
]
created_rooms = []
for name, cap in rooms_data:
    r, _ = Room.objects.get_or_create(room_name=name, defaults={"capacity": cap})
    created_rooms.append(r)
print(f"  ✓ {len(rooms_data)} rooms created/verified")

AcademicTerm.objects.all().update(is_active=False)
term, _ = AcademicTerm.objects.get_or_create(
    term_name="AY 2025-2026 Term 3",
    defaults={"is_active": True, "term_number": 3}
)
term.is_active = True
term.term_number = 3
term.save()
print(f"  ✓ Active term: {term.term_name} (Term {term.term_number})")

schedule_defs = [
    # (subject_code, faculty_idx, room_idx, day,   time_start,   time_end,    slots)
    ("CMPDESN",  0, 0, "MON", time(7, 30),  time(9,  0),  35),
    ("CMPE30A",  0, 1, "TUE", time(9, 0),   time(10, 30), 40),
    ("CMPE30B",  1, 2, "WED", time(10, 30), time(12, 0),  40),
    ("CMPE30AL", 0, 0, "WED", time(12, 0),  time(13, 30), 40),
    ("LBYCPG3",  1, 3, "THU", time(13, 0),  time(15, 0),  30),
    ("ENGMATH1", 2, 4, "FRI", time(7, 30),  time(9,  0),  40),
    ("ENGMATH2", 2, 5, "SAT", time(9, 0),   time(10, 30), 35),
    ("DATASRUC", 0, 0, "WED", time(7, 30),  time(9,  0),  35),
    ("ENGTREP", 3, 5, "FRI", time(7, 30),  time(9,  0),  40),
]
created_schedules = []
for subj_code, fac_idx, room_idx, day, tstart, tend, slots in schedule_defs:
    sched, created = Schedule.objects.get_or_create(
        term=term,
        subject=subj_map[subj_code],
        faculty=created_faculty[fac_idx],
        room=created_rooms[room_idx],
        day=day,
        time_start=tstart,
        time_end=tend,
        defaults={"total_slots": slots, "available_slots": slots}
    )
    created_schedules.append(sched)

print(f"  ✓ {len(schedule_defs)} schedules created/verified")

print("\n✅ Seed complete! Login credentials:")
print("   Admin:    admin   / admin1234   → /admin/")
print("   Faculty:  faculty1 / faculty1234  → /faculty/dashboard/")
print("   Student:  student1 / student1234  → /student/dashboard/")
print("\nStart the server:  python manage.py runserver")
