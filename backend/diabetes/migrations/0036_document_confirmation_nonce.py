"""Synthetic stateless Pulper: one-time confirmation registry, no document data."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0035_diabetesprofile_optional_type_codes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentConfirmationNonce",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nonce_digest", models.CharField(max_length=64, unique=True)),
                ("used_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=("patient", "used_at"), name="pulper_nonce_patient_idx")
                ]
            },
        ),
    ]
