from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0026_companionreviewanchor_and_snapshot"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AfterVisitAnchor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("occurred_at", models.DateTimeField()),
                ("source", models.CharField(choices=[("after-visit.patient-recorded.v1", "Patient-recorded consultation"), ("after-visit.clinician-recorded.v1", "Clinician-recorded consultation")], max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="after_visit_anchors", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-occurred_at", "-id")},
        ),
        migrations.CreateModel(
            name="AfterVisitFactRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=96)),
                ("value", models.JSONField()),
                ("fact_kind", models.CharField(choices=[("patient_recorded", "Patient recorded"), ("clinician_recorded", "Clinician recorded"), ("governed_derivation", "Governed derivation")], max_length=32)),
                ("source", models.CharField(max_length=96)),
                ("recorded_at", models.DateTimeField()),
                ("evidence_id", models.CharField(blank=True, default="", max_length=96)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("anchor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="facts", to="diabetes.aftervisitanchor")),
            ],
            options={"ordering": ("recorded_at", "id")},
        ),
        migrations.AddIndex(
            model_name="aftervisitanchor",
            index=models.Index(fields=["patient", "-occurred_at"], name="after_visit_patient_latest_idx"),
        ),
        migrations.AddConstraint(
            model_name="aftervisitanchor",
            constraint=models.CheckConstraint(condition=models.Q(("source__in", ("after-visit.patient-recorded.v1", "after-visit.clinician-recorded.v1"))), name="after_visit_anchor_source_safe"),
        ),
        migrations.AddConstraint(
            model_name="aftervisitfactrecord",
            constraint=models.CheckConstraint(condition=models.Q(("fact_kind__in", ("patient_recorded", "clinician_recorded", "governed_derivation"))), name="after_visit_fact_kind_safe"),
        ),
        migrations.AddConstraint(
            model_name="aftervisitfactrecord",
            constraint=models.CheckConstraint(condition=models.Q(("fact_kind", "governed_derivation"), _negated=True) | models.Q(("evidence_id", ""), _negated=True), name="after_visit_governed_evidence_required"),
        ),
    ]
