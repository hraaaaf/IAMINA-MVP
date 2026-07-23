from django.db import models


class ErasureRecord(models.Model):
    """
    RGPD Art. 17 — immutable record of a completed account erasure request.

    Created after all hooks succeed and the Django User is deleted.
    Preserves enough data for compliance audit without storing live PHI.
    """

    patient_id_snapshot = models.IntegerField(
        help_text="PK of the deleted Django User (no FK — user no longer exists).",
    )
    firebase_uid_snapshot = models.CharField(
        max_length=128,
        help_text="Firebase UID at time of erasure.",
    )
    hook_failures = models.JSONField(
        default=list,
        help_text="List of hook error strings if any hooks partially failed.",
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the erasure request was received.",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the erasure was fully completed (set after user.delete()).",
    )

    class Meta:
        app_label = "core"
        ordering = ["-requested_at"]
        verbose_name = "Erasure Record"
        verbose_name_plural = "Erasure Records"

    def __str__(self) -> str:
        return f"ErasureRecord patient={self.patient_id_snapshot} at {self.requested_at}"
