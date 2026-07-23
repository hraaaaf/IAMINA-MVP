from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_backfill_diabetes_module"),
    ]

    operations = [
        migrations.AlterField(
            model_name="basepatientprofile",
            name="date_of_birth",
            field=models.DateField(
                blank=True,
                help_text="Patient-declared date of birth. NULL = not provided.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="basepatientprofile",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("male", "Homme"), ("female", "Femme")],
                help_text="Patient-declared gender. NULL = not provided.",
                max_length=6,
                null=True,
            ),
        ),
    ]
