"""Durable diabetes-owned lifecycle for deterministic clinical observations."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class ClinicalObservationState(models.Model):
    """Persisted lifecycle of an approved deterministic observation.

    This model is deliberately not a diagnosis/problem list. Rows may be active or
    inactive only, and the database accepts deterministic-derivation provenance only.
    """

    KIND_CONTEXT = "context"
    KIND_MEAL = "meal"
    KIND_CHOICES = (
        (KIND_CONTEXT, "Recorded context association"),
        (KIND_MEAL, "Recorded post-meal association"),
    )

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

    TREND_INITIAL = "initial"
    TREND_STABLE = "stable"
    TREND_STRENGTHENING = "strengthening"
    TREND_WEAKENING = "weakening"
    EVIDENCE_TREND_CHOICES = (
        (TREND_INITIAL, "Initial evidence grade"),
        (TREND_STABLE, "Stable evidence grade"),
        (TREND_STRENGTHENING, "Strengthening repeatability"),
        (TREND_WEAKENING, "Weakening repeatability"),
    )

    DETERMINISTIC_TRUTH_KIND = "deterministic_derivation"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clinical_observation_states",
    )
    observation_key = models.CharField(max_length=64)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    truth_kind = models.CharField(
        max_length=32,
        default=DETERMINISTIC_TRUTH_KIND,
        editable=False,
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    status_changed_at = models.DateTimeField(default=timezone.now)
    recurrence_count = models.PositiveIntegerField(default=1)

    evidence_strength = models.CharField(max_length=16, choices=EVIDENCE_STRENGTH_CHOICES)
    previous_evidence_strength = models.CharField(max_length=16, blank=True, default="")
    evidence_strength_trend = models.CharField(
        max_length=16,
        choices=EVIDENCE_TREND_CHOICES,
        default=TREND_INITIAL,
    )
    observations = models.PositiveIntegerField()
    distinct_days = models.PositiveIntegerField()

    observation_median_glucose_mg_dl = models.FloatField()
    window_median_glucose_mg_dl = models.FloatField()
    baseline_delta_mg_dl = models.FloatField()
    previous_baseline_delta_mg_dl = models.FloatField(null=True, blank=True)
    baseline_delta_change_mg_dl = models.FloatField(null=True, blank=True)

    evidence_window_days = models.PositiveSmallIntegerField(default=90)
    evidence_id = models.CharField(max_length=96)
    producer = models.CharField(max_length=96)
    context_modifiers = models.JSONField(default=dict)
    last_evidence_fingerprint = models.CharField(max_length=64)

    created_at = models.DateTimeField(auto_now_add=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("patient", "observation_key"),
                name="uniq_patient_clinical_observation_key",
            ),
            models.CheckConstraint(
                condition=models.Q(truth_kind="deterministic_derivation"),
                name="clinical_obs_truth_deterministic",
            ),
        ]
        ordering = ("patient_id", "observation_key")

    def __str__(self) -> str:
        return f"{self.patient_id}:{self.observation_key}:{self.status}"
