"""CAL-12 test-only medical export consent rehearsal. No production export."""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0020_d2_notification_center"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Cal12ExportConsentFixtureReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("revision", models.PositiveIntegerField()),
                ("notice_version", models.CharField(max_length=48)),
                ("notice_sha256", models.CharField(max_length=64)),
                ("notice_locale", models.CharField(max_length=8)),
                ("purpose", models.CharField(max_length=48)),
                ("data_category", models.CharField(max_length=48)),
                ("recipient_ref", models.CharField(max_length=64)),
                ("channel", models.CharField(max_length=32)),
                ("period_start_utc", models.DateTimeField()),
                ("period_end_utc", models.DateTimeField()),
                ("recipient_confirmed_at", models.DateTimeField()),
                ("granted_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cal12_fixture_export_receipts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-revision",),
                "indexes": [models.Index(fields=("owner", "revoked_at", "expires_at"), name="core_cal12_fixture_active")],
                "constraints": [models.UniqueConstraint(fields=("owner", "revision"), name="core_cal12_fixture_owner_rev_unique")],
            },
        ),
        migrations.CreateModel(
            name="Cal12ExportConsentFixtureEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("granted", "Granted"), ("revoked", "Revoked"), ("superseded", "Superseded")], max_length=16)),
                ("occurred_at", models.DateTimeField()),
                ("receipt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="core.cal12exportconsentfixturereceipt")),
            ],
            options={
                "ordering": ("id",),
                "constraints": [models.UniqueConstraint(fields=("receipt", "kind"), name="core_cal12_fixture_event_once")],
            },
        ),
    ]
