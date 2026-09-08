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


class CGMSensorSession(models.Model):
    """Pseudonymized sensor activity interval used to prove CGM coverage.

    ``session_key`` is an opaque provider/session identifier and must not contain
    a serial number, patient name, email, phone number or other direct identifier.
    A session describes when readings were expected. Missing readings inside that
    interval are data gaps; time outside all sessions is sensor-off time.
    """

    class EndReason(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        REMOVED = "removed", "Removed"
        REPLACED = "replaced", "Replaced"
        DISCONNECTED = "disconnected", "Disconnected"
        UNKNOWN = "unknown", "Unknown"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cgm_sensor_sessions",
    )
    source = models.CharField(max_length=16, choices=CGMConnection.Source.choices)
    session_key = models.CharField(max_length=64)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    expected_interval_minutes = models.PositiveSmallIntegerField()
    timezone_name = models.CharField(max_length=64, default="UTC")
    end_reason = models.CharField(
        max_length=16,
        choices=EndReason.choices,
        default=EndReason.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "source", "session_key"],
                name="uniq_cgm_session_patient_source_key",
            ),
            models.CheckConstraint(
                condition=models.Q(expected_interval_minutes__gte=1)
                & models.Q(expected_interval_minutes__lte=60),
                name="cgm_session_interval_1_60_min",
            ),
            models.CheckConstraint(
                condition=models.Q(ended_at__isnull=True) | models.Q(ended_at__gt=models.F("started_at")),
                name="cgm_session_end_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["patient", "started_at"], name="cgm_session_patient_start"),
            models.Index(fields=["patient", "source", "started_at"], name="cgm_session_source_start"),
        ]
        ordering = ["-started_at"]


class CGMReadingRecord(models.Model):
    """Normalized recorded CGM transport fact, isolated from manual LogEntry."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cgm_readings",
    )
    source = models.CharField(max_length=16, choices=CGMConnection.Source.choices)
    session = models.ForeignKey(
        CGMSensorSession,
        on_delete=models.SET_NULL,
        related_name="readings",
        null=True,
        blank=True,
    )
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
            models.Index(fields=["session", "recorded_at"], name="cgm_session_recorded_idx"),
        ]
        ordering = ["-recorded_at"]
