"""
Document Pulper API — Phase 12
================================
POST /api/v1/documents/ingest
  Body: multipart/form-data
    - file     : UploadedFile  (PDF, image, Excel, CSV, DOCX)
    - confirm  : bool = False  — if True, persist to DB; if False, return preview only

Two-step flow:
  1. POST with confirm=False → returns PulperPreviewResponse (no DB write)
     Flutter shows the user what was extracted, asks for confirmation.
  2. POST with confirm=True  → persists and returns PulperConfirmResponse

GET /api/v1/documents/
  Returns list of LabReport rows for the current patient.

Anti-hallucination discipline:
  - All data passes through PulperShield before returning to client
  - Confirmation is MANDATORY before any DB write (confirm=False default)
  - confidence + warnings shown in preview so user can spot errors
"""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from django.core.cache import cache
from django.http import HttpRequest
from ninja import File, Router, Schema, UploadedFile

from core.ai_egress import IMAGE, TEXT, patient_ai_egress_scope
from diabetes.models import LabReport
from diabetes.services.documents.pulper import ingest
from diabetes.services.documents.store import persist

logger = logging.getLogger(__name__)
router = Router(tags=["documents"])

_MAX_UPLOAD_BYTES = 15 * 1024 * 1024


# ── Response schemas ──────────────────────────────────────────────────────────

class GlucoseReadingOut(Schema):
    value_mgdl:     float
    timestamp:      Optional[str]  = None
    context:        Optional[str]  = None
    original_value: Optional[float] = None
    original_unit:  Optional[str]  = None


class LabValuesOut(Schema):
    hba1c_pct:              Optional[float] = None
    fasting_glucose_mgdl:   Optional[float] = None
    total_cholesterol_mgdl: Optional[float] = None
    hdl_mgdl:               Optional[float] = None
    ldl_mgdl:               Optional[float] = None
    triglycerides_mgdl:     Optional[float] = None
    creatinine_umol:        Optional[float] = None
    report_date:            Optional[str]   = None


class MedicationOut(Schema):
    name:      str
    dose:      Optional[str] = None
    frequency: Optional[str] = None
    drug_type: Optional[str] = None


class PulperPreviewResponse(Schema):
    """Returned on confirm=False — nothing persisted yet."""
    batch_id:         str
    document_type:    str
    source_format:    str
    confidence:       float
    needs_review:     bool
    glucose_readings: List[GlucoseReadingOut]
    lab_values:       LabValuesOut
    medications:      List[MedicationOut]
    clinical_notes:   str
    warnings:         List[str]
    errors:           List[str]


class PulperConfirmResponse(Schema):
    """Returned on confirm=True — data has been persisted."""
    ok:                       bool
    lab_report_id:            Optional[int]
    glucose_readings_saved:   int
    glucose_duplicates:       int
    errors:                   List[str]


class LabReportOut(Schema):
    id:                       int
    document_type:            str
    source_format:            str
    report_date:              Optional[str]
    hba1c_pct:                Optional[float]
    fasting_glucose_mgdl:     Optional[float]
    total_cholesterol_mgdl:   Optional[float]
    hdl_mgdl:                 Optional[float]
    ldl_mgdl:                 Optional[float]
    triglycerides_mgdl:       Optional[float]
    creatinine_umol:          Optional[float]
    glucose_readings_imported: int
    confidence:               float
    clinical_notes:           str
    created_at:               str


# ── Pending batch store (Django cache / Redis) ────────────────────────────────
# Replaces the former in-memory dict which broke on multi-worker Gunicorn deploys
# (4 workers = 4 separate dicts; confirm_import would 404 cross-worker).
# Django cache with IGNORE_EXCEPTIONS=True gracefully degrades to None on miss
# when Redis is unavailable, triggering the "Session expirée" error path.
_PENDING_TTL = 3600  # 1 hour — plenty for human review + confirmation


def _pending_key(batch_id: str) -> str:
    return f"pulper:pending:{batch_id}"


def _read_upload_with_limit(file: UploadedFile) -> tuple[bytes | None, str | None]:
    """Reject oversize uploads before a full read, with a bounded-read fallback."""
    declared_size = getattr(file, "size", None)
    if isinstance(declared_size, int) and declared_size > _MAX_UPLOAD_BYTES:
        return None, "too_large"

    file_bytes = file.read(_MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) == 0:
        return None, "empty"
    if len(file_bytes) > _MAX_UPLOAD_BYTES:
        return None, "too_large"
    return file_bytes, None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/documents/ingest", response={200: PulperPreviewResponse, 422: dict})
@patient_ai_egress_scope("document_ingest", TEXT, IMAGE)
def ingest_document(
    request: HttpRequest,
    file: UploadedFile = File(...),
    confirm: bool = False,
):
    """
    Stage 1 (confirm=False): Extract and validate.  Returns preview.
    Stage 2 (confirm=True):  Persist from a previously staged batch_id
                             passed as query param ?batch_id=<uuid>.
    """
    patient   = request.auth
    mime_type = file.content_type or ''
    filename  = file.name or 'upload'

    file_bytes, upload_error = _read_upload_with_limit(file)
    if upload_error == "empty":
        return 422, {"detail": "Fichier vide."}
    if upload_error == "too_large":
        return 422, {"detail": "Fichier trop volumineux (max 15 MB)."}
    assert file_bytes is not None

    # ── Extract ────────────────────────────────────────────────────────────────
    output    = ingest(file_bytes, filename, mime_type)
    batch_id  = str(uuid.uuid4())
    cache.set(_pending_key(batch_id), output, timeout=_PENDING_TTL)

    preview = PulperPreviewResponse(
        batch_id=batch_id,
        document_type=output.document_type,
        source_format=output.source_format,
        confidence=output.confidence,
        needs_review=output.needs_review,
        glucose_readings=[
            GlucoseReadingOut(
                value_mgdl=r.value_mgdl,
                timestamp=r.timestamp,
                context=r.context,
                original_value=r.original_value,
                original_unit=r.original_unit,
            )
            for r in output.glucose_readings
        ],
        lab_values=LabValuesOut(
            hba1c_pct=output.lab_values.hba1c_pct,
            fasting_glucose_mgdl=output.lab_values.fasting_glucose_mgdl,
            total_cholesterol_mgdl=output.lab_values.total_cholesterol_mgdl,
            hdl_mgdl=output.lab_values.hdl_mgdl,
            ldl_mgdl=output.lab_values.ldl_mgdl,
            triglycerides_mgdl=output.lab_values.triglycerides_mgdl,
            creatinine_umol=output.lab_values.creatinine_umol,
            report_date=output.lab_values.report_date,
        ),
        medications=[
            MedicationOut(name=m.name, dose=m.dose, frequency=m.frequency, drug_type=m.drug_type)
            for m in output.medications
        ],
        clinical_notes=output.clinical_notes,
        warnings=output.warnings,
        errors=output.errors,
    )

    if not confirm:
        logger.info(
            "documents.ingest preview patient=%s type=%s confidence=%.0f%% readings=%d",
            getattr(patient, 'id', '?'), output.document_type,
            output.confidence * 100, len(output.glucose_readings),
        )
        return 200, preview

    # ── Confirm & persist ──────────────────────────────────────────────────────
    return _do_persist(output, patient, batch_id)


@router.post("/documents/confirm/{batch_id}", response=PulperConfirmResponse)
def confirm_import(request: HttpRequest, batch_id: str):
    """
    Persist a previously staged extraction (batch_id from /ingest response).
    Called when the user taps "Confirmer" in the Flutter UI.
    """
    output = cache.get(_pending_key(batch_id))
    if output is not None:
        cache.delete(_pending_key(batch_id))   # consume once — no replay attacks
    if output is None:
        return PulperConfirmResponse(
            ok=False,
            lab_report_id=None,
            glucose_readings_saved=0,
            glucose_duplicates=0,
            errors=["Session expirée — veuillez réimporter le document."],
        )

    patient = request.auth
    return _do_persist(output, patient, batch_id)


@router.get("/documents/", response=List[LabReportOut])
def list_lab_reports(request: HttpRequest, limit: int = 20):
    """Return the most recent LabReport rows for the authenticated patient."""
    patient  = request.auth
    reports  = LabReport.objects.filter(patient=patient)[:limit]
    return [
        LabReportOut(
            id=r.pk,
            document_type=r.document_type,
            source_format=r.source_format,
            report_date=r.report_date.isoformat() if r.report_date else None,
            hba1c_pct=r.hba1c_pct,
            fasting_glucose_mgdl=r.fasting_glucose_mgdl,
            total_cholesterol_mgdl=r.total_cholesterol_mgdl,
            hdl_mgdl=r.hdl_mgdl,
            ldl_mgdl=r.ldl_mgdl,
            triglycerides_mgdl=r.triglycerides_mgdl,
            creatinine_umol=r.creatinine_umol,
            glucose_readings_imported=r.glucose_readings_imported,
            confidence=r.confidence,
            clinical_notes=r.clinical_notes,
            created_at=r.created_at.isoformat(),
        )
        for r in reports
    ]


# ── Helper ────────────────────────────────────────────────────────────────────

def _do_persist(output, patient, batch_id: str) -> PulperConfirmResponse:
    store_result = persist(output, patient, batch_id)
    logger.info(
        "documents.confirm patient=%s batch=%s saved=%d dups=%d",
        getattr(patient, 'id', '?'), batch_id,
        store_result.glucose_readings_saved, store_result.glucose_duplicates,
    )
    return PulperConfirmResponse(
        ok=store_result.ok,
        lab_report_id=store_result.lab_report_id,
        glucose_readings_saved=store_result.glucose_readings_saved,
        glucose_duplicates=store_result.glucose_duplicates,
        errors=store_result.errors,
    )
