"""Persisted P2-COMPANION-6 after-visit continuity facts.

Rows in this module are explicit workflow records. They must never be inferred
from glucose logs, app activity, current treatment profile, or model output.
"""

from django.conf import settings
from django.db import models


class AfterVisitAnchor(models.Model):
    """Explicitly recorded consultation occurrence for continuity tracking."""

    SOURCE_PATIENT_RECORDED = "after-visit.patient-recorded.v1"
    SOURCE_CLINICIAN_RECORDED = "after-visit.clinician-recorded.v1"
    SOURCE_CHOICES = (
        (SOURCE_PATIENT_RECORDED, "Patient-recorded consultation"),
        (SOURCE_CLINICIAN_RECORDED, "Clinician-recorded consultation"),
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="after_visit_anchors",
    )
    occurred_at = models.DateTimeField()
    source = models.CharField(max_length=64, choices=SOURCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=("patient", "-occurred_at"),
                name="after_visit_patient_latest_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    source__in=(
                        "after-visit.patient-recorded.v1",
                        "after-visit.clinician-recorded.v1",
                    )
                ),
                name="after_visit_anchor_source_safe",
            ),
        ]
        ordering = ("-occurred_at", "-id")


class AfterVisitFactRecord(models.Model):
    """One structured fact attached to an explicit consultation anchor."""

    KIND_PATIENT = "patient_recorded"
    KIND_CLINICIAN = "clinician_recorded"
    KIND_GOVERNED = "governed_derivation"
    KIND_CHOICES = (
        (KIND_PATIENT, "Patient recorded"),
        (KIND_CLINICIAN, "Clinician recorded"),
        (KIND_GOVERNED, "Governed derivation"),
    )

    anchor = models.ForeignKey(
        AfterVisitAnchor,
        on_delete=models.CASCADE,
        related_name="facts",
    )
    key = models.CharField(max_length=96)
    value = models.JSONField()
    fact_kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    source = models.CharField(max_length=96)
    recorded_at = models.DateTimeField()
    evidence_id = models.CharField(max_length=96, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("recorded_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    fact_kind__in=(
                        "patient_recorded",
                        "clinician_recorded",
                        "governed_derivation",
                    )
                ),
                name="after_visit_fact_kind_safe",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(fact_kind="governed_derivation")
                    | ~models.Q(evidence_id="")
                ),
                name="after_visit_governed_evidence_required",
            ),
        ]
