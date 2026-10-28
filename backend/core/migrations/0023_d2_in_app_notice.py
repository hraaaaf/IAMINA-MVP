from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_d2_preview_consent_receipt"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="D2InAppNotice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("signature", models.CharField(max_length=64)),
                ("kind", models.CharField(max_length=12, choices=[("context", "Context"), ("meal", "Meal")])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("patient", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="d2_in_app_notices", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "constraints": [models.UniqueConstraint(
                    fields=("patient", "signature"),
                    name="core_d2_notice_patient_signature_unique",
                )],
                "indexes": [models.Index(
                    fields=("patient", "expires_at", "created_at"),
                    name="core_d2_notice_active_lookup",
                )],
            },
        ),
    ]
