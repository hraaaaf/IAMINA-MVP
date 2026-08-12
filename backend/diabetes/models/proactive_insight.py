"""Persistence for deterministic proactive insight workflow state."""

from django.db import models


class ProactiveInsightState(models.Model):
    """Derived product-state for one approved clinical observation.

    The source observation remains the clinical truth. This row stores only
    proactive workflow state and delivery bookkeeping.
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
        (STATE_IMPROVING, "Improving"),
        (STATE_RESOLVED, "Resolved"),
        (STATE_ESCALATED, "Escalated"),
    )

    RELEVANCE_OBSERVATIONAL = "observational"
    RELEVANCE_REVIEW_WORTHY = "review_worthy"
    RELEVANCE_CHOICES = (
        (RELEVANCE_OBSERVATIONAL, "Observational"),
        (RELEVANCE_REVIEW_WORTHY, "Review worthy"),
    )

    ACTION_MONITOR = "MONITOR"
    ACTION_PREPARE_CLINICIAN_DISCUSSION = "PREPARE_CLINICIAN_DISCUSSION"
    ACTION_CHOICES = (
        (ACTION_MONITOR, "Monitor"),
        (ACTION_PREPARE_CLINICIAN_DISCUSSION, "Prepare clinician discussion"),
    )

    ESCALATION_NONE = "none"

    observation = models.OneToOneField(
        "diabetes.ClinicalObservationState",
        on_delete=models.CASCADE,
        related_name="proactive_insight",
    )
    state = models.CharField(max_length=16, choices=STATE_CHOICES)
    clinical_relevance = models.CharField(max_length=24, choices=RELEVANCE_CHOICES)
    action_class = models.CharField(max_length=40, choices=ACTION_CHOICES)
    escalation_class = models.CharField(
        max_length=24,
        default=ESCALATION_NONE,
        editable=False,
    )

    last_observation_fingerprint = models.CharField(max_length=64)
    current_signature = models.CharField(max_length=64)
    last_delivered_signature = models.CharField(max_length=64, blank=True, default="")
    last_surfaced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    state__in=(
                        "new",
                        "monitoring",
                        "persisting",
                        "improving",
                        "resolved",
                    )
                ),
                name="proactive_personal_response_state_safe",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    clinical_relevance__in=("observational", "review_worthy")
                ),
                name="proactive_personal_response_relevance_safe",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    action_class__in=("MONITOR", "PREPARE_CLINICIAN_DISCUSSION")
                ),
                name="proactive_personal_response_action_safe",
            ),
            models.CheckConstraint(
                condition=models.Q(escalation_class="none"),
                name="proactive_personal_response_no_escalation",
            ),
        ]
        indexes = [
            models.Index(fields=("last_surfaced_at",), name="proactive_last_surface_idx"),
        ]
        ordering = ("observation_id",)

    def __str__(self) -> str:
        return f"{self.observation_id}:{self.state}:{self.action_class}"
