# Generated for CGM-GW-V2 product wiring.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0026_companionreviewanchor_and_snapshot"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CGMConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("dexcom", "Dexcom"), ("libre", "FreeStyle Libre"), ("linx", "LinX")], max_length=16)),
                ("base_url", models.URLField(max_length=500)),
                ("auth_type", models.CharField(choices=[("bearer", "Bearer token"), ("api_secret", "Nightscout API secret")], max_length=16)),
                ("encrypted_credential", models.TextField()),
                ("enabled", models.BooleanField(default=True)),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                ("last_success_at", models.DateTimeField(blank=True, null=True)),
                ("last_error_code", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="cgm_connection", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CGMReadingRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("dexcom", "Dexcom"), ("libre", "FreeStyle Libre"), ("linx", "LinX")], max_length=16)),
                ("recorded_at", models.DateTimeField()),
                ("glucose_mg_dl", models.PositiveIntegerField()),
                ("trend", models.CharField(blank=True, default="", max_length=64)),
                ("device", models.CharField(blank=True, default="", max_length=255)),
                ("dedupe_key", models.CharField(max_length=64)),
                ("imported_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cgm_readings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-recorded_at"]},
        ),
        migrations.AddIndex(
            model_name="cgmconnection",
            index=models.Index(fields=["source", "enabled"], name="cgm_conn_source_enabled"),
        ),
        migrations.AddConstraint(
            model_name="cgmreadingrecord",
            constraint=models.UniqueConstraint(fields=("patient", "source", "dedupe_key"), name="uniq_cgm_reading_patient_source_key"),
        ),
        migrations.AddIndex(
            model_name="cgmreadingrecord",
            index=models.Index(fields=["patient", "recorded_at"], name="cgm_patient_recorded_idx"),
        ),
        migrations.AddIndex(
            model_name="cgmreadingrecord",
            index=models.Index(fields=["patient", "source", "recorded_at"], name="cgm_patient_source_time_idx"),
        ),
    ]
