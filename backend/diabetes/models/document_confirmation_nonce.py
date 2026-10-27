"""Non-clinical one-time marker for synthetic stateless Pulper confirmations."""
from django.conf import settings
from django.db import models


class DocumentConfirmationNonce(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nonce_digest = models.CharField(max_length=64, unique=True)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "diabetes"
        indexes = [
            models.Index(fields=("patient", "used_at"), name="pulper_nonce_patient_idx")
        ]
