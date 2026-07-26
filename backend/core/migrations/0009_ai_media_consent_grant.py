from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_p0_auth_profile_nullable_facts"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AIMediaConsentGrant",
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
                ("purpose", models.CharField(max_length=64)),
                (
                    "modality",
                    models.CharField(
                        choices=[
                            ("audio", "Audio"),
                            ("image", "Image"),
                            ("document", "Document"),
                        ],
                        max_length=16,
                    ),
                ),
                ("granted_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_media_consent_grants",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["patient", "purpose", "modality", "revoked_at"],
                        name="core_ai_media_consent_lookup",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("patient", "purpose", "modality"),
                        name="core_unique_ai_media_consent_grant",
                    )
                ],
            },
        ),
    ]
