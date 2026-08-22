"""
Document Pulper — Store layer (Phase 12).

Persists a validated PulperOutput to the database:
  - LabReport row    (always, even if only clinical_notes are present)
  - LogEntry rows    (one per glucose_reading, source='import')

Uses the same idempotency pattern as imports.py:
  Deterministic UUID5 on (patient_id, timestamp, value) prevents duplicates
  when the same file is imported twice.

Never raises — returns a StoreResult with counts and any errors.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from django.contrib.auth.models import User
from django.utils import timezone as tz

from diabetes.models import LabReport, LogEntry

from .schema import PulperOutput

logger = logging.getLogger(__name__)


@dataclass
class StoreResult:
    lab_report_id:          Optional[int] = None
    glucose_readings_saved: int           = 0
    glucose_duplicates:     int           = 0
    errors:                 List[str]     = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and self.lab_report_id is not None


def persist(output: PulperOutput, patient: User, import_batch_id: str) -> StoreResult:
    """
    Persist PulperOutput to database.  Always returns StoreResult, never raises.
    """
    result = StoreResult()
    try:
        _persist(output, patient, import_batch_id, result)
    except Exception as exc:
        logger.exception("pulper.store.persist unexpected error: %s", exc)
        result.errors.append(f"Erreur de sauvegarde: {exc}")
    return result


def _persist(
    output: PulperOutput,
    patient: User,
    import_batch_id: str,
    result: StoreResult,
) -> None:
    lv = output.lab_values

    # ── LabReport ──────────────────────────────────────────────────────────────
    report = LabReport.objects.create(
        patient=patient,
        document_type=output.document_type,
        source_format=output.source_format,
        report_date=_parse_date(lv.report_date),
        hba1c_pct=lv.hba1c_pct,
        fasting_glucose_mgdl=lv.fasting_glucose_mgdl,
        total_cholesterol_mgdl=lv.total_cholesterol_mgdl,
        hdl_mgdl=lv.hdl_mgdl,
        ldl_mgdl=lv.ldl_mgdl,
        triglycerides_mgdl=lv.triglycerides_mgdl,
        creatinine_umol=lv.creatinine_umol,
        confidence=output.confidence,
        clinical_notes=output.clinical_notes,
        raw_text=output.raw_text,
        import_batch_id=import_batch_id,
    )
    result.lab_report_id = report.pk

    # ── LogEntry rows (glucose readings) ──────────────────────────────────────
    for reading in output.glucose_readings:
        ts = _parse_timestamp(reading.timestamp)
        if ts is None:
            result.errors.append(
                "Lecture glycémique sans timestamp explicite — non sauvegardée."
            )
            continue
        if ts.tzinfo is None:
            ts = tz.make_aware(ts, tz.get_current_timezone())

        client_uuid = _make_uuid(patient.pk, ts, reading.value_mgdl, import_batch_id)

        if LogEntry.objects.filter(client_uuid=client_uuid).exists():
            result.glucose_duplicates += 1
            continue

        try:
            LogEntry.objects.create(
                patient=patient,
                logged_at=ts,
                blood_sugar=reading.value_mgdl,
                client_uuid=client_uuid,
                source='import',
                meal_type=reading.context or '',
            )
            result.glucose_readings_saved += 1
        except Exception as exc:
            if 'unique' in str(exc).lower():
                result.glucose_duplicates += 1
            else:
                logger.warning("store: LogEntry creation failed: %s", exc)
                result.errors.append(f"Lecture glycémique ignorée: {exc}")

    report.glucose_readings_imported = result.glucose_readings_saved
    report.save(update_fields=['glucose_readings_imported'])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_uuid(patient_id: int, ts: datetime, glucose: float, batch: str) -> str:
    seed = f"pulper:{patient_id}:{ts.isoformat()}:{glucose:.1f}:{batch}"
    digest = hashlib.sha256(seed.encode()).digest()
    return str(uuid.UUID(bytes=digest[:16]))


def _parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None

    candidate = str(ts).strip()
    if 'T' not in candidate and ' ' not in candidate:
        return None

    try:
        return datetime.fromisoformat(candidate.replace('Z', '+00:00'))
    except ValueError:
        return None


def _parse_date(d: Optional[str]):
    if not d:
        return None
    try:
        return datetime.strptime(d[:10], '%Y-%m-%d').date()
    except ValueError:
        return None
