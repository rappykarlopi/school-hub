from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="subject",
            name="term_number",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Term 1"), (2, "Term 2"), (3, "Term 3")],
                default=1,
                help_text="Which trimester of the curriculum this subject is normally offered in "
                          "(e.g. Term 3), and which students may enlist in it. "
                          "Set and changed only by the administrator.",
            ),
        ),
        migrations.AddField(
            model_name="academicterm",
            name="term_number",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Term 1"), (2, "Term 2"), (3, "Term 3")],
                default=1,
                help_text="Which trimester this academic term represents. Students will only "
                          "see and enlist in Subjects whose term_number matches this value.",
            ),
        ),
        migrations.AlterModelOptions(
            name="subject",
            options={
                "ordering": ["term_number", "subject_code"],
                "verbose_name": "Subject",
                "verbose_name_plural": "Subjects",
            },
        ),
    ]
