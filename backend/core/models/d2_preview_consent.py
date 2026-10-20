"""D2 patient-owned in-app preview consent receipts. No push authorization."""
from django.conf import settings
from django.db import models


class D2PreviewConsentReceipt(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="d2_preview_consent_receipts",
    )
    notice_version = models.CharField(max_length=32)
    notice_hash = models.CharField(max_length=64)
    notice_locale = models.CharField(max_length=8)
    global_consent_epoch = models.DateTimeField()
    granted_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        ordering = ("-granted_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("patient",), condition=models.Q(revoked_at__isnull=True),
                name="core_d2_one_active_receipt",
            ),
        ]
        indexes = [
            models.Index(
                fields=("patient", "revoked_at", "granted_at"),
                name="core_d2_consent_lookup",
            ),
        ]
