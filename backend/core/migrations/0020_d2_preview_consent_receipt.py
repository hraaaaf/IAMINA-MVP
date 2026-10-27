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
            name="D2PreviewConsentReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notice_version", models.CharField(max_length=32)),
                ("notice_hash", models.CharField(max_length=64)),
                ("notice_locale", models.CharField(max_length=8)),
                ("global_consent_epoch", models.DateTimeField()),
                ("granted_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="d2_preview_consent_receipts",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ("-granted_at", "-id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("patient",), condition=models.Q(revoked_at__isnull=True),
                        name="core_d2_one_active_receipt",
                    ),
                ],
                "indexes": [
                    models.Index(
                        fields=("patient", "revoked_at", "granted_at"),
                        name="core_d2_consent_lookup",
                    ),
                ],
            },
        ),
    ]
