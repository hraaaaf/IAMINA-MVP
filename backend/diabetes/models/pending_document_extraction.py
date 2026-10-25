"""Experimental database-backed Pulper review staging (synthetic only)."""
from django.conf import settings
from django.db import models


class PendingDocumentExtraction(models.Model):
    batch_id = models.UUIDField(primary_key=True, serialize=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="w01_synthetic_pending_documents",
    )
    # Clinical fields remain sensitive even when the original raw text is excluded.
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [models.Index(fields=["patient", "expires_at"], name="w01_pending_patient_ttl")]

