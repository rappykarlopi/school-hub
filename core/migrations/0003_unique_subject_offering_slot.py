from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_subject_and_academicterm_term_number"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="schedule",
            constraint=models.UniqueConstraint(
                fields=("term", "subject", "day", "time_start", "time_end"),
                name="unique_subject_offering_slot",
            ),
        ),
    ]
