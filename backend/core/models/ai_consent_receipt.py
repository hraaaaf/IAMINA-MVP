from django.contrib.auth.models import User
from django.db import models


class AIConsentReceipt(models.Model):
    """Append-only evidence of one explicit acceptance of an exact AI notice."""

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ai_consent_receipts",
    )
    notice_version = models.CharField(max_length=32)
    notice_hash = models.CharField(max_length=64)
    notice_locale = models.CharField(max_length=8)
    granted_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        ordering = ["-granted_at", "-id"]
        indexes = [
            models.Index(
                fields=("patient", "revoked_at", "granted_at"),
                name="core_ai_consent_receipt_lookup",
            ),
        ]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
