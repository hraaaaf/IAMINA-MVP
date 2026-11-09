"""D7 additive declarations, without destructive or inferred legacy backfill."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0033_logentry_meal_episode_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="diabetesprofile",
            name="treatment_declaration_state",
            field=models.CharField(
                max_length=24,
                choices=[
                    ("not_answered", "Not answered"),
                    ("unsure", "Patient unsure"),
                    ("declared", "Patient declarations"),
                    ("none_declared", "Patient explicitly declared none"),
                ],
                default="not_answered",
                help_text="D7 declaration state, separate from clinical profile completeness.",
            ),
        ),
        migrations.AddField(
            model_name="diabetesprofile",
            name="treatment_declarations",
            field=models.JSONField(
                default=list,
                blank=True,
                help_text="Patient-declared treatment codes (v1), never prescriptions.",
            ),
        ),
        migrations.AddField(
            model_name="diabetesprofile",
            name="treatment_declaration_version",
            field=models.PositiveSmallIntegerField(
                default=1,
                help_text="Version of D7 treatment declaration vocabulary.",
            ),
        ),
        migrations.AddField(
            model_name="diabetesprofile",
            name="treatment_declaration_source",
            field=models.CharField(
                max_length=24,
                choices=[("patient_declared", "Patient declared")],
                null=True,
                blank=True,
                help_text="Provenance of an explicit D7 declaration; NULL for legacy rows.",
            ),
        ),
        migrations.AddField(
            model_name="diabetesprofile",
            name="treatment_declaration_updated_at",
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="Server timestamp of explicit patient D7 declaration.",
            ),
        ),
    ]
