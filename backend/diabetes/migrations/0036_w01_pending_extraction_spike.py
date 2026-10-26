"""W01 synthetic-only PostgreSQL pending document staging candidate.

Schema is inert until the DEBUG-only feature flag is enabled in tests.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0035_diabetesprofile_optional_type_codes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PendingDocumentExtraction",
            fields=[
                ("batch_id", models.UUIDField(primary_key=True, serialize=False)),
                ("payload", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="w01_synthetic_pending_documents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["patient", "expires_at"],
                        name="w01_pending_patient_ttl",
                    )
                ],
            },
        )
    ]
