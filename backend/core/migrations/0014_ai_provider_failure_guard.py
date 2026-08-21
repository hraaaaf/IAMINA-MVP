# Generated manually for FRUG-8C persistent provider failure guard.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_ai_budget_ledger"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIProviderCircuitState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("provider", models.CharField(max_length=64, unique=True)),
                ("consecutive_failures", models.PositiveIntegerField(default=0)),
                ("opened_until", models.DateTimeField(blank=True, null=True)),
                (
                    "probe_in_flight_until",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("last_error_code", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "core_ai_provider_circuit",
            },
        ),
        migrations.CreateModel(
            name="AIProviderOperationAttempt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("provider", models.CharField(max_length=64)),
                ("operation_key", models.CharField(max_length=72)),
                ("attempt_count", models.PositiveIntegerField(default=0)),
                (
                    "active_attempt_number",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("in_flight_until", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("last_error_code", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "core_ai_provider_operation",
            },
        ),
        migrations.AddConstraint(
            model_name="aiprovideroperationattempt",
            constraint=models.UniqueConstraint(
                fields=("provider", "operation_key"),
                name="uniq_ai_provider_operation_key",
            ),
        ),
    ]
