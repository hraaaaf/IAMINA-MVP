"""
Import API — CSV glucose data import.

POST /api/v1/import/librelink
  Body: multipart/form-data  (field: csv_file — UploadedFile)
  Returns: ImportResultResponse with counts + sample of imported readings.

Pipeline:
  1. Read uploaded CSV bytes, decode to text
  2. Parse via diabetes.services.import_csv (anti-hallucination range check)
  3. Create LogEntry records with shared import identity
  4. Return import summary: {imported, duplicates, rejected, preview[0:3]}

Idempotency:
  All diabetes import paths share a deterministic identity derived from
  (patient_id, canonical UTC timestamp, glucose at storage precision).
  Semantic lookup also catches legacy imported rows with older UUID schemes.
"""
from __future__ import annotations

import logging
from typing import Optional

from django.db import IntegrityError
from django.http import HttpRequest
from ninja import File, Router, Schema, UploadedFile

from diabetes.models import LogEntry
from diabetes.services.import_csv import parse_librelink_csv
from diabetes.services.import_identity import (
    imported_reading_exists,
    make_import_client_uuid,
    normalize_import_timestamp,
)

logger = logging.getLogger(__name__)
router = Router(tags=["import"])


class ImportSample(Schema):
    timestamp:   str
    glucose:     float
    record_type: str


class ImportResultResponse(Schema):
    ok:              bool
    imported:        int
    duplicates:      int
    rejected_values: int
    skipped_rows:    int
    detected_format: str
    error:           Optional[str] = None
    sample:          list[ImportSample]


def _make_client_uuid(patient_id: int, ts, glucose: float) -> str:
    """Backward-compatible wrapper around the shared import identity."""
    return make_import_client_uuid(patient_id, ts, glucose)


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
    patient = request.auth
    patient_id = getattr(patient, "id", 0)

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

    imported = 0
    duplicates = 0
    database_failed = False

    for reading in result.readings:
        canonical_ts = normalize_import_timestamp(reading.timestamp)

        if imported_reading_exists(patient, canonical_ts, reading.glucose_mgdl):
            duplicates += 1
            continue

        client_uuid = _make_client_uuid(
            patient_id,
            canonical_ts,
            reading.glucose_mgdl,
        )

        try:
            LogEntry.objects.create(
                patient=patient,
                logged_at=canonical_ts,
                blood_sugar=reading.glucose_mgdl,
                client_uuid=client_uuid,
                source="import",
                meal_type="",
            )
            imported += 1
        except IntegrityError:
            duplicates += 1
        except Exception as exc:
            database_failed = True
            logger.warning("librelink import: row failed: %s", exc)

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
        patient_id,
        imported,
        duplicates,
        result.rejected_values,
        result.detected_format,
    )

    return ImportResultResponse(
        ok=not database_failed,
        imported=imported,
        duplicates=duplicates,
        rejected_values=result.rejected_values,
        skipped_rows=result.skipped_rows,
        detected_format=result.detected_format,
        error="database_write_failed" if database_failed else None,
        sample=sample,
    )
