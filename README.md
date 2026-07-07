# LBYCPG3 — Computer Engineering Enlistment and Scheduler System

A web-based student enlistment and class scheduling system built for the Computer Engineering department. Supports three user roles (Admin, Faculty, Student), a 10-step enlistment workflow, conflict detection, three types of prerequisite checking, and a downloadable enrollment-form PDF.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Quick Start](#quick-start)
4. [Demo Credentials](#demo-credentials)
5. [User Roles & Access](#user-roles--access)
6. [URL Reference](#url-reference)
7. [Database Models](#database-models)
8. [Prerequisite System](#prerequisite-system)
9. [Enlistment Workflow (10 Steps)](#enlistment-workflow-10-steps)
10. [Validation Engine](#validation-engine)
11. [Admin Panel](#admin-panel)
12. [Templates](#templates)
13. [Seed Data](#seed-data)
14. [Adding a New Term](#adding-a-new-term)
15. [Common Issues](#common-issues)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Framework | Django 5+ (tested on Django 6) |
| Database | SQLite (file: `db.sqlite3`) |
| CSS Framework | Tailwind CSS via CDN (no build step) |
| Auth | Django built-in `AbstractUser` with role extension |
| Fonts | Inter (Google Fonts, loaded via CDN) |
| PDF Export | ReportLab |

Install the PDF dependency with:

```bash
pip install reportlab
```

---

## Project Structure

```
enlistment_system/
│
├── manage.py                   # Django management entry point
├── seed_data.py                # One-time script to populate demo data
├── db.sqlite3                  # SQLite database (auto-created after migrate)
│
├── enlistment/                 # Django project configuration package
│   ├── settings.py             # All project settings (DB, apps, auth, timezone)
│   ├── urls.py                 # Root URL dispatcher (admin + core app)
│   └── wsgi.py                 # WSGI entry point for deployment
│
├── core/                       # Main application package
│   ├── models.py               # All database models (Phase 1)
│   ├── admin.py                # Django Admin registrations (Phase 2)
│   ├── views.py                # All view logic and workflow engine (Phase 3)
│   ├── urls.py                 # URL patterns for all student/faculty/auth views
│   └── templatetags/
│       └── core_extras.py      # Custom template filter: dict_key
│
└── templates/
    └── core/
        ├── base.html           # Shared layout: navbar, flash messages, footer
        ├── login.html          # Standalone login page (no base inheritance)
        ├── student/
        │   ├── dashboard.html      # Cart + confirmed enrollments overview
        │   ├── subject_list.html   # Browse & search available sections
        │   ├── schedule.html       # Weekly schedule grid (confirmed only)
        │   └── enrollment_form.html # Printable official enrollment form
        └── faculty/
            ├── dashboard.html      # Teaching load summary + unit bar
            ├── schedule.html       # Weekly teaching schedule grid
            └── class_list.html     # Per-section list of enrolled students
```

---

## Quick Start

### 1. Prerequisites

Make sure Python 3.10 or higher is installed:

```bash
python --version
```

### 2. Install Django

```bash
pip install django
```

### 3. Navigate into the project folder

```bash
cd enlistment_system
```

### 4. Create the database tables

```bash
python manage.py migrate
```

### 5. Populate demo data

```bash
python seed_data.py
```

This creates 1 admin, 3 faculty members, 3 students, 8 subjects (including a co-requisite example), 6 rooms, 1 active academic term, and 8 schedule sections. It is safe to run multiple times — it uses `get_or_create` throughout and will not duplicate records.

### 6. Start the development server

```bash
python manage.py runserver
```

### 7. Open in your browser

```
http://127.0.0.1:8000
```

To stop the server, press `Ctrl + C` in the terminal.

---

## Demo Credentials

| Role | Username | Password | Redirects To |
|---|---|---|---|
| Admin | `admin` | `admin1234` | `/admin/` (Django admin panel) |
| Faculty | `faculty1` | `faculty1234` | `/faculty/dashboard/` |
| Faculty | `faculty2` | `faculty1234` | `/faculty/dashboard/` |
| Faculty | `faculty3` | `faculty1234` | `/faculty/dashboard/` |
| Student | `student1` | `student1234` | `/student/dashboard/` |
| Student | `student2` | `student1234` | `/student/dashboard/` |
| Student | `student3` | `student1234` | `/student/dashboard/` |

---

## User Roles & Access

The system uses Django's built-in authentication extended with a `role` field on the custom `User` model.

### Admin

- Accesses the full Django Admin panel at `/admin/`
- Can create, edit, and delete all records: Users, Students, Faculty, Subjects, Rooms, Academic Terms, Schedules, and Enrollments
- Can activate a term using the "Set as Active Term" admin action
- Can manually override enrollment statuses and slot counts

### Faculty

- Sees only their own data
- Views their weekly teaching schedule
- Views the full class list (enrolled students) for each section they handle
- Cannot access student enlistment views or the admin panel

### Student

- Sees only their own data
- Browses available subject offerings for the active term
- Adds subjects to cart (with live validation)
- Confirms enlistment atomically
- Views their confirmed weekly schedule
- Downloads their official enrollment form as a PDF

Access to the wrong role's views redirects back to the login page with an error message.

---

## URL Reference

### Auth

| URL | View | Description |
|---|---|---|
| `/` | `login_view` | Login page; redirects by role on success |
| `/logout/` | `logout_view` | Logs out and redirects to login |

### Student

| URL | View | Description |
|---|---|---|
| `/student/dashboard/` | `student_dashboard` | Cart, confirmed enrollments, unit totals |
| `/student/subjects/` | `subject_list` | Browse and search available sections |
| `/student/cart/add/<id>/` | `add_to_cart` | POST — add a schedule section to cart |
| `/student/cart/remove/<id>/` | `remove_from_cart` | POST — remove an item from cart |
| `/student/confirm/` | `confirm_enlistment` | POST — confirm all cart items atomically |
| `/student/schedule/` | `student_schedule` | Weekly schedule grid (confirmed only) |
| `/student/enrollment-form/` | `enrollment_form` | Enrollment form page |
| `/student/enrollment-form/pdf/` | `enrollment_form_pdf` | Downloads the enrollment form as a PDF |

### Faculty

| URL | View | Description |
|---|---|---|
| `/faculty/dashboard/` | `faculty_dashboard` | Teaching load summary for active term |
| `/faculty/schedule/` | `faculty_schedule` | Weekly teaching schedule grid |
| `/faculty/class-list/` | `faculty_class_list` | All sections with full student rosters |

### Admin

| URL | Description |
|---|---|
| `/admin/` | Full Django Admin panel |

---

## Database Models

All models live in `core/models.py`.

### User
Extends Django's `AbstractUser`. Adds a `role` field with three choices: `admin`, `faculty`, `student`. Helper properties `is_admin`, `is_faculty`, `is_student` are available on every user instance.

### Faculty
One-to-one profile linked to a `User` with role `faculty`. Stores `first_name`, `last_name`, `department`, and `max_teaching_load` (in units). Has a `current_load(term)` method that sums units across assigned schedules.

### Student
One-to-one profile linked to a `User` with role `student`. Stores `student_number` (unique), `first_name`, `last_name`, and `program`.

### Subject
Stores `subject_code` (unique), `subject_title`, `units`, a self-referential `prerequisite` FK, and `prerequisite_type` (see [Prerequisite System](#prerequisite-system) below).

### Room
Stores `room_name` (unique) and `capacity`.

### AcademicTerm
Stores `term_name` and `is_active`. Only one term should be active at a time. Use the admin action "Set selected term as the ACTIVE term" to safely switch terms.

### Schedule
Represents one section offering of a subject in a term. Links `term`, `subject`, `faculty`, `room`, `day`, `time_start`, `time_end`, `total_slots`, and `available_slots`. Two database-level `UniqueConstraint`s prevent double-booking a room or faculty member at the exact same day/time. A `clean()` method also catches partial time overlaps.

### Enrollment
Links a `student` to a `schedule` with a `status` of either `Cart` or `Confirmed`. The `clean()` method is the core validation engine. `save()` always calls `full_clean()` so validation cannot be bypassed.

---

## Prerequisite System

Set per-subject in the `prerequisite` and `prerequisite_type` fields on the `Subject` model. There are three types:

### Hard Prerequisite
The student must have a `Confirmed` enrollment record for the prerequisite subject from any past or current term before they can enlist in this subject. This represents a subject that must be passed first.

Example: A student cannot enlist in `CMPE30B` unless they have a confirmed enrollment in `CMPE30A`.

### Soft Prerequisite
The student must have a `Confirmed` enrollment record for the prerequisite subject at least once across any term — regardless of whether they passed or failed. They simply must have taken it.

Example: A student who failed `ENGMATH1` last term can still enlist in `ENGMATH2` this term, because they have taken it before.

### Co-requisite
The prerequisite subject must be in the student's cart or already confirmed for the **same active term**. Both subjects must be enrolled together. The rule is enforced when the student clicks **Confirm All Enlistment**, so the full cart is validated as a set.

Example: A laboratory subject requires its paired lecture subject to be enrolled in the same term. The lecture does not require the lab, but the lab cannot be confirmed without the lecture.

To configure in the admin panel: go to **Subjects**, select a subject, set the `Prerequisite` field and the `Prerequisite Type` dropdown accordingly.

---

## Enlistment Workflow (10 Steps)

This follows the project specification exactly.

| Step | Action | Where it happens |
|---|---|---|
| 1 | Student logs in | `login_view` → redirects to dashboard |
| 2 | Active term is auto-resolved | `_get_active_term()` helper, used across all student views |
| 3 | Student views available subjects | `subject_list` view — shows all Schedule offerings for the active term |
| 4 | Student selects a desired subject | "Add to Cart" button on the subject list page |
| 5 | System checks prerequisites and conflicts | Hard/soft prerequisite checks run as the subject is added; the full cart is validated on confirmation for prerequisites, co-requisites, duplicates, conflicts, and slot availability |
| 6 | Subject added to enlistment cart | `add_to_cart` view creates `Enrollment` with `status='Cart'` |
| 7 | Student confirms enlistment | "Confirm All Enlistment" button on the dashboard |
| 8 | System updates available slots | `confirm_enlistment` view uses `transaction.atomic()` + `SELECT FOR UPDATE` to decrement `available_slots` safely |
| 9 | Enrollment record generated | All cart items flipped to `status='Confirmed'` inside the same transaction |
| 10 | Student downloads enrollment form | `enrollment_form` and `enrollment_form_pdf` render the official record and PDF export |

---

## Validation Engine

Validation is handled in `Enrollment.clean()` and the confirmation-time cart validator in `models.py`. The app checks the full cart before enrollment is confirmed.

**Check 1 — Prerequisite (type-aware)**
Branches on `subject.prerequisite_type` for hard, soft, and co-requisite rules. Each case raises a descriptive error explaining which subject is missing and what type of requirement it is.

**Check 2 — Duplicate subject in same term**
Prevents a student from adding the same subject code twice in one term (even across different sections). Checks both `Cart` and `Confirmed` statuses.

**Check 3 — Time conflict**
Uses the overlap formula `start_A < end_B AND end_A > start_B` to detect any schedule that overlaps with an existing cart or confirmed enrollment on the same day in the same term.

**Check 4 — Slot availability**
Only triggers when `status='Confirmed'`. Ensures `available_slots > 0` before confirming. The actual decrement in `confirm_enlistment` also uses `SELECT FOR UPDATE` to handle concurrent requests safely.

If any check fails, the confirmation is blocked and the error is shown as a flash message — no data is written to the database.

---

## Admin Panel

Access at `/admin/` using the `admin` account.

### What you can manage

| Section | Capabilities |
|---|---|
| Users | Create/edit users, assign roles, set passwords |
| Faculty Members | Manage faculty profiles and max teaching loads |
| Students | Manage student profiles, view their enrollments inline |
| Subjects | Create subjects, set prerequisite and prereq type |
| Rooms | Manage rooms and capacities |
| Academic Terms | Create terms, use the "Set as Active" action to switch terms |
| Schedules | Create section offerings, see fill-rate bar per section |
| Enrollments | View and edit enrollment records with color-coded status badges |

### Useful admin features

- **Fill-rate bar** on the Schedule list — green/amber/red visual showing how full each section is
- **Slot utilization filter** on Schedules — filter by Full, Almost Full, or Has Available Slots
- **Status badges** on Enrollments — green pill for Confirmed, yellow for In Cart
- **Make Active Term** action — safely sets one term active and deactivates all others
- **Role-aware inlines** on Users — editing a Faculty user shows the Faculty profile inline; editing a Student user shows the Student profile inline

---

## Templates

All templates extend `core/base.html` except `login.html` which is fully standalone.

### base.html
Provides the navigation bar (role-aware links), flash message display area, page `<main>` wrapper, and footer. Loads Tailwind CSS and the Inter font via CDN. Navigation links change automatically based on `user.role`.

### login.html
Standalone page with a centered card layout, role legend, and CSRF-protected login form. Displays error messages if authentication fails.

### student/dashboard.html
Shows stat cards (confirmed units, cart units, subject counts), the enlistment cart with a "Confirm All" button and per-item remove, and the confirmed enrollments table with a link to the printable form.

### student/subject_list.html
Search bar (filters by subject code, title, faculty name), a full table of all Schedule offerings for the active term with slot availability indicators, prerequisite column, and per-row Add to Cart / Already Added state.

### student/schedule.html
Day-by-day accordion list showing confirmed enrollments grouped by weekday. Uses the `dict_key` custom template filter to access the `schedule_by_day` dictionary.

### student/enrollment_form.html
Print-ready document with university header, student info block, enrolled subjects table with totals, and signature lines. A download button exports the form as a PDF, while the page also supports browser printing.

### faculty/dashboard.html
Teaching load stat cards, a unit utilization progress bar (`widthratio` tag), and a summary table of all assigned sections.

### faculty/schedule.html
Day-by-day layout of the faculty member's teaching schedule with time, subject, and room details.

### faculty/class_list.html
Accordion of sections, each with a full student roster table (student number, name, program, enrollment date) and a count badge.

---

## Seed Data

`seed_data.py` populates the following on first run:

**Users & Profiles**
- 1 admin superuser (`admin`)
- 3 faculty members (`faculty1`, `faculty2`, `faculty3`) — Maria Santos (CpE), Jose Reyes (CpE), Ricardo Cruz (Math)
- 3 students (`student1`, `student2`, `student3`) — Ana Dela Cruz, Marco Bautista, Lena Garcia

**Subjects (8 total)**

| Code | Title | Units | Prerequisite | Type |
|---|---|---|---|---|
| CMPDESN | Computer Design | 3 | — | — |
| CMPE30A | Computer Engineering I | 3 | — | — |
| CMPE30B | Computer Engineering II | 3 | CMPE30A | Hard |
| LBYCPG3 | CPE Integrative Project III | 2 | CMPE30B | Hard |
| ENGMATH1 | Engineering Mathematics I | 3 | — | — |
| ENGMATH2 | Engineering Mathematics II | 3 | ENGMATH1 | Soft |
| DATASRUC | Data Structures | 3 | CMPE30A | Hard |
| CMPE30AL | Computer Engineering I Lab | 1 | CMPE30A | Co-requisite |

**Rooms:** GK101, GK102, GK103, LS202, LS203, AG1901

**Active Term:** AY 2025-2026 Term 3

**Schedules:** 8 sections spread across Monday through Saturday.

---

## Adding a New Term

1. Log in as `admin` and go to `/admin/`
2. Under **Academic Terms**, click **Add Academic Term**
3. Enter the term name (e.g., `AY 2026-2027 Term 1`) and save
4. Go back to the Academic Terms list, select the new term, choose the action **"Set selected term as the ACTIVE term"**, and click Go
5. Under **Schedules**, create new Schedule offerings linked to the new term
6. Students can now enlist in the new term's subjects

---

## Common Issues

**`no such table` error on first run**
You skipped the migrate step. Run `python manage.py migrate` before anything else.

**Login works but profile not found error**
The user exists but no Faculty or Student profile is linked to them. Go to `/admin/`, find the user, and create the profile inline on their edit page, or run `seed_data.py` again.

**Changes to models.py not reflected**
After editing any model, run:
```bash
python manage.py makemigrations
python manage.py migrate
```

**No subjects showing on the subject list page**
Either no Academic Term is marked active, or no Schedules exist for the active term. Check both in the admin panel.

**Port 8000 already in use**
Run the server on a different port:
```bash
python manage.py runserver 8080
```
Then visit `http://127.0.0.1:8080`.

**Static directory warning on startup**
This is harmless in development. The warning appears because `STATICFILES_DIRS` points to a `static/` folder. It has been created by the setup steps — if it reappears, run `mkdir static` inside the project root.
