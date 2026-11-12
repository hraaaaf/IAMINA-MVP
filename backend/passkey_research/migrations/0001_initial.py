"""D1 research-only WebAuthn owner/ceremony tables. Never migrates patient vaults."""
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="D1ResearchPasskeyCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("credential_id", models.CharField(max_length=1024, unique=True)),
                ("public_key", models.BinaryField()),
                ("user_handle", models.BinaryField()),
                ("sign_count", models.PositiveBigIntegerField(default=0)),
                ("rp_id", models.CharField(max_length=255)),
                ("origin", models.URLField(max_length=512)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("patient", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="d1_research_passkeys",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "indexes": [
                    models.Index(fields=["patient", "revoked_at"], name="d1_prf_owner_rev_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="D1ResearchPasskeyChallenge",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("purpose", models.CharField(
                    choices=[("enroll", "Enroll"), ("verify", "Verify")], max_length=16,
                )),
                ("challenge", models.BinaryField()),
                ("user_handle", models.BinaryField()),
                ("origin", models.URLField(max_length=512)),
                ("rp_id", models.CharField(max_length=255)),
                ("auth_token_version", models.PositiveIntegerField()),
                ("session_binding", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("patient", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="d1_research_passkey_challenges",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("credential", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                    to="passkey_research.d1researchpasskeycredential",
                )),
            ],
            options={
                "indexes": [
                    models.Index(fields=["patient", "purpose", "expires_at"], name="d1_prf_chal_owner_idx"),
                ],
            },
        ),
    ]
