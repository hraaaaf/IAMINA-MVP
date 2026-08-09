from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0022_context_unknown_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="diabetesprofile",
            name="ramadan_start_date",
            field=models.DateField(
                blank=True,
                help_text=(
                    "Patient-declared start of an optional Ramadan journal context. "
                    "NULL means no period is configured."
                ),
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="diabetesprofile",
            name="ramadan_end_date",
            field=models.DateField(
                blank=True,
                help_text=(
                    "Patient-declared end of an optional Ramadan journal context. "
                    "NULL means no period is configured."
                ),
                null=True,
            ),
        ),
    ]
