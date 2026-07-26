from django.contrib.auth.models import User
from django.db import models


class AIMediaConsentGrant(models.Model):
    RAW_MEDIA_MODALITIES = (
        ("audio", "Audio"),
        ("image", "Image"),
        ("document", "Document"),
    )

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ai_media_consent_grants",
    )
    purpose = models.CharField(max_length=64)
    modality = models.CharField(max_length=16, choices=RAW_MEDIA_MODALITIES)
    granted_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        constraints = [
            models.UniqueConstraint(
                fields=("patient", "purpose", "modality"),
                name="core_unique_ai_media_consent_grant",
            ),
        ]
        indexes = [
            models.Index(
                fields=("patient", "purpose", "modality", "revoked_at"),
                name="core_ai_media_consent_lookup",
            ),
        ]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
