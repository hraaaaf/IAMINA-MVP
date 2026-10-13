"""D7 optional diagnosis codes, without inferring a clinical category."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0034_diabetesprofile_declared_treatments_v1"),
    ]

    operations = [
        migrations.AlterField(
            model_name="diabetesprofile",
            name="diabetes_type",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("type1", "Type 1"),
                    ("type2", "Type 2"),
                    ("gestational", "Gestationnel"),
                    ("prediabetes", "Prediabete"),
                    ("other", "Another patient-declared diagnosis"),
                    ("unknown", "Patient unsure or answering later"),
                ],
                null=True,
                blank=True,
                help_text="Patient-declared/validated type of diabetes. NULL = unknown.",
            ),
        ),
    ]
