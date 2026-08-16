from __future__ import annotations

from django.conf import settings
from django.db import models


class CGMConnection(models.Model):
    """One patient-scoped CGM transport connection.

    The encrypted credential is transport-only secret material. It is never
    returned by patient APIs and grants no clinical authority.
    """

    class Source(models.TextChoices):
        DEXCOM = "dexcom", "Dexcom"
        LIBRE = "libre", "FreeStyle Libre"
        LINX = "linx", "LinX"

    class AuthType(models.TextChoices):
        BEARER = "bearer", "Bearer token"
        API_SECRET = "api_secret", "Nightscout API secret"

    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cgm_connection",
    )
    source = models.CharField(max_length=16, choices=Source.choices)
    base_url = models.URLField(max_length=500)
    auth_type = models.CharField(max_length=16, choices=AuthType.choices)
    encrypted_credential = models.TextField()
    enabled = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["source", "enabled"], name="cgm_conn_source_enabled")]


class CGMReadingRecord(models.Model):
    """Normalized recorded CGM transport fact, isolated from manual LogEntry."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cgm_readings",
    )
    source = models.CharField(max_length=16, choices=CGMConnection.Source.choices)
    recorded_at = models.DateTimeField()
    glucose_mg_dl = models.PositiveIntegerField()
    trend = models.CharField(max_length=64, blank=True, default="")
    device = models.CharField(max_length=255, blank=True, default="")
    dedupe_key = models.CharField(max_length=64)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "source", "dedupe_key"],
                name="uniq_cgm_reading_patient_source_key",
            )
        ]
        indexes = [
            models.Index(fields=["patient", "recorded_at"], name="cgm_patient_recorded_idx"),
            models.Index(fields=["patient", "source", "recorded_at"], name="cgm_patient_source_time_idx"),
        ]
        ordering = ["-recorded_at"]
