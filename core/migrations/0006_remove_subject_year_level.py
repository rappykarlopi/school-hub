from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_subject_year_level"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="subject",
            name="year_level",
        ),
    ]
