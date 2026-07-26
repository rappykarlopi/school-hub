from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_enrollment_term_subject_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="subject",
            name="year_level",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Year 1"), (2, "Year 2"), (3, "Year 3"), (4, "Year 4")],
                default=1,
                help_text="Year level in the Bachelor of Science in Computer Engineering curriculum.",
            ),
        ),
    ]
