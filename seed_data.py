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
# the trimestral enlistment restriction (1 = 1st term of the academic year,
# 2 = 2nd term, 3 = 3rd term). The full 12-term checklist maps onto this
# 3-term cycle as follows:
#   Checklist Term  1, 4, 7, 10  -> term_number 1
#   Checklist Term  2, 5, 8, 11  -> term_number 2
#   Checklist Term  3, 6, 9, 12  -> term_number 3
#
# NOTE ON PREREQUISITES: the Subject model only supports a single
# `prerequisite` FK + `prerequisite_type`. Several checklist courses list
# more than one prerequisite (e.g. one hard + one soft, or multiple hard
# prereqs). In those cases the single most binding prerequisite was kept
# and the rest are noted in a trailing comment — they are NOT enforced.
subjects_data = [
    # ── Checklist Term 1 -> term_number 1 ──────────────────────────────────
    ("NSTP101", "National Service Training Program – General Orientation", 0, None, "none", 1),
    ("FNDMATH", "Foundation in Math", 5, None, "none", 1),
    ("BASCHEM", "Basic Chemistry", 3, None, "none", 1),
    ("BASPHYS", "Basic Physics", 3, None, "none", 1),
    ("FNDSTAT", "Foundation in Statistics", 3, None, "none", 1),
    ("GEARTAP", "Art Appreciation", 3, None, "none", 1),

    # ── Checklist Term 2 -> term_number 2 ──────────────────────────────────
    ("NSTPCW1", "National Service Training Program 1", 3, None, "none", 2),
    ("GEMATMW", "Mathematics in the Modern World", 3, None, "none", 2),
    ("CALENG1", "Differential Calculus", 3, "FNDMATH", "hard", 2),
    ("COEDISC", "Computer Engineering as a Discipline", 1, None, "hard", 2),
    ("PROLOGI", "Programming Logic and Design Lecture", 2, None, "hard", 2),
    ("LBYCPA1", "Programming Logic and Design Laboratory", 2, "PROLOGI", "co_requisite", 2),
    ("LBYEC2A", "Computer Fundamentals and Programming 1", 1, None, "none", 2),
    ("GESTSOC", "Science, Technology, and Society", 3, None, "none", 2),
    ("GERIZAL", "Life and Works of Rizal", 3, None, "none", 2),

    # ── Checklist Term 3 -> term_number 3 ──────────────────────────────────
    ("NSTPCW2", "National Service Training Program 2", 3, "NSTPCW1", "hard", 3),
    ("ENGPHYS", "Physics for Engineers", 3, "BASPHYS", "hard", 3),  # also S: CALENG1 (omitted)
    ("LBYPH1A", "Physics for Engineers Laboratory", 1, "ENGPHYS", "co_requisite", 3),
    ("CALENG2", "Integral Calculus", 3, "CALENG1", "hard", 3),
    ("LBYEC2B", "Computer Fundamentals and Programming 2", 1, "LBYEC2A", "hard", 3),
    ("LBYCPEI", "Object-Oriented Programming Laboratory", 2, "PROLOGI", "hard", 3),
    ("GEPCOMM", "Purposive Communications", 3, None, "none", 3),
    ("LCFAITH", "Faith Worth Living", 3, None, "none", 3),
    ("GELECSP", "Social Science and Philosophy", 3, None, "none", 3),

    # ── Checklist Term 4 -> term_number 1 ──────────────────────────────────
    ("CALENG3", "Differential Equations", 3, "CALENG2", "hard", 1),
    ("DATSRAL", "Data Structures and Algorithms Lecture", 1, "LBYCPEI", "hard", 1),
    ("LBYCPA2", "Data Structures and Algorithms Laboratory", 2, "DATSRAL", "co_requisite", 1),
    ("DISCRMT", "Discrete Mathematics", 3, "CALENG1", "hard", 1),
    ("FUNDCKT", "Fundamentals of Electrical Circuits Lecture", 3, "ENGPHYS", "hard", 1),
    ("LBYEC2M", "Fundamentals of Electrical Circuits Laboratory", 1, "FUNDCKT", "co_requisite", 1),
    ("ENGCHEM", "Chemistry for Engineers", 3, "BASCHEM", "hard", 1),
    ("LBYCH1A", "Chemistry for Engineers Laboratory", 1, "ENGCHEM", "co_requisite", 1),
    ("GEFTWEL", "Physical Fitness and Wellness", 2, None, "none", 1),

    # ── Checklist Term 5 -> term_number 2 ──────────────────────────────────
    ("ENGDATA", "Engineering Data Analysis", 3, "FNDSTAT", "hard", 2),  # also S: CALENG2 (omitted)
    ("NUMMETS", "Numerical Methods", 3, "CALENG3", "hard", 2),
    ("FUNDLEC", "Fundamentals of Electronic Circuits Lecture", 3, "FUNDCKT", "hard", 2),
    ("LBYCPC2", "Fundamentals of Electronic Circuits Laboratory", 1, "FUNDLEC", "co_requisite", 2),
    ("SOFDESG", "Software Design Lecture", 3, "LBYCPA2", "hard", 2),
    ("LBYCPD2", "Software Design Laboratory", 1, "SOFDESG", "co_requisite", 2),
    ("ENGENVI", "Environmental Science and Engineering", 3, "ENGCHEM", "hard", 2),
    ("GEDANCE", "Physical Fitness and Wellness in Dance", 2, None, "none", 2),
    ("SAS2000", "Student Affairs Series 2", 0, None, "none", 2),

    # ── Checklist Term 6 -> term_number 3 ──────────────────────────────────
    ("LCLSTWO", "Lasallian Studies 2", 1, None, "none", 3),
    ("LASARE2", "Lasallian Recollection 2", 0, None, "none", 3),
    ("MXSIGFN", "Fundamentals of Mixed Signals and Sensors", 3, "FUNDLEC", "hard", 3),
    ("LOGDSGN", "Logic Circuits and Design Lecture", 3, "FUNDLEC", "hard", 3),
    ("LBYCPG4", "Logic Circuits and Design Laboratory", 1, "LOGDSGN", "co_requisite", 3),
    ("FDCNSYS", "Feedback and Control Systems", 3, "NUMMETS", "hard", 3),
    ("LBYCPC3", "Feedback and Control Systems Laboratory", 1, "FDCNSYS", "co_requisite", 3),
    ("LBYME1C", "Computer-Aided Drafting (CAD) for ECE and CpE", 1, None, "none", 3),
    ("GELECAH", "Arts and Humanities", 3, None, "none", 3),
    ("GESPORT", "Physical Fitness and Wellness in Individual Sports", 2, None, "none", 3),

    # ── Checklist Term 7 -> term_number 1 ──────────────────────────────────
    ("GEETHIC", "Ethics", 3, None, "none", 1),
    ("MICPROS", "Microprocessors Lecture", 3, "LOGDSGN", "hard", 1),
    ("LBYCPA3", "Microprocessors Laboratory", 1, "MICPROS", "co_requisite", 1),
    ("LBYCPB3", "Computer Engineering Drafting and Design Laboratory", 1, "LOGDSGN", "hard", 1),  # also H: FUNDLEC (omitted)
    ("LBYEC3B", "Intelligent Systems for Engineering", 1, "ENGDATA", "hard", 1),  # also H: LBYEC2A (omitted)
    ("LBYCPF2", "Introduction to HDL Laboratory", 1, "FUNDLEC", "hard", 1),
    ("DIGDACM", "Data and Digital Communications", 3, "FUNDLEC", "hard", 1),
    ("GETEAMS", "Physical Fitness and Wellness in Team Sports", 2, None, "none", 1),
    ("LBYCPG2", "Basic Computer Systems Administration", 1, None, "none", 1),

    # ── Checklist Term 8 -> term_number 2 ──────────────────────────────────
    ("CSYSARC", "Computer Architecture and Organization Lecture", 3, "MICPROS", "hard", 2),
    ("LBYCPD3", "Computer Architecture and Organization Laboratory", 1, "CSYSARC", "co_requisite", 2),
    ("EMBDSYS", "Embedded Systems Lecture", 3, "MICPROS", "hard", 2),
    ("LBYCPM3", "Embedded Systems Laboratory", 1, "EMBDSYS", "co_requisite", 2),
    ("LBYCPG3", "Online Technologies Laboratory", 1, None, "none", 2),
    ("GELECST", "Science and Technology", 3, None, "none", 2),
    ("REMETHS", "Methods of Research for CpE", 3, "ENGDATA", "hard", 2),  # also H: GEPCOMM, H: LOGDSGN (omitted)
    ("OPESSYS", "Operating Systems", 3, "LBYCPA2", "hard", 2),
    ("LBYCPO1", "Operating Systems Laboratory", 1, "OPESSYS", "co_requisite", 2),

    # ── Checklist Term 9 -> term_number 3 ──────────────────────────────────
    ("LCLSTRI", "Lasallian Studies 3", 1, None, "none", 3),
    ("LCASEAN", "The Filipino and ASEAN", 3, None, "none", 3),
    ("LASARE3", "Lasallian Recollection 3", 0, None, "none", 3),
    ("DSIGPRO", "Digital Signal Processing Lecture", 3, "FDCNSYS", "hard", 3),  # also S: EMBDSYS (omitted)
    ("LBYCPA4", "Digital Signal Processing Laboratory", 1, "DSIGPRO", "co_requisite", 3),
    ("OCHESAF", "Basic Occupational Health and Safety", 3, "EMBDSYS", "hard", 3),
    ("THSCP4A", "CpE Practice and Design 1", 1, "REMETHS", "hard", 3),  # also H: EMBDSYS (omitted)
    ("CPEPRAC", "CpE Laws and Professional Practice", 2, "EMBDSYS", "hard", 3),
    ("CPECOG1", "CpE Elective 1 Lecture", 2, "EMBDSYS", "hard", 3),  # also C: THSCP4A (omitted)
    ("LBYCPF3", "CpE Elective 1 Laboratory", 1, "CPECOG1", "co_requisite", 3),

    # ── Checklist Term 10 -> term_number 1 ─────────────────────────────────
    ("LCENWRD", "Encountering the Word in the World", 3, None, "none", 1),
    ("EMERTEC", "Emerging Technologies in CpE", 3, "EMBDSYS", "hard", 1),
    ("THSCP4B", "CpE Practice and Design 2", 1, "THSCP4A", "hard", 1),
    ("ENGTREP", "Technopreneurship 101", 3, "EMBDSYS", "hard", 1),
    ("CONETSC", "Computer Networks and Security Lecture", 3, "DIGDACM", "hard", 1),
    ("LBYCPB4", "Computer Networks and Security Laboratory", 1, "CONETSC", "co_requisite", 1),
    ("CPECAPS", "Operational Technologies", 1, "LBYCPB4", "co_requisite", 1),  # also C: LBYCPH3 (omitted)
    ("CPECOG2", "CpE Elective 2 Lecture", 2, "THSCP4A", "soft", 1),
    ("LBYCPH3", "CpE Elective 2 Laboratory", 1, "CPECOG2", "co_requisite", 1),
    ("SAS3000", "Student Affairs Series 3", 0, "SAS2000", "hard", 1),

    # ── Checklist Term 11 -> term_number 2 ─────────────────────────────────
    ("PRCGECP", "Practicum for CpE", 3, "REMETHS", "hard", 2),

    # ── Checklist Term 12 -> term_number 3 ─────────────────────────────────
    ("GERPHIS", "Readings in Philippine History", 3, None, "none", 3),
    ("GEWORLD", "The Contemporary World", 3, None, "none", 3),
    ("THSCP4C", "CpE Practice and Design 3", 1, "THSCP4B", "hard", 3),
    ("CPECOG3", "CpE Elective 3 Lecture", 2, "THSCP4A", "soft", 3),
    ("LBYCPC4", "CpE Elective 3 Laboratory", 1, "CPECOG3", "co_requisite", 3),
    ("CPETRIP", "Seminars and Field Trips for CpE", 1, "CPECAPS", "hard", 3),  # also H: EMBDSYS (omitted)
    ("ECNOMIC", "Engineering Economics for CpE", 3, "CALENG1", "soft", 3),
    ("ENGMANA", "Engineering Management", 2, "CALENG1", "soft", 3),
    ("GEUSELF", "Understanding the Self", 3, None, "none", 3),
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

# NOTE: subject codes below were updated to match the real curriculum codes
# now used in subjects_data (the previous placeholder codes like CMPDESN,
# CMPE30A/B, ENGMATH1/2, DATASRUC, CMPE30AL no longer exist). LBYCPG3 and
# ENGTREP kept their codes since those also exist in the real checklist.
schedule_defs = [
    # (subject_code, faculty_idx, room_idx, day,   time_start,   time_end,    slots)
    ("LBYCPB3",  0, 0, "MON", time(7, 30),  time(9,  0),  35),
    ("MICPROS",  0, 1, "TUE", time(9, 0),   time(10, 30), 40),
    ("EMBDSYS",  1, 2, "WED", time(10, 30), time(12, 0),  40),
    ("LBYCPM3",  0, 0, "WED", time(12, 0),  time(13, 30), 40),
    ("LBYCPG3",  1, 3, "THU", time(13, 0),  time(15, 0),  30),
    ("CALENG1",  2, 4, "FRI", time(7, 30),  time(9,  0),  40),
    ("CALENG2",  2, 5, "SAT", time(9, 0),   time(10, 30), 35),
    ("DATSRAL",  0, 0, "WED", time(7, 30),  time(9,  0),  35),
    ("ENGTREP",  3, 5, "FRI", time(7, 30),  time(9,  0),  40),
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