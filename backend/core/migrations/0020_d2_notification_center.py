"""D2 account-owned event inbox and explicit proactivity preference, no clinical fields."""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_auth_abuse_bucket"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="D2NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("proactive_opt_in", models.BooleanField(default=False)),
                ("notice_version", models.CharField(blank=True, default="", max_length=48)),
                ("notice_digest", models.CharField(blank=True, default="", max_length=64)),
                ("granted_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="d2_notification_preference", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="D2Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_key", models.CharField(max_length=64)),
                ("kind", models.CharField(choices=[("event", "Event"), ("proactive", "Proactive")], max_length=12)),
                ("code", models.CharField(choices=[("ai_consent_given", "AI consent confirmed"), ("ai_consent_withdrawn", "AI consent withdrawn"), ("language_pref_available", "Language preference available")], max_length=48)),
                ("created_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField()),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="d2_notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [models.Index(fields=["patient", "expires_at", "created_at"], name="core_d2_notice_owner_active")],
                "constraints": [models.UniqueConstraint(fields=("patient", "event_key"), name="core_d2_notice_event_key_unique")],
            },
        ),
    ]
