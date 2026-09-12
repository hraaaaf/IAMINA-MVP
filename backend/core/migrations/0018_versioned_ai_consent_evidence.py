from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def invalidate_legacy_ai_consent(apps, schema_editor):
    """Legacy timestamps/grants have no exact-notice evidence and must fail closed."""
    BasePatientProfile = apps.get_model("core", "BasePatientProfile")
    AIMediaConsentGrant = apps.get_model("core", "AIMediaConsentGrant")
    BasePatientProfile.objects.filter(ai_consent_given_at__isnull=False).update(
        ai_consent_given_at=None,
        ai_consent_notice_version=None,
        ai_consent_notice_hash=None,
        ai_consent_notice_locale=None,
    )
    AIMediaConsentGrant.objects.filter(revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_finopstelemetryevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="basepatientprofile",
            name="ai_consent_notice_hash",
            field=models.CharField(
                blank=True,
                help_text="SHA-256 fingerprint of the exact rendered patient consent notice.",
                max_length=64,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="basepatientprofile",
            name="ai_consent_notice_locale",
            field=models.CharField(
                blank=True,
                help_text="Locale of the exact patient consent notice accepted.",
                max_length=8,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="basepatientprofile",
            name="ai_consent_notice_version",
            field=models.CharField(
                blank=True,
                help_text="Version of the exact patient notice accepted for AI processing.",
                max_length=32,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="AIConsentReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notice_version", models.CharField(max_length=32)),
                ("notice_hash", models.CharField(max_length=64)),
                ("notice_locale", models.CharField(max_length=8)),
                ("granted_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_consent_receipts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-granted_at", "-id"],
                "indexes": [models.Index(fields=["patient", "revoked_at", "granted_at"], name="core_ai_consent_receipt_lookup")],
            },
        ),
        migrations.RunPython(invalidate_legacy_ai_consent, migrations.RunPython.noop),
    ]
