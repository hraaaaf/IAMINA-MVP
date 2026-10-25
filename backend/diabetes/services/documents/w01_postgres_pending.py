"""W01 isolated PostgreSQL staging spike — SYNTHETIC DEBUG ONLY.

Not a production data-retention implementation. Postgres physical backups/PITR
can retain JSON clinical payloads beyond the 3600-second logical TTL. Do not
enable for patients without a separate privacy, backup, and deletion design.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from diabetes.models import PendingDocumentExtraction
from diabetes.services.documents.schema import (
    FieldEvidence,
    GlucoseReading,
    LabValues,
    MedicationEntry,
    PulperOutput,
)

logger = logging.getLogger(__name__)
PENDING_TTL_SECONDS = 3600


def ensure_synthetic_debug_only() -> None:
    """Never activate the prototype in Vercel or any non-debug environment."""
    if not getattr(settings, "W01_PG_PENDING_SYNTHETIC_ONLY", False) or not settings.DEBUG:
        raise PermissionError("PostgreSQL pending staging is disabled outside synthetic DEBUG tests")


def _evidence(values: dict) -> dict[str, FieldEvidence]:
    return {name: FieldEvidence(**details) for name, details in values.items()}


def _encode(output: PulperOutput) -> dict:
    body = asdict(output)
    # Full extracted source text is NEVER staged by this candidate.
    body["raw_text"] = ""
    return body


def _decode(body: dict) -> PulperOutput:
    lab = dict(body["lab_values"])
    lab["evidence"] = _evidence(lab.get("evidence", {}))
    readings = []
    for item in body["glucose_readings"]:
        row = dict(item)
        row["evidence"] = _evidence(row.get("evidence", {}))
        readings.append(GlucoseReading(**row))
    medications = []
    for item in body["medications"]:
        row = dict(item)
        row["evidence"] = _evidence(row.get("evidence", {}))
        medications.append(MedicationEntry(**row))
    extra = {
        key: value for key, value in body.items()
        if key not in {"lab_values", "glucose_readings", "medications", "raw_text"}
    }
    return PulperOutput(
        **extra,
        lab_values=LabValues(**lab),
        glucose_readings=readings,
        medications=medications,
        raw_text="",
    )


def prune_expired() -> int:
    """Logical TTL plus best-effort row purge, NOT a physical backup erasure."""
    ensure_synthetic_debug_only()
    deleted, _ = PendingDocumentExtraction.objects.filter(
        expires_at__lte=timezone.now()
    ).delete()
    return deleted


def stage_pending(patient_id: int, output: PulperOutput) -> str:
    ensure_synthetic_debug_only()
    if patient_id <= 0:
        raise ValueError("invalid patient")
    prune_expired()
    batch_id = uuid.uuid4()
    PendingDocumentExtraction.objects.create(
        batch_id=batch_id,
        patient_id=patient_id,
        payload=_encode(output),
        expires_at=timezone.now() + timedelta(seconds=PENDING_TTL_SECONDS),
    )
    return str(batch_id)


def confirm_once(patient, batch_id: str, persist_callback):
    """Row lock and clinical persist share ONE transaction.

    Concurrent requests on PostgreSQL serialize on SELECT FOR UPDATE; once a
    row is consumed, later requests cannot persist the same staged payload.
    An unexpected persistence exception rolls the whole transaction back.
    """
    ensure_synthetic_debug_only()
    try:
        parsed_id = uuid.UUID(batch_id)
    except (ValueError, TypeError, AttributeError):
        return None
    with transaction.atomic():
        pending = (
            PendingDocumentExtraction.objects.select_for_update()
            .filter(
                batch_id=parsed_id,
                patient_id=patient.id,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if pending is None:
            return None
        output = _decode(pending.payload)
        result = persist_callback(output, patient, str(parsed_id))
        pending.delete()
        return result


def purge_patient(patient_id: int) -> int:
    """Delete all staging rows for a synthetic patient; propagate DB failures."""
    ensure_synthetic_debug_only()
    if not isinstance(patient_id, int) or patient_id <= 0:
        raise ValueError("invalid patient")
    deleted, _ = PendingDocumentExtraction.objects.filter(patient_id=patient_id).delete()
    return deleted
