from django.db import migrations, models
import django.db.models.deletion


def populate_enrollment_identity(apps, schema_editor):
    Enrollment = apps.get_model("core", "Enrollment")

    for enrollment in Enrollment.objects.select_related("schedule").iterator():
        enrollment.term_id = enrollment.schedule.term_id
        enrollment.subject_id = enrollment.schedule.subject_id
        enrollment.save(update_fields=["term", "subject"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_unique_subject_offering_slot"),
    ]

    operations = [
        migrations.AddField(
            model_name="enrollment",
            name="term",
            field=models.ForeignKey(
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="core.academicterm",
            ),
        ),
        migrations.AddField(
            model_name="enrollment",
            name="subject",
            field=models.ForeignKey(
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="core.subject",
            ),
        ),
        migrations.RunPython(populate_enrollment_identity, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="enrollment",
            name="term",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="core.academicterm",
            ),
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="subject",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="core.subject",
            ),
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(
                fields=("student", "term", "subject"),
                name="unique_student_subject_per_term",
            ),
        ),
    ]
