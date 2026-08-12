"""Persisted companion review anchors for deterministic longitudinal comparison.

These rows are product workflow state, not clinician-authored medical records. An
anchor records what governed Clinical Twin observations existed when the patient
explicitly reviewed their companion state so later code can compare current truth
against that immutable checkpoint without inventing history from app activity.
"""

from django.conf import settings
from django.db import models


class CompanionReviewAnchor(models.Model):
    """Server-captured checkpoint for an explicit IAmina companion review."""

    SOURCE_EXPLICIT_REVIEW = "companion.explicit-review.v1"
    SNAPSHOT_VERSION = "clinical-observation-snapshot.v1"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="companion_review_anchors",
    )
    source = models.CharField(
        max_length=64,
        default=SOURCE_EXPLICIT_REVIEW,
        editable=False,
    )
    snapshot_version = models.CharField(
        max_length=64,
        default=SNAPSHOT_VERSION,
        editable=False,
    )
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(source="companion.explicit-review.v1"),
                name="comp_review_anchor_source_safe",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    snapshot_version="clinical-observation-snapshot.v1"
                ),
                name="comp_review_anchor_version_safe",
            ),
        ]
        indexes = [
            models.Index(
                fields=("patient", "-captured_at"),
                name="comp_review_patient_latest_idx",
            ),
        ]
        ordering = ("-captured_at", "-id")

    def __str__(self) -> str:
        return f"{self.patient_id}:{self.captured_at.isoformat()}"


class CompanionReviewObservationSnapshot(models.Model):
    """Minimal immutable copy of one governed observation at anchor capture time."""

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active observation"),
        (STATUS_INACTIVE, "Inactive observation"),
    )

    EVIDENCE_LIMITED = "limited"
    EVIDENCE_MODERATE = "moderate"
    EVIDENCE_STRONG = "strong"
    EVIDENCE_STRENGTH_CHOICES = (
        (EVIDENCE_LIMITED, "Limited repeatability"),
        (EVIDENCE_MODERATE, "Moderate repeatability"),
        (EVIDENCE_STRONG, "Strong repeatability"),
    )

    DETERMINISTIC_TRUTH_KIND = "deterministic_derivation"
    APPROVED_PRODUCER = "diabetes.personal_response.v1"
    APPROVED_EVIDENCE_ID = "rule.personal-response.repetition.v1"

    anchor = models.ForeignKey(
        CompanionReviewAnchor,
        on_delete=models.CASCADE,
        related_name="observation_snapshots",
    )
    observation_key = models.CharField(max_length=64)
    truth_kind = models.CharField(
        max_length=32,
        default=DETERMINISTIC_TRUTH_KIND,
        editable=False,
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)

    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    status_changed_at = models.DateTimeField()
    last_refreshed_at = models.DateTimeField()
    recurrence_count = models.PositiveIntegerField()

    evidence_strength = models.CharField(
        max_length=16,
        choices=EVIDENCE_STRENGTH_CHOICES,
    )
    baseline_delta_mg_dl = models.FloatField()
    observation_median_glucose_mg_dl = models.FloatField()
    window_median_glucose_mg_dl = models.FloatField()
    evidence_window_days = models.PositiveSmallIntegerField()

    evidence_id = models.CharField(max_length=96)
    producer = models.CharField(max_length=96)
    evidence_fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("anchor", "observation_key"),
                name="uniq_comp_review_anchor_observation",
            ),
            models.CheckConstraint(
                condition=models.Q(truth_kind="deterministic_derivation"),
                name="comp_review_snapshot_truth_safe",
            ),
            models.CheckConstraint(
                condition=models.Q(producer="diabetes.personal_response.v1"),
                name="comp_review_snapshot_producer_safe",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    evidence_id="rule.personal-response.repetition.v1"
                ),
                name="comp_review_snapshot_evidence_safe",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=("active", "inactive")),
                name="comp_review_snapshot_status_safe",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    evidence_strength__in=("limited", "moderate", "strong")
                ),
                name="comp_review_snapshot_density_safe",
            ),
        ]
        ordering = ("anchor_id", "observation_key")

    def __str__(self) -> str:
        return f"{self.anchor_id}:{self.observation_key}:{self.status}"
