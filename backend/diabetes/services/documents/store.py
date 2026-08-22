"""
Document Pulper — Store layer (Phase 12).

Persists a validated PulperOutput to the database:
  - LabReport row    (one per patient + source SHA-256 when available)
  - LogEntry rows    (one per distinct imported glucose reading)

Idempotency:
  - patient-scoped source SHA-256 reuses the same LabReport on re-import;
  - all diabetes import paths share one deterministic reading identity;
  - semantic lookup catches legacy rows created by older UUID schemes.

Never raises — returns a StoreResult with counts and any errors.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import F

from diabetes.models import LabReport, LogEntry
from diabetes.services.import_identity import (
    imported_reading_exists,
    make_import_client_uuid,
    normalize_import_timestamp,
)

from .neutral_adapter import provenance_snapshot
from .schema import PulperOutput

logger = logging.getLogger(__name__)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
    """Persist PulperOutput to database. Always returns StoreResult, never raises."""
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
    source_sha256 = _normalize_source_sha256(output.source_sha256)
    report_defaults = {
        "document_type": output.document_type,
        "source_format": output.source_format,
        "report_date": _parse_date(lv.report_date),
        "hba1c_pct": lv.hba1c_pct,
        "fasting_glucose_mgdl": lv.fasting_glucose_mgdl,
        "total_cholesterol_mgdl": lv.total_cholesterol_mgdl,
        "hdl_mgdl": lv.hdl_mgdl,
        "ldl_mgdl": lv.ldl_mgdl,
        "triglycerides_mgdl": lv.triglycerides_mgdl,
        "creatinine_umol": lv.creatinine_umol,
        "confidence": output.confidence,
        "clinical_notes": output.clinical_notes,
        "raw_text": output.raw_text,
        "extraction_provenance": provenance_snapshot(output),
        "import_batch_id": import_batch_id,
    }

    if source_sha256:
        report, _created = LabReport.objects.get_or_create(
            patient=patient,
            source_sha256=source_sha256,
            defaults=report_defaults,
        )
    else:
        report = LabReport.objects.create(
            patient=patient,
            source_sha256=None,
            **report_defaults,
        )
    result.lab_report_id = report.pk

    for reading in output.glucose_readings:
        ts = _parse_timestamp(reading.timestamp)
        if ts is None:
            result.errors.append(
                "Lecture glycémique sans timestamp explicite — non sauvegardée."
            )
            continue

        canonical_ts = normalize_import_timestamp(ts)
        if imported_reading_exists(patient, canonical_ts, reading.value_mgdl):
            result.glucose_duplicates += 1
            continue

        client_uuid = make_import_client_uuid(
            patient.pk,
            canonical_ts,
            reading.value_mgdl,
        )

        try:
            LogEntry.objects.create(
                patient=patient,
                logged_at=canonical_ts,
                blood_sugar=reading.value_mgdl,
                client_uuid=client_uuid,
                source="import",
                meal_type=reading.context or "",
            )
            result.glucose_readings_saved += 1
        except IntegrityError:
            result.glucose_duplicates += 1
        except Exception as exc:
            logger.warning("store: LogEntry creation failed: %s", exc)
            result.errors.append(f"Lecture glycémique ignorée: {exc}")

    if result.glucose_readings_saved:
        LabReport.objects.filter(pk=report.pk).update(
            glucose_readings_imported=F("glucose_readings_imported")
            + result.glucose_readings_saved
        )


def _make_uuid(
    patient_id: int,
    ts: datetime,
    glucose: float,
    batch: str | None = None,
) -> str:
    """Backward-compatible helper; batch no longer participates in identity."""
    return make_import_client_uuid(patient_id, ts, glucose)


def _normalize_source_sha256(value: str | None) -> str:
    if not value:
        return ""
    normalized = str(value).strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError("source_sha256 invalide")
    return normalized


def _parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None

    candidate = str(ts).strip()
    if "T" not in candidate and " " not in candidate:
        return None

    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_date(d: Optional[str]):
    if not d:
        return None
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
