"""D18: optional birth-year granularity and append-only weight observations."""

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_auth_abuse_bucket"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="basepatientprofile",
            name="birth_year",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text="Patient-declared year only; no exact birth date is inferred.",
            ),
        ),
        migrations.CreateModel(
            name="PatientWeightObservation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True,
                        serialize=False, verbose_name="ID",
                    ),
                ),
                ("client_uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("value", models.DecimalField(decimal_places=2, max_digits=7)),
                (
                    "unit",
                    models.CharField(
                        max_length=2, choices=[("kg", "Kilograms"), ("lb", "Pounds")]
                    ),
                ),
                ("weight_kg", models.DecimalField(decimal_places=2, max_digits=7)),
                ("measured_at", models.DateTimeField()),
                (
                    "provenance",
                    models.CharField(
                        max_length=32,
                        choices=[("patient_declared", "Patient declared")],
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weight_observations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-measured_at", "-pk"),
                "indexes": [
                    models.Index(
                        fields=["patient", "-measured_at"],
                        name="core_d18_weight_owner_time",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("patient", "client_uuid"),
                        name="core_d18_weight_owner_uuid",
                    ),
                ],
            },
        ),
    ]
