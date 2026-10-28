"""Durable non-clinical intent for recovering cross-service account erasure."""
from django.db import models


class ErasureAttempt(models.Model):
    """No FK to User: survives User deletion and SQL rollback after Firebase."""

    class State(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        REVIEW_REQUIRED = "review_required", "Review required"
        COMPLETED = "completed", "Completed"

    patient_id_snapshot = models.IntegerField(unique=True)
    firebase_uid_snapshot = models.CharField(max_length=128, blank=True, default="")
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.PENDING, db_index=True
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        ordering = ["-requested_at"]
