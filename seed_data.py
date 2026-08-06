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

import itertools
import random
from django.contrib.auth import get_user_model
from core.models import AcademicTerm, Enrollment, Faculty, Room, Schedule, Student, Subject
from datetime import time

User = get_user_model()

print("⚡ Seeding LBYCPG3 demo data...")

# Reset prior demo data so re-running the script produces a clean, consistent dataset.
Schedule.objects.all().delete()
Enrollment.objects.all().delete()
AcademicTerm.objects.all().delete()
Subject.objects.all().delete()
Room.objects.all().delete()
Faculty.objects.all().delete()
Student.objects.all().delete()
User.objects.exclude(username="admin").delete()

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
    ("faculty1", "Maria",     "Santos",     "Computer Engineering"),
    ("faculty2", "Jose",      "Reyes",      "Computer Engineering"),
    ("faculty3", "Ricardo",   "Cruz",       "Mathematics"),
    ("faculty4", "Raphael",   "Santiago",   "Mathematics"),
    ("faculty5", "Andrea",    "Villanueva", "Computer Engineering"),
    ("faculty6", "Michael",   "Torres",     "Computer Engineering"),
    ("faculty7", "Grace",     "Fernandez",  "Natural Sciences"),
    ("faculty8", "Patricia",  "Lim",        "General Education"),
    ("faculty9", "Elena",     "Ramos",      "Computer Engineering"),
    ("faculty10", "Chris",    "Dizon",      "Computer Engineering"),
    ("faculty11", "Nina",     "Castillo",   "Mathematics"),
    ("faculty12", "Bryan",    "Pascual",    "Computer Engineering"),
    ("faculty13", "Liza",     "Mendoza",    "Natural Sciences"),
    ("faculty14", "Kevin",    "Tan",        "General Education"),
    ("faculty15", "Sofia",    "David",      "Computer Engineering"),
    ("faculty16", "Renz",     "Bautista",   "Computer Engineering"),
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
        "max_teaching_load": 16,
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

# ── 4. Subjects ────────────────────────────────────────────────────────────────
subjects_data = [
    # (code, title, units, prereq_code, prereq_type, term_number)
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
    ("ENGPHYS", "Physics for Engineers", 3, "BASPHYS", "hard", 3),
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
    ("ENGDATA", "Engineering Data Analysis", 3, "FNDSTAT", "hard", 2),
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
    ("LBYCPB3", "Computer Engineering Drafting and Design Laboratory", 1, "LOGDSGN", "hard", 1),
    ("LBYEC3B", "Intelligent Systems for Engineering", 1, "ENGDATA", "hard", 1),
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
    ("REMETHS", "Methods of Research for CpE", 3, "ENGDATA", "hard", 2),
    ("OPESSYS", "Operating Systems", 3, "LBYCPA2", "hard", 2),
    ("LBYCPO1", "Operating Systems Laboratory", 1, "OPESSYS", "co_requisite", 2),
    # ── Checklist Term 9 -> term_number 3 ──────────────────────────────────
    ("LCLSTRI", "Lasallian Studies 3", 1, None, "none", 3),
    ("LCASEAN", "The Filipino and ASEAN", 3, None, "none", 3),
    ("LASARE3", "Lasallian Recollection 3", 0, None, "none", 3),
    ("DSIGPRO", "Digital Signal Processing Lecture", 3, "FDCNSYS", "hard", 3),
    ("LBYCPA4", "Digital Signal Processing Laboratory", 1, "DSIGPRO", "co_requisite", 3),
    ("OCHESAF", "Basic Occupational Health and Safety", 3, "EMBDSYS", "hard", 3),
    ("THSCP4A", "CpE Practice and Design 1", 1, "REMETHS", "hard", 3),
    ("CPEPRAC", "CpE Laws and Professional Practice", 2, "EMBDSYS", "hard", 3),
    ("CPECOG1", "CpE Elective 1 Lecture", 2, "EMBDSYS", "hard", 3),
    ("LBYCPF3", "CpE Elective 1 Laboratory", 1, "CPECOG1", "co_requisite", 3),
    # ── Checklist Term 10 -> term_number 1 ─────────────────────────────────
    ("LCENWRD", "Encountering the Word in the World", 3, None, "none", 1),
    ("EMERTEC", "Emerging Technologies in CpE", 3, "EMBDSYS", "hard", 1),
    ("THSCP4B", "CpE Practice and Design 2", 1, "THSCP4A", "hard", 1),
    ("ENGTREP", "Technopreneurship 101", 3, "EMBDSYS", "hard", 1),
    ("CONETSC", "Computer Networks and Security Lecture", 3, "DIGDACM", "hard", 1),
    ("LBYCPB4", "Computer Networks and Security Laboratory", 1, "CONETSC", "co_requisite", 1),
    ("CPECAPS", "Operational Technologies", 1, "LBYCPB4", "co_requisite", 1),
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
    ("CPETRIP", "Seminars and Field Trips for CpE", 1, "CPECAPS", "hard", 3),
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

# Assign prerequisites in a second pass
for code, title, units, prereq_code, prereq_type, term_number in subjects_data:
    if prereq_code:
        subj = subj_map[code]
        subj.prerequisite = subj_map[prereq_code]
        subj.prerequisite_type = prereq_type
        subj.save(update_fields=["prerequisite", "prerequisite_type"])

print(f"  ✓ {len(subjects_data)} subjects created/verified")

# ── 5. Rooms ────────────────────────────────────────────────────────────────
rooms_data = [
    ("GK101", 40), ("GK102", 40), ("GK103", 40), ("GK104", 40), ("GK105", 40),
    ("LS202", 35), ("LS203", 35), ("LS204", 35),
    ("AG1901", 50),
]
created_rooms = []
for name, cap in rooms_data:
    r, _ = Room.objects.get_or_create(room_name=name, defaults={"capacity": cap})
    created_rooms.append(r)
print(f"  ✓ {len(rooms_data)} rooms created/verified")

# ── 6. Academic Terms + Schedules ──────────────────────────────────────────────
# 7 days x 7 periods = 49 slots – enough for all subjects in each term.
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
PERIODS = [
    (time(7, 30),  time(9, 0)),
    (time(9, 0),   time(10, 30)),
    (time(10, 30), time(12, 0)),
    (time(13, 0),  time(14, 30)),
    (time(14, 30), time(16, 0)),
    (time(16, 0),  time(17, 30)),
    (time(17, 30), time(19, 0)),
]

MAX_FACULTY_UNITS = 16


def _select_faculty_for_subject(subject, candidate_indices, faculty_loads):
    available_indices = [
        idx for idx in candidate_indices
        if faculty_loads.get(idx, 0) + subject.units <= MAX_FACULTY_UNITS
    ]
    if not available_indices:
        raise RuntimeError(
            f"No faculty can take {subject.subject_code} without exceeding {MAX_FACULTY_UNITS} units"
        )
    return min(available_indices, key=lambda idx: faculty_loads.get(idx, 0))


def auto_schedule_term(subject_codes, faculty_count, room_count, faculty_loads=None):
    """
    Create a conflict‑free timetable for one term.
    Subjects are assigned to slots in round‑robin order across all (day,period)
    combinations, so they spread naturally across the week and across times.
    Co‑requisite labs are placed on the same day as their lecture.
    """
    if faculty_loads is None:
        faculty_loads = {idx: 0 for idx in range(faculty_count)}

    used_faculty_slots = set()   # (faculty_idx, day_idx, period_idx)
    used_room_slots = set()      # (room_idx, day_idx, period_idx)
    placement = {}               # code -> (faculty_idx, room_idx, day_idx, period_idx)
    schedule_defs = []

    # Identify co‑requisite pairs: lecture -> lab
    co_req_map = {}
    for code in subject_codes:
        subj = subj_map[code]
        if subj.prerequisite_type == "co_requisite" and subj.prerequisite:
            lecture_code = subj.prerequisite.subject_code
            if lecture_code in subject_codes:
                co_req_map[lecture_code] = code

    # Separate lectures and labs
    lectures = [code for code in subject_codes if code not in co_req_map.values()]
    labs = [code for code in subject_codes if code in co_req_map.values()]

    # We'll assign slots in a round‑robin fashion over all (day, period) slots.
    # We'll keep a counter to cycle through slots.
    slot_counter = 0
    total_slots = len(DAYS) * len(PERIODS)

    def next_slot():
        nonlocal slot_counter
        day_idx = (slot_counter // len(PERIODS)) % len(DAYS)
        period_idx = slot_counter % len(PERIODS)
        slot_counter += 1
        return day_idx, period_idx

    # First assign lectures
    for code in lectures:
        subject = subj_map[code]
        fac_idx = _select_faculty_for_subject(subject, list(range(faculty_count)), faculty_loads)
        room_idx = random.randrange(room_count)
        # Find a free slot for this faculty/room
        found = False
        # Try the next 2*total_slots slots to avoid infinite loop
        for _ in range(total_slots * 2):
            day_idx, period_idx = next_slot()
            if (fac_idx, day_idx, period_idx) not in used_faculty_slots and \
               (room_idx, day_idx, period_idx) not in used_room_slots:
                found = True
                break
        if not found:
            raise RuntimeError(f"Could not find free slot for lecture {code}")
        used_faculty_slots.add((fac_idx, day_idx, period_idx))
        used_room_slots.add((room_idx, day_idx, period_idx))
        placement[code] = (fac_idx, room_idx, day_idx, period_idx)
        faculty_loads[fac_idx] += subject.units
        tstart, tend = PERIODS[period_idx]
        slots = created_rooms[room_idx].capacity
        schedule_defs.append((code, fac_idx, room_idx, DAYS[day_idx], tstart, tend, slots))

    # Now assign labs: try to put on same day as lecture, and later period if possible
    for code in labs:
        lecture_code = subj_map[code].prerequisite.subject_code
        subject = subj_map[code]
        if lecture_code in placement:
            fac_idx, room_idx, lec_day, lec_period = placement[lecture_code]
            candidate_indices = [fac_idx] + [idx for idx in range(faculty_count) if idx != fac_idx]
            fac_idx = _select_faculty_for_subject(subject, candidate_indices, faculty_loads)
            # Try to find a free slot on same day, starting from lec_period+1
            found = False
            for period_offset in range(len(PERIODS)):
                period_idx = (lec_period + 1 + period_offset) % len(PERIODS)
                if (fac_idx, lec_day, period_idx) not in used_faculty_slots and \
                   (room_idx, lec_day, period_idx) not in used_room_slots:
                    day_idx = lec_day
                    found = True
                    break
            if not found:
                # If no free slot on same day, fallback to any free slot
                for _ in range(total_slots * 2):
                    day_idx, period_idx = next_slot()
                    if (fac_idx, day_idx, period_idx) not in used_faculty_slots and \
                       (room_idx, day_idx, period_idx) not in used_room_slots:
                        found = True
                        break
                if not found:
                    raise RuntimeError(f"Could not find free slot for lab {code}")
        else:
            # Lecture not in this term (unlikely) – assign any free slot
            fac_idx = _select_faculty_for_subject(subject, list(range(faculty_count)), faculty_loads)
            room_idx = random.randrange(room_count)
            for _ in range(total_slots * 2):
                day_idx, period_idx = next_slot()
                if (fac_idx, day_idx, period_idx) not in used_faculty_slots and \
                   (room_idx, day_idx, period_idx) not in used_room_slots:
                    found = True
                    break
            if not found:
                raise RuntimeError(f"Could not find free slot for lab {code}")
        used_faculty_slots.add((fac_idx, day_idx, period_idx))
        used_room_slots.add((room_idx, day_idx, period_idx))
        placement[code] = (fac_idx, room_idx, day_idx, period_idx)
        faculty_loads[fac_idx] += subject.units
        tstart, tend = PERIODS[period_idx]
        slots = created_rooms[room_idx].capacity
        schedule_defs.append((code, fac_idx, room_idx, DAYS[day_idx], tstart, tend, slots))

    return schedule_defs

def create_term_with_schedules(term_name, term_number, is_active, schedule_defs):
    term, _ = AcademicTerm.objects.get_or_create(
        term_name=term_name,
        defaults={"is_active": is_active, "term_number": term_number}
    )
    term.is_active = is_active
    term.term_number = term_number
    term.save()
    status = "Active" if is_active else "Inactive"
    print(f"  ✓ {status} term: {term.term_name} (Term {term.term_number})")

    created_schedules = []
    for subj_code, fac_idx, room_idx, day, tstart, tend, slots in schedule_defs:
        subj = subj_map[subj_code]
        if subj.term_number != term_number:
            raise ValueError(
                f"{subj_code} has term_number={subj.term_number}, "
                f"cannot be scheduled under {term_name} (term_number={term_number})"
            )
        sched, _created = Schedule.objects.get_or_create(
            term=term,
            subject=subj,
            faculty=created_faculty[fac_idx],
            room=created_rooms[room_idx],
            day=day,
            time_start=tstart,
            time_end=tend,
            defaults={"total_slots": slots, "available_slots": slots}
        )
        created_schedules.append(sched)

    for faculty in created_faculty:
        load = faculty.current_load(term)
        if load > faculty.max_teaching_load:
            raise RuntimeError(
                f"Faculty {faculty.full_name} is overloaded at {load} units for {term.term_name}"
            )

    print(f"  ✓ {len(schedule_defs)} schedules created/verified for {term.term_name}")
    return term, created_schedules

def _find_free_slots(term):
    """Return list of (day_idx, period_idx) not used by any schedule in this term."""
    existing = set()
    for sched in Schedule.objects.filter(term=term):
        day = sched.day
        period = None
        for i, (start, end) in enumerate(PERIODS):
            if sched.time_start == start and sched.time_end == end:
                period = i
                break
        if period is not None:
            existing.add((day, period))
    free = []
    for day_idx, day in enumerate(DAYS):
        for period_idx in range(len(PERIODS)):
            if (day, period_idx) not in existing:
                free.append((day_idx, period_idx))
    return free

def add_extra_sections(term, subject_codes, faculty_indices, room_indices, free_slots, faculty_loads):
    """Create an extra section for each given subject using free slots."""
    if not free_slots:
        print(f"  ⚠ No free slots available for extra sections in {term.term_name}")
        return
    extra_scheds = []
    for idx, code in enumerate(subject_codes):
        if idx >= len(free_slots):
            break
        subj = subj_map[code]
        day_idx, period_idx = free_slots[idx]
        day = DAYS[day_idx]
        tstart, tend = PERIODS[period_idx]
        candidate_indices = [idx for idx in faculty_indices if idx < len(created_faculty)]
        if not candidate_indices:
            raise RuntimeError(f"No faculty available for extra section {subj.subject_code}")
        fac_idx = _select_faculty_for_subject(subj, candidate_indices, faculty_loads)
        fac = created_faculty[fac_idx]
        room = created_rooms[room_indices[idx % len(room_indices)]]
        slots = room.capacity
        sched, _ = Schedule.objects.get_or_create(
            term=term,
            subject=subj,
            faculty=fac,
            room=room,
            day=day,
            time_start=tstart,
            time_end=tend,
            defaults={"total_slots": slots, "available_slots": slots}
        )
        faculty_loads[fac_idx] += subj.units
        extra_scheds.append(sched)
    print(f"  ✓ Added {len(extra_scheds)} extra sections for {term.term_name}")

# Deactivate any pre-existing terms
AcademicTerm.objects.all().update(is_active=False)

term1_codes = [code for code, _, _, _, _, tn in subjects_data if tn == 1]
term2_codes = [code for code, _, _, _, _, tn in subjects_data if tn == 2]
term3_codes = [code for code, _, _, _, _, tn in subjects_data if tn == 3]

# Generate primary schedules for all terms
term1_faculty_loads = {idx: 0 for idx in range(len(created_faculty))}
term2_faculty_loads = {idx: 0 for idx in range(len(created_faculty))}
term3_faculty_loads = {idx: 0 for idx in range(len(created_faculty))}

schedule_defs_term1 = auto_schedule_term(term1_codes, len(created_faculty), len(created_rooms), term1_faculty_loads)
schedule_defs_term2 = auto_schedule_term(term2_codes, len(created_faculty), len(created_rooms), term2_faculty_loads)
schedule_defs_term3 = auto_schedule_term(term3_codes, len(created_faculty), len(created_rooms), term3_faculty_loads)

term1, _ = create_term_with_schedules("AY 2025-2026 Term 1", 1, False, schedule_defs_term1)
term2, _ = create_term_with_schedules("AY 2025-2026 Term 2", 2, False, schedule_defs_term2)
term3, created_schedules = create_term_with_schedules("AY 2025-2026 Term 3", 3, True, schedule_defs_term3)

# ── Add extra sections (demonstrating multiple offerings) ──────────────────
extra_subjects = ["CALENG1", "LBYCPA1", "FUNDCKT", "ENGPHYS", "LOGDSGN", "MICPROS"]
extra_faculty = list(range(4, len(created_faculty)))   # use different faculty
extra_rooms   = list(range(0, 4))                     # use different rooms

free_term1 = _find_free_slots(term1)
free_term2 = _find_free_slots(term2)
free_term3 = _find_free_slots(term3)

add_extra_sections(term1, extra_subjects, extra_faculty, extra_rooms, free_term1, term1_faculty_loads)
add_extra_sections(term2, extra_subjects, extra_faculty, extra_rooms, free_term2, term2_faculty_loads)
add_extra_sections(term3, extra_subjects, extra_faculty, extra_rooms, free_term3, term3_faculty_loads)

print("\n✅ Seed complete! Login credentials:")
print("   Admin:    admin   / admin1234   → /admin/")
print("   Faculty:  faculty1 / faculty1234  → /faculty/dashboard/")
print("   Student:  student1 / student1234  → /student/dashboard/")
print("\nStart the server:  python manage.py runserver")