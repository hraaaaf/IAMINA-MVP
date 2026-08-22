"""
Document Pulper — Main orchestrator (Phase 12).

Architecture:
  1. Detect file format from MIME type + filename extension
  2. Route to the correct extractor → raw text OR structured readings
  3. For text documents: call Gemini with the parsing prompt → JSON → PulperOutput
  4. For spreadsheets: skip LLM, map directly to PulperOutput
  5. Run PulperShield validation on the result
  6. Return PulperOutput — always, never raises

ADR-0007 compliance:
  - Gemini prompt is English Pivot Text
  - Patient raw text is sent to LLM only for structural parsing
  - All clinical decisions remain in the clinical engine, not here
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from core.ai_egress import TEXT, assert_ai_egress_allowed
from diabetes.services.documents.extractors.spreadsheet import extract_spreadsheet
from diabetes.services.documents.schema import (
    GlucoseReading,
    LabValues,
    MedicationEntry,
    PulperOutput,
)
from diabetes.services.documents.shield import PulperShield
from media.documents.extractors.docx import extract_docx
from media.documents.extractors.image import extract_image
from media.documents.extractors.pdf import extract_pdf

logger = logging.getLogger(__name__)

# ── MIME type routing ─────────────────────────────────────────────────────────

_PDF_MIMES   = {'application/pdf'}
_IMAGE_MIMES = {'image/jpeg', 'image/jpg', 'image/png', 'image/webp',
                'image/heic', 'image/heif', 'image/tiff', 'image/bmp'}
_SHEET_MIMES = {
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream',   # catch-all — rely on extension
}
_DOCX_MIMES  = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
}

# ── Gemini parsing prompt ─────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a medical document parser for a diabetes management application. "
    "Your task is to extract structured data from medical documents."
)

_PARSE_PROMPT_TEMPLATE = """Extract all medical data from the following document text.

Return ONLY valid JSON with this exact structure (omit fields you cannot find — never invent values):

{{
  "document_type": "lab_report|cgm_export|glucose_log|prescription|medical_report|unknown",
  "confidence": 0.0,
  "lab_values": {{
    "hba1c_pct": null,
    "fasting_glucose_mgdl": null,
    "total_cholesterol_mgdl": null,
    "hdl_mgdl": null,
    "ldl_mgdl": null,
    "triglycerides_mgdl": null,
    "creatinine_umol": null,
    "report_date": null
  }},
  "glucose_readings": [
    {{"value_mgdl": 0.0, "timestamp": null, "context": null, "original_value": null, "original_unit": null}}
  ],
  "medications": [
    {{"name": "", "dose": null, "frequency": null, "drug_type": null}}
  ],
  "clinical_notes": ""
}}

Rules:
- confidence: 0.0–1.0 — how certain you are about the extracted values
- Convert mmol/L to mg/dL: multiply by 18.018
- Convert % HbA1c values (e.g. "7.2%" → 7.2)
- lab_values.report_date: use "YYYY-MM-DD" when present
- glucose_readings.timestamp: preserve an explicit source date+time as ISO-8601; keep its timezone/offset when present
- if a glucose reading has no explicit time, set timestamp to null; NEVER invent midnight or a timezone
- context must be one of: fasting, post_meal, bedtime, random, or null
- glucose_readings: include explicit numeric readings; timestamp may be null when the source provides no date-time
- NEVER invent values — if not present in the document, use null
- clinical_notes: short summary of any medical observations, diagnoses, or recommendations
- Return ONLY the JSON object — no markdown, no explanation

Document text:
---
{text}
---"""


def ingest(
    file_bytes: bytes,
    filename: str,
    mime_type: str,
) -> PulperOutput:
    """
    Main entry point.  Always returns PulperOutput, never raises.

    Args:
        file_bytes  — raw uploaded file content
        filename    — original filename (used for extension detection)
        mime_type   — MIME type declared by the client
    """
    output = PulperOutput()

    try:
        _ingest(output, file_bytes, filename, mime_type)
    except Exception as exc:
        logger.exception("pulper.ingest unexpected error: %s", exc)
        output.errors.append(f"Erreur d'ingestion: {exc}")
        output.confidence = 0.0

    return PulperShield.validate(output)


# ── Internal ──────────────────────────────────────────────────────────────────

def _ingest(output: PulperOutput, file_bytes: bytes, filename: str, mime_type: str) -> None:
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

    # ── Spreadsheet: direct mapping, no LLM needed ───────────────────────────
    if mime_type in _SHEET_MIMES or ext in ('csv', 'xlsx', 'xls'):
        _handle_spreadsheet(output, file_bytes, filename)
        return

    # ── DOCX ─────────────────────────────────────────────────────────────────
    if mime_type in _DOCX_MIMES or ext in ('docx', 'doc'):
        raw_text = extract_docx(file_bytes)
        output.source_format = 'docx'
        output.raw_text = raw_text
        if raw_text:
            _parse_with_llm(output, raw_text)
        else:
            output.errors.append("Impossible d'extraire le texte du document Word.")
        return

    # ── PDF ───────────────────────────────────────────────────────────────────
    if mime_type in _PDF_MIMES or ext == 'pdf':
        raw_text, is_scanned = extract_pdf(file_bytes)
        output.source_format = 'pdf_scanned' if is_scanned else 'pdf'
        output.raw_text = raw_text
        if raw_text:
            _parse_with_llm(output, raw_text)
        else:
            output.errors.append("Impossible d'extraire le texte du PDF.")
        return

    # ── Image ─────────────────────────────────────────────────────────────────
    if mime_type in _IMAGE_MIMES or ext in ('jpg', 'jpeg', 'png', 'webp', 'heic', 'tiff', 'bmp'):
        raw_text = extract_image(file_bytes, mime_type or 'image/jpeg')
        output.source_format = 'image'
        output.raw_text = raw_text
        if raw_text:
            _parse_with_llm(output, raw_text)
        else:
            output.errors.append("Impossible de lire le contenu de l'image.")
        return

    # ── Unknown ───────────────────────────────────────────────────────────────
    output.source_format = 'unknown'
    output.errors.append(f"Format non reconnu: {mime_type} / .{ext}")
    output.confidence = 0.0


def _handle_spreadsheet(output: PulperOutput, file_bytes: bytes, filename: str) -> None:
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else 'csv'
    output.source_format = 'excel' if ext in ('xlsx', 'xls') else 'csv'

    readings, source_type, raw_summary = extract_spreadsheet(file_bytes, filename)
    output.raw_text     = raw_summary
    output.document_type = source_type

    if not readings:
        output.errors.append("Aucune glycémie trouvée dans le fichier.")
        output.confidence = 0.0
        return

    output.glucose_readings = [
        GlucoseReading(
            value_mgdl=r['value_mgdl'],
            timestamp=r.get('timestamp'),
            context=r.get('context'),
            original_value=r.get('original_value'),
            original_unit=r.get('original_unit'),
        )
        for r in readings
    ]
    output.confidence = 0.95   # direct structured extraction = high confidence


def _parse_with_llm(output: PulperOutput, raw_text: str) -> None:
    """
    Parse raw_text into structured fields via the LLM factory.

    Uses get_llm() so the full provider chain (Gemini → Kimi → Fallback)
    applies here, including the daily rate guard and quota diabetes.
    """
    from llm.factory import get_llm

    # PHI-AUDIT(P1.3): strip CIN and date-of-birth patterns from extracted text before
    # forwarding to LLM. Full name stripping is deferred — the pulper has no patient
    # context at this callsite (signature change needed to accept patient_first_name).
    from llm.pseudonymizer import PHIPseudonymizer
    _phi = PHIPseudonymizer()
    safe_text = _phi.mask(raw_text[:8000])
    prompt = _PARSE_PROMPT_TEMPLATE.format(text=safe_text)

    try:
        assert_ai_egress_allowed(TEXT)
        llm = get_llm()
        response = llm.complete(_SYSTEM_PROMPT, prompt)
        json_text = (response.content or '').strip()

        # Strip markdown fences if present
        json_text = re.sub(r'^```(?:json)?\s*', '', json_text, flags=re.MULTILINE)
        json_text = re.sub(r'\s*```$', '', json_text, flags=re.MULTILINE)

        data = json.loads(json_text)
        _map_json_to_output(output, data)

    except json.JSONDecodeError as exc:
        logger.warning("pulper: LLM returned non-JSON: %s", exc)
        output.errors.append("L'IA n'a pas retourné un JSON valide.")
        output.confidence = 0.1   # text was extracted but not structured

    except Exception as exc:
        logger.warning("pulper: LLM call failed: %s", exc)
        output.errors.append(f"Erreur lors de l'analyse IA: {exc}")
        output.confidence = 0.1


def _map_json_to_output(output: PulperOutput, data: dict) -> None:
    """Map parsed JSON dict → PulperOutput fields."""
    output.document_type = data.get('document_type', 'unknown')
    output.confidence    = float(data.get('confidence', 0.5))

    # Lab values
    lv = data.get('lab_values') or {}
    output.lab_values = LabValues(
        hba1c_pct=_float(lv.get('hba1c_pct')),
        fasting_glucose_mgdl=_float(lv.get('fasting_glucose_mgdl')),
        total_cholesterol_mgdl=_float(lv.get('total_cholesterol_mgdl')),
        hdl_mgdl=_float(lv.get('hdl_mgdl')),
        ldl_mgdl=_float(lv.get('ldl_mgdl')),
        triglycerides_mgdl=_float(lv.get('triglycerides_mgdl')),
        creatinine_umol=_float(lv.get('creatinine_umol')),
        report_date=lv.get('report_date'),
    )

    # Glucose readings
    output.glucose_readings = []
    for r in data.get('glucose_readings') or []:
        val = _float(r.get('value_mgdl'))
        if val is None:
            continue
        output.glucose_readings.append(GlucoseReading(
            value_mgdl=val,
            timestamp=r.get('timestamp'),
            context=r.get('context'),
            original_value=_float(r.get('original_value')),
            original_unit=r.get('original_unit'),
        ))

    # Medications
    output.medications = []
    for m in data.get('medications') or []:
        name = (m.get('name') or '').strip()
        if name:
            output.medications.append(MedicationEntry(
                name=name,
                dose=m.get('dose'),
                frequency=m.get('frequency'),
                drug_type=m.get('drug_type'),
            ))

    # Notes
    output.clinical_notes = (data.get('clinical_notes') or '').strip()


def _float(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        return None if (f == 0.0 and v == 0) else f   # treat explicit 0 as missing
    except (TypeError, ValueError):
        return None
