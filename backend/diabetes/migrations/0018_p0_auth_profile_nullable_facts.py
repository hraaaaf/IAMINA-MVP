from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_p0_auth_profile_nullable_facts"),
        ("diabetes", "0017_patientprofile_to_extension"),
    ]

    operations = [
        migrations.AlterField(
            model_name="diabetesprofile",
            name="diabetes_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("type1", "Type 1"),
                    ("type2", "Type 2"),
                    ("gestational", "Gestationnel"),
                    ("prediabetes", "Prediabete"),
                ],
                help_text="Patient-declared/validated type of diabetes. NULL = unknown.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="diabetesprofile",
            name="treatment_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("insulin_pump", "Pompe a insuline"),
                    ("insulin_injections", "Injections d'insuline"),
                    ("oral_meds", "Medicaments oraux"),
                    ("diet_exercise", "Regime et exercice"),
                    ("insulin", "Insuline"),
                ],
                help_text="Patient-declared current treatment approach. NULL = unknown.",
                max_length=20,
                null=True,
            ),
        ),
    ]
