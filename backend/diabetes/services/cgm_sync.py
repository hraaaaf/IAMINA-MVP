from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from diabetes.models.cgm import CGMConnection, CGMReadingRecord
from integrations.cgm import CGMSource, NightscoutCGMProvider, NightscoutConfig
from integrations.cgm.nightscout import CGMProviderError

from .cgm_credentials import CGMCredentialError, decrypt_cgm_credential


class CGMSyncError(RuntimeError):
    """Stable patient-safe CGM sync error."""


@dataclass(frozen=True, slots=True)
class CGMSyncResult:
    received: int
    inserted: int
    last_recorded_at: object | None


def _source(value: str) -> CGMSource:
    try:
        return CGMSource(value)
    except ValueError as exc:
        raise CGMSyncError("cgm_source_unqualified") from exc


def _provider(connection: CGMConnection) -> NightscoutCGMProvider:
    credential = decrypt_cgm_credential(connection.encrypted_credential)
    kwargs: dict[str, str] = {}
    if connection.auth_type == CGMConnection.AuthType.BEARER:
        kwargs["bearer_token"] = credential
    elif connection.auth_type == CGMConnection.AuthType.API_SECRET:
        kwargs["api_secret_sha1"] = credential
    else:
        raise CGMSyncError("cgm_auth_unqualified")

    try:
        config = NightscoutConfig(
            base_url=connection.base_url,
            source=_source(connection.source),
            **kwargs,
        )
    except ValueError as exc:
        raise CGMSyncError("cgm_connection_invalid") from exc
    return NightscoutCGMProvider(config)


def _dedupe_key(*, source: str, recorded_at, glucose_mg_dl: int, trend: str, device: str) -> str:
    canonical = "|".join(
        [
            source,
            recorded_at.isoformat(),
            str(glucose_mg_dl),
            trend,
            device,
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sync_patient_cgm(*, patient_id: int) -> CGMSyncResult:
    now = timezone.now()
    try:
        with transaction.atomic():
            connection = (
                CGMConnection.objects.select_for_update()
                .select_related("patient")
                .get(patient_id=patient_id, enabled=True)
            )

            # Re-read a short overlap to make retries/idempotency robust while
            # limiting initial import to a bounded 24-hour window.
            if connection.last_sync_at:
                since = connection.last_sync_at - timedelta(minutes=10)
            else:
                since = now - timedelta(hours=24)

            readings = _provider(connection).readings(since)
            records = [
                CGMReadingRecord(
                    patient_id=patient_id,
                    source=connection.source,
                    recorded_at=reading.timestamp,
                    glucose_mg_dl=reading.glucose_mg_dl,
                    trend=reading.trend or "",
                    device=reading.device or "",
                    dedupe_key=_dedupe_key(
                        source=connection.source,
                        recorded_at=reading.timestamp,
                        glucose_mg_dl=reading.glucose_mg_dl,
                        trend=reading.trend or "",
                        device=reading.device or "",
                    ),
                )
                for reading in readings
            ]
            before = CGMReadingRecord.objects.filter(patient_id=patient_id).count()
            if records:
                CGMReadingRecord.objects.bulk_create(records, ignore_conflicts=True)
            after = CGMReadingRecord.objects.filter(patient_id=patient_id).count()

            connection.last_sync_at = now
            connection.last_success_at = now
            connection.last_error_code = ""
            connection.save(
                update_fields=["last_sync_at", "last_success_at", "last_error_code", "updated_at"]
            )
            return CGMSyncResult(
                received=len(readings),
                inserted=max(0, after - before),
                last_recorded_at=max((r.timestamp for r in readings), default=None),
            )
    except CGMConnection.DoesNotExist as exc:
        raise CGMSyncError("cgm_connection_unavailable") from exc
    except CGMCredentialError as exc:
        CGMConnection.objects.filter(patient_id=patient_id).update(last_error_code=str(exc))
        raise CGMSyncError(str(exc)) from exc
    except CGMProviderError as exc:
        CGMConnection.objects.filter(patient_id=patient_id).update(last_error_code="provider_unavailable")
        raise CGMSyncError("provider_unavailable") from exc
