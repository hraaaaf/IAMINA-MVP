# Generated manually for FRUG-8A persistent FinOps ledger.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_alter_basepatientprofile_firebase_uid"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIBudgetAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject_key", models.CharField(max_length=160)),
                ("month_key", models.CharField(max_length=7)),
                ("committed_microusd", models.BigIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "core_ai_budget_account",
            },
        ),
        migrations.CreateModel(
            name="AIBudgetReservationRecord",
            fields=[
                ("reservation_id", models.CharField(max_length=32, primary_key=True, serialize=False)),
                ("idempotency_key", models.CharField(blank=True, max_length=160, null=True)),
                ("reserved_microusd", models.BigIntegerField()),
                ("settled_microusd", models.BigIntegerField(blank=True, null=True)),
                ("cancelled", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservations",
                        to="core.aibudgetaccount",
                    ),
                ),
            ],
            options={
                "db_table": "core_ai_budget_reservation",
            },
        ),
        migrations.AddConstraint(
            model_name="aibudgetaccount",
            constraint=models.UniqueConstraint(
                fields=("subject_key", "month_key"),
                name="uniq_ai_budget_subject_month",
            ),
        ),
        migrations.AddConstraint(
            model_name="aibudgetreservationrecord",
            constraint=models.UniqueConstraint(
                fields=("account", "idempotency_key"),
                name="uniq_ai_budget_account_idempotency",
            ),
        ),
    ]
