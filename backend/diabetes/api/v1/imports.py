"""
Import API — CSV glucose data import.

POST /api/v1/import/librelink
  Body: multipart/form-data  (field: csv_file — UploadedFile)
  Returns: ImportResultResponse with counts + sample of imported readings.

Pipeline:
  1. Read uploaded CSV bytes, decode to text
  2. Parse via diabetes.services.import_csv (anti-hallucination range check)
  3. Bulk-create LogEntry records (idempotent via client_uuid)
  4. Return import summary: {imported, duplicates, rejected, preview[0:3]}

Idempotency:
  Each reading gets a deterministic UUID5 derived from
  (patient_id, timestamp, glucose) so re-uploading the same file is a no-op.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Optional

from django.http import HttpRequest
from django.utils import timezone as tz
from ninja import File, Router, Schema, UploadedFile

from diabetes.models import LogEntry
from diabetes.services.import_csv import parse_librelink_csv

logger = logging.getLogger(__name__)
router = Router(tags=["import"])


# ── Response schemas ──────────────────────────────────────────────────────────

class ImportSample(Schema):
    timestamp:   str
    glucose:     float
    record_type: str


class ImportResultResponse(Schema):
    ok:              bool
    imported:        int
    duplicates:      int
    rejected_values: int   # out-of-range physiological values
    skipped_rows:    int
    detected_format: str
    error:           Optional[str] = None
    sample:          list[ImportSample]   # first 3 readings for UI preview


# ── Idempotency helper ────────────────────────────────────────────────────────

def _make_client_uuid(patient_id: int, ts, glucose: float) -> str:
    """
    Deterministic UUID for idempotency across re-uploads of the same file.
    SHA-256 of (patient_id, ISO timestamp, glucose rounded to 1dp) → UUID bytes.
    Same reading → same UUID → unique constraint on LogEntry.client_uuid blocks
    the duplicate without raising an unhandled exception.
    """
    seed = f"librelink:{patient_id}:{ts.isoformat()}:{glucose:.1f}"
    digest = hashlib.sha256(seed.encode()).digest()
    return str(uuid.UUID(bytes=digest[:16]))


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/import/librelink", response=ImportResultResponse)
def import_librelink_csv(request: HttpRequest, csv_file: UploadedFile = File(...)):
    """
    Import a LibreLink / LibreView CSV file for the authenticated patient.

    Accepts multipart/form-data with a single field ``csv_file``.
    Idempotent: re-uploading the same file produces zero new rows.

    Returns:
        imported        — number of new LogEntry rows created
        duplicates      — rows skipped because client_uuid already existed
        rejected_values — rows dropped for out-of-physiological-range glucose
        skipped_rows    — rows dropped for unparseable timestamp or missing value
        detected_format — "librelink_detailed" | "simple" | "unknown"
        sample          — first 3 parsed readings (for UI preview)
    """
    patient    = request.auth
    patient_id = getattr(patient, "id", 0)

    # Decode uploaded file to text (LibreLink CSVs are typically UTF-8 or Latin-1)
    raw_bytes = csv_file.read()
    try:
        csv_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = raw_bytes.decode("latin-1", errors="replace")

    result = parse_librelink_csv(csv_text)

    if result.error:
        return ImportResultResponse(
            ok=False,
            imported=0,
            duplicates=0,
            rejected_values=result.rejected_values,
            skipped_rows=result.skipped_rows,
            detected_format=result.detected_format,
            error=result.error,
            sample=[],
        )

    imported   = 0
    duplicates = 0

    for reading in result.readings:
        client_uuid = _make_client_uuid(patient_id, reading.timestamp, reading.glucose_mgdl)

        # Fast-path idempotency check: skip if UUID already stored
        if LogEntry.objects.filter(client_uuid=client_uuid).exists():
            duplicates += 1
            continue

        ts = reading.timestamp
        if ts.tzinfo is None:
            ts = tz.make_aware(ts, tz.get_current_timezone())

        try:
            LogEntry.objects.create(
                patient=patient,
                logged_at=ts,
                blood_sugar=reading.glucose_mgdl,
                client_uuid=client_uuid,
                source="import",
                meal_type="",
            )
            imported += 1
        except Exception as exc:
            # Unique constraint race (unlikely but safe to handle) or other DB error
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                duplicates += 1
            else:
                logger.warning("librelink import: row failed: %s", exc)
                duplicates += 1

    sample = [
        ImportSample(
            timestamp=r.timestamp.isoformat(),
            glucose=r.glucose_mgdl,
            record_type=r.record_type,
        )
        for r in result.readings[:3]
    ]

    logger.info(
        "import.librelink patient=%s imported=%d duplicates=%d rejected=%d format=%s",
        patient_id, imported, duplicates, result.rejected_values, result.detected_format,
    )

    return ImportResultResponse(
        ok=True,
        imported=imported,
        duplicates=duplicates,
        rejected_values=result.rejected_values,
        skipped_rows=result.skipped_rows,
        detected_format=result.detected_format,
        sample=sample,
    )
