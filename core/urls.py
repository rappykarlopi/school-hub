"""
LBYCPG3 – core/urls.py
URL patterns for all student, faculty, and auth views.
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────
    path("",          views.login_view,  name="login"),
    path("logout/",   views.logout_view, name="logout"),
    path("api/classes/create/", views.create_class, name="create_class"),

    # ── Student ───────────────────────────────────────────────────────
    path("student/dashboard/",        views.student_dashboard,  name="student_dashboard"),
    path("student/subjects/",         views.subject_list,        name="subject_list"),
    path("student/cart/add/<int:schedule_id>/",
                                      views.add_to_cart,         name="add_to_cart"),
    path("student/cart/remove/<int:enrollment_id>/",
                                      views.remove_from_cart,    name="remove_from_cart"),
    path("student/confirm/",          views.confirm_enlistment,  name="confirm_enlistment"),
    path("student/schedule/",         views.student_schedule,    name="student_schedule"),
    path("student/enrollment-form/",  views.enrollment_form,     name="enrollment_form"),
    path("student/enrollment-form/pdf/", views.enrollment_form_pdf, name="enrollment_form_pdf"),

    # ── Faculty ───────────────────────────────────────────────────────
    path("faculty/dashboard/",        views.faculty_dashboard,   name="faculty_dashboard"),
    path("faculty/schedule/",         views.faculty_schedule,    name="faculty_schedule"),
    path("faculty/class-list/",       views.faculty_class_list,  name="faculty_class_list"),
]
