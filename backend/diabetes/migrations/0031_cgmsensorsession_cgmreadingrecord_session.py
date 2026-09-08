# Generated for ANALYSIS-4 real CGM sufficiency contract.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("diabetes", "0030_labreport_source_sha256"),
    ]

    operations = [
        migrations.CreateModel(
            name="CGMSensorSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("dexcom", "Dexcom"), ("libre", "FreeStyle Libre"), ("linx", "LinX")], max_length=16)),
                ("session_key", models.CharField(max_length=64)),
                ("started_at", models.DateTimeField()),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("expected_interval_minutes", models.PositiveSmallIntegerField()),
                ("timezone_name", models.CharField(default="UTC", max_length=64)),
                ("end_reason", models.CharField(choices=[("active", "Active"), ("expired", "Expired"), ("removed", "Removed"), ("replaced", "Replaced"), ("disconnected", "Disconnected"), ("unknown", "Unknown")], default="active", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cgm_sensor_sessions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-started_at"]},
        ),
        migrations.AddField(
            model_name="cgmreadingrecord",
            name="session",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="readings", to="diabetes.cgmsensorsession"),
        ),
        migrations.AddConstraint(
            model_name="cgmsensorsession",
            constraint=models.UniqueConstraint(fields=("patient", "source", "session_key"), name="uniq_cgm_session_patient_source_key"),
        ),
        migrations.AddConstraint(
            model_name="cgmsensorsession",
            constraint=models.CheckConstraint(condition=models.Q(("expected_interval_minutes__gte", 1), ("expected_interval_minutes__lte", 60)), name="cgm_session_interval_1_60_min"),
        ),
        migrations.AddConstraint(
            model_name="cgmsensorsession",
            constraint=models.CheckConstraint(condition=models.Q(("ended_at__isnull", True), ("ended_at__gt", models.F("started_at")), _connector="OR"), name="cgm_session_end_after_start"),
        ),
        migrations.AddIndex(
            model_name="cgmsensorsession",
            index=models.Index(fields=["patient", "started_at"], name="cgm_session_patient_start"),
        ),
        migrations.AddIndex(
            model_name="cgmsensorsession",
            index=models.Index(fields=["patient", "source", "started_at"], name="cgm_session_source_start"),
        ),
        migrations.AddIndex(
            model_name="cgmreadingrecord",
            index=models.Index(fields=["session", "recorded_at"], name="cgm_session_recorded_idx"),
        ),
    ]
