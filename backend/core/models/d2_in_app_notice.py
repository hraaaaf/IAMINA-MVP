"""Short-lived, consent-owned, explicitly saved in-app observations.

No automatic notification is emitted: each row requires a patient's explicit
save action. No raw clinical value, generated advice or medical text is stored.
"""
from django.conf import settings
from django.db import models


class D2InAppNotice(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="d2_in_app_notices",
    )
    signature = models.CharField(max_length=64)
    kind = models.CharField(
        max_length=12, choices=[("context", "Context"), ("meal", "Meal")],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("patient", "signature"),
                name="core_d2_notice_patient_signature_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=("patient", "expires_at", "created_at"),
                name="core_d2_notice_active_lookup",
            ),
        ]
