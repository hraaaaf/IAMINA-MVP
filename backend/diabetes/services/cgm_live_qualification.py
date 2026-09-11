"""Fail-closed live CGM bridge qualification without exposing clinical values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from diabetes.models.cgm import CGMConnection, CGMReadingRecord
from diabetes.services.cgm_sync import CGMSyncError, sync_patient_cgm


class LiveCGMQualificationError(RuntimeError):
    """Stable qualification failure safe to expose in engineering evidence."""


@dataclass(frozen=True, slots=True)
class LiveCGMQualificationResult:
    source: str
    provider_received: int
    provider_inserted: int
    fresh_persisted_readings: int
    newest_reading_age_seconds: int
    max_age_minutes: int
    minimum_readings: int

    def as_payload(self) -> dict[str, object]:
        return {
            "status": "PASS",
            "scope": "authorized_non_patient_physical_sensor",
            "source": self.source,
            "provider_received": self.provider_received,
            "provider_inserted": self.provider_inserted,
            "fresh_persisted_readings": self.fresh_persisted_readings,
            "newest_reading_age_seconds": self.newest_reading_age_seconds,
            "max_age_minutes": self.max_age_minutes,
            "minimum_readings": self.minimum_readings,
            "physical_sensor_attested": True,
            "contains_glucose_values": False,
            "contains_credentials": False,
        }


def qualify_live_cgm(
    *,
    patient_id: int,
    expected_source: str,
    max_age_minutes: int = 15,
    minimum_readings: int = 2,
    authorized_non_patient_test_subject: bool = False,
    physical_sensor_attested: bool = False,
) -> LiveCGMQualificationResult:
    """Exercise the real provider path and retain only non-clinical proof metadata.

    This gate is deliberately stricter than the synthetic E2E tests. It requires
    explicit operator attestations, a live provider fetch, and recent persisted
    readings from the configured source. It never returns glucose values, bridge
    URLs, credentials, patient identifiers, or device identifiers.
    """

    if not authorized_non_patient_test_subject:
        raise LiveCGMQualificationError(
            "authorized_non_patient_test_subject_confirmation_required"
        )
    if not physical_sensor_attested:
        raise LiveCGMQualificationError("physical_sensor_confirmation_required")
    if expected_source not in {"dexcom", "libre", "linx"}:
        raise LiveCGMQualificationError("cgm_source_unqualified")
    if not 1 <= max_age_minutes <= 120:
        raise LiveCGMQualificationError("max_age_minutes_out_of_range")
    if not 1 <= minimum_readings <= 100:
        raise LiveCGMQualificationError("minimum_readings_out_of_range")

    connection = CGMConnection.objects.filter(
        patient_id=patient_id,
        enabled=True,
    ).first()
    if connection is None:
        raise LiveCGMQualificationError("cgm_connection_unavailable")
    if connection.source != expected_source:
        raise LiveCGMQualificationError("cgm_source_mismatch")

    try:
        sync_result = sync_patient_cgm(patient_id=patient_id)
    except CGMSyncError as exc:
        raise LiveCGMQualificationError(f"cgm_sync_failed:{exc}") from exc

    observed_at = timezone.now()
    cutoff = observed_at - timedelta(minutes=max_age_minutes)
    recent = CGMReadingRecord.objects.filter(
        patient_id=patient_id,
        source=expected_source,
        recorded_at__gte=cutoff,
    )
    fresh_count = recent.count()
    newest = recent.order_by("-recorded_at").values_list("recorded_at", flat=True).first()

    if sync_result.received < minimum_readings:
        raise LiveCGMQualificationError("provider_readings_below_minimum")
    if fresh_count < minimum_readings:
        raise LiveCGMQualificationError("fresh_persisted_readings_below_minimum")
    if newest is None:
        raise LiveCGMQualificationError("fresh_cgm_reading_unavailable")
    if newest > observed_at + timedelta(minutes=5):
        raise LiveCGMQualificationError("fresh_cgm_reading_timestamp_in_future")

    newest_age_seconds = max(0, int((observed_at - newest).total_seconds()))
    if newest_age_seconds > max_age_minutes * 60:
        raise LiveCGMQualificationError("fresh_cgm_reading_too_old")

    return LiveCGMQualificationResult(
        source=expected_source,
        provider_received=sync_result.received,
        provider_inserted=sync_result.inserted,
        fresh_persisted_readings=fresh_count,
        newest_reading_age_seconds=newest_age_seconds,
        max_age_minutes=max_age_minutes,
        minimum_readings=minimum_readings,
    )
