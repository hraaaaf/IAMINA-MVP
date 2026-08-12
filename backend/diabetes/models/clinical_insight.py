"""Diabetes-owned attention lifecycle for governed clinical observations."""

from django.db import models

from diabetes.models.clinical_observation import ClinicalObservationState


class ClinicalInsightState(models.Model):
    """Persisted product-attention state for one governed observation.

    This is not patient truth, a diagnosis, a risk score, or an emergency state.
    It records only deterministic lifecycle/surfacing bookkeeping for the approved
    ``personal_response`` observation producer. Emergency handling remains owned by
    the upstream deterministic safety layer.
    """

    STATE_NEW = "new"
    STATE_MONITORING = "monitoring"
    STATE_PERSISTING = "persisting"
    STATE_IMPROVING = "improving"
    STATE_RESOLVED = "resolved"
    STATE_ESCALATED = "escalated"
    STATE_CHOICES = (
        (STATE_NEW, "New"),
        (STATE_MONITORING, "Monitoring"),
        (STATE_PERSISTING, "Persisting"),
        (STATE_IMPROVING, "Improving toward recorded baseline"),
        (STATE_RESOLVED, "Resolved from proactive attention"),
        (STATE_ESCALATED, "Escalated by governed criterion"),
    )

    ACTION_MONITOR = "monitor"
    ACTION_COLLECT_MISSING_DATA = "collect_missing_data"
    ACTION_CHOICES = (
        (ACTION_MONITOR, "Monitor"),
        (ACTION_COLLECT_MISSING_DATA, "Collect missing data"),
    )

    DETERMINISTIC_TRUTH_KIND = "deterministic_derivation"
    PRODUCER = "diabetes.proactive_attention.v1"
    APPROVED_SOURCE_PRODUCER = "diabetes.personal_response.v1"
    APPROVED_SOURCE_EVIDENCE_ID = "rule.personal-response.repetition.v1"

    observation = models.OneToOneField(
        ClinicalObservationState,
        on_delete=models.CASCADE,
        related_name="proactive_insight_state",
    )
    observation_key = models.CharField(max_length=64)

    truth_kind = models.CharField(
        max_length=32,
        default=DETERMINISTIC_TRUTH_KIND,
        editable=False,
    )
    producer = models.CharField(max_length=96, default=PRODUCER, editable=False)
    source_producer = models.CharField(
        max_length=96,
        default=APPROVED_SOURCE_PRODUCER,
        editable=False,
    )
    source_evidence_id = models.CharField(
        max_length=96,
        default=APPROVED_SOURCE_EVIDENCE_ID,
        editable=False,
    )

    lifecycle_state = models.CharField(max_length=16, choices=STATE_CHOICES, default=STATE_NEW)
    allowed_next_step = models.CharField(
        max_length=32,
        choices=ACTION_CHOICES,
        default=ACTION_MONITOR,
    )

    # Last deterministic source snapshot used to explain what materially changed.
    source_status_snapshot = models.CharField(max_length=16, blank=True, default="")
    recurrence_count_snapshot = models.PositiveIntegerField(default=0)
    evidence_strength_snapshot = models.CharField(max_length=16, blank=True, default="")
    baseline_delta_snapshot_mg_dl = models.FloatField(null=True, blank=True)
    observations_snapshot = models.PositiveIntegerField(default=0)
    distinct_days_snapshot = models.PositiveIntegerField(default=0)
    dataset_eligible_snapshot = models.BooleanField(default=False)

    last_material_fingerprint = models.CharField(max_length=64, blank=True, default="")
    last_decision_fingerprint = models.CharField(max_length=64, blank=True, default="")
    last_surfaced_decision_fingerprint = models.CharField(max_length=64, blank=True, default="")

    first_surfaced_at = models.DateTimeField(null=True, blank=True)
    last_surfaced_at = models.DateTimeField(null=True, blank=True)
    surface_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(truth_kind="deterministic_derivation"),
                name="clinical_insight_truth_deterministic",
            ),
            models.CheckConstraint(
                condition=models.Q(producer="diabetes.proactive_attention.v1"),
                name="clinical_insight_producer_approved",
            ),
            models.CheckConstraint(
                condition=models.Q(source_producer="diabetes.personal_response.v1"),
                name="clinical_insight_source_producer_approved",
            ),
            models.CheckConstraint(
                condition=models.Q(source_evidence_id="rule.personal-response.repetition.v1"),
                name="clinical_insight_source_evidence_approved",
            ),
            models.CheckConstraint(
                condition=~models.Q(lifecycle_state="escalated"),
                name="clinical_insight_no_unruled_escalation",
            ),
            models.CheckConstraint(
                condition=models.Q(allowed_next_step__in=("monitor", "collect_missing_data")),
                name="clinical_insight_safe_action_only",
            ),
        ]
        ordering = ("observation__patient_id", "observation_key")

    def __str__(self) -> str:
        return f"{self.observation.patient_id}:{self.observation_key}:{self.lifecycle_state}"
