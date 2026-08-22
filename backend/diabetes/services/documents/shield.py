"""
Document Pulper — PulperShield (Phase 12).

Validates every field of a PulperOutput AFTER LLM extraction.
Same philosophy as GlucoseOcrShield and MealVisionShield:
  - Reject or clamp values outside physiological ranges
  - Flag suspicious patterns (hallucinated future dates, impossible HbA1c)
  - Never modify clinical_notes content — only flag length
  - Return the same object with warnings/errors appended; never raise
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from typing import Optional

from .schema import GlucoseReading, LabValues, PulperOutput

logger = logging.getLogger(__name__)

# ── Physiological ranges ──────────────────────────────────────────────────────
_GLUCOSE_MIN   = 20.0    # mg/dL — below this is implausible (physiological min ~40)
_GLUCOSE_MAX   = 600.0   # mg/dL — critically high but possible
_HBA1C_MIN     = 3.0     # %
_HBA1C_MAX     = 20.0    # %
_CHOLESTEROL_MAX = 600.0  # mg/dL
_HDL_MIN       = 10.0
_LDL_MAX       = 500.0
_TRIG_MAX      = 2000.0
_CREATININE_MAX = 2000.0  # µmol/L


def _clamp_glucose(r: GlucoseReading, warnings: list) -> Optional[GlucoseReading]:
    """Return validated reading or None (drop it)."""
    if r.value_mgdl < _GLUCOSE_MIN or r.value_mgdl > _GLUCOSE_MAX:
        warnings.append(
            f"Glycémie hors plage physiologique ({r.value_mgdl:.0f} mg/dL) — ignorée."
        )
        return None
    return r


def _validate_date(d: Optional[str], field_name: str, warnings: list) -> Optional[str]:
    if d is None:
        return None
    try:
        parsed = datetime.strptime(d[:10], "%Y-%m-%d").date()
        if parsed > date.today():
            warnings.append(f"{field_name}: date future ({d}) — ignorée.")
            return None
        if parsed.year < 1900:
            warnings.append(f"{field_name}: date invalide ({d}) — ignorée.")
            return None
        return d[:10]
    except ValueError:
        warnings.append(f"{field_name}: format de date non reconnu ({d!r}) — ignoré.")
        return None


def _validate_datetime(
    value: Optional[str],
    field_name: str,
    warnings: list,
) -> Optional[str]:
    """Validate an ISO-8601 datetime without discarding time or timezone."""
    if value is None:
        return None

    candidate = value.strip()
    if "T" not in candidate and " " not in candidate:
        warnings.append(
            f"{field_name}: heure absente ({value!r}) — timestamp ignoré."
        )
        return None

    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        warnings.append(
            f"{field_name}: format datetime non reconnu ({value!r}) — ignoré."
        )
        return None

    if parsed.year < 1900:
        warnings.append(f"{field_name}: date invalide ({value}) — ignorée.")
        return None

    if parsed.tzinfo is None:
        is_future = parsed > datetime.now()
    else:
        is_future = parsed.astimezone(timezone.utc) > datetime.now(timezone.utc)

    if is_future:
        warnings.append(f"{field_name}: date future ({value}) — ignorée.")
        return None

    # Preserve the accepted source representation exactly (apart from surrounding
    # whitespace). In particular, never coerce an offset/Z timestamp to a date.
    return candidate


def _validate_lab(lab: LabValues, warnings: list) -> LabValues:
    if lab.hba1c_pct is not None:
        if not (_HBA1C_MIN <= lab.hba1c_pct <= _HBA1C_MAX):
            warnings.append(f"HbA1c hors plage ({lab.hba1c_pct}%) — ignoré.")
            lab.hba1c_pct = None

    if lab.fasting_glucose_mgdl is not None:
        if not (_GLUCOSE_MIN <= lab.fasting_glucose_mgdl <= _GLUCOSE_MAX):
            warnings.append(f"Glucose à jeun hors plage ({lab.fasting_glucose_mgdl} mg/dL) — ignoré.")
            lab.fasting_glucose_mgdl = None

    if lab.total_cholesterol_mgdl is not None and lab.total_cholesterol_mgdl > _CHOLESTEROL_MAX:
        warnings.append("Cholestérol total hors plage — ignoré.")
        lab.total_cholesterol_mgdl = None

    if lab.hdl_mgdl is not None and lab.hdl_mgdl < _HDL_MIN:
        warnings.append(f"HDL trop bas ({lab.hdl_mgdl}) — ignoré.")
        lab.hdl_mgdl = None

    if lab.ldl_mgdl is not None and lab.ldl_mgdl > _LDL_MAX:
        warnings.append("LDL hors plage — ignoré.")
        lab.ldl_mgdl = None

    if lab.triglycerides_mgdl is not None and lab.triglycerides_mgdl > _TRIG_MAX:
        warnings.append("Triglycérides hors plage — ignoré.")
        lab.triglycerides_mgdl = None

    if lab.creatinine_umol is not None and lab.creatinine_umol > _CREATININE_MAX:
        warnings.append("Créatinine hors plage — ignorée.")
        lab.creatinine_umol = None

    lab.report_date = _validate_date(lab.report_date, "Date du bilan", warnings)
    return lab


class PulperShield:
    """
    Run validate(output) after LLM extraction.

    Mutates output in-place (appends to warnings/errors, nullifies bad values)
    and returns it.  Never raises.
    """

    @staticmethod
    def validate(output: PulperOutput) -> PulperOutput:
        try:
            PulperShield._validate(output)
        except Exception as exc:
            logger.exception("PulperShield.validate unexpected error: %s", exc)
            output.errors.append(f"Erreur interne de validation: {exc}")
        return output

    @staticmethod
    def _validate(output: PulperOutput) -> None:
        w = output.warnings

        # Glucose readings
        clean = []
        for r in output.glucose_readings:
            validated = _clamp_glucose(r, w)
            if validated:
                validated.timestamp = _validate_datetime(
                    validated.timestamp, "Timestamp glycémie", w
                )
                clean.append(validated)
        output.glucose_readings = clean

        # Lab values
        output.lab_values = _validate_lab(output.lab_values, w)

        # Medications — reject obviously hallucinated names (empty or >80 chars)
        clean_meds = []
        for m in output.medications:
            name = (m.name or '').strip()
            if not name:
                continue
            if len(name) > 80:
                w.append(f"Médicament ignoré (nom trop long): {name[:40]}…")
                continue
            m.name = name
            clean_meds.append(m)
        output.medications = clean_meds

        # Confidence: clamp to [0, 1]
        output.confidence = max(0.0, min(1.0, output.confidence))

        # Clinical notes: cap at 2000 chars to avoid storing hallucinated essays
        if len(output.clinical_notes) > 2000:
            output.clinical_notes = output.clinical_notes[:2000]
            w.append("Notes cliniques tronquées à 2000 caractères.")

        # Raw text: cap at 20 000 chars (audit trail, not patient data)
        if len(output.raw_text) > 20_000:
            output.raw_text = output.raw_text[:20_000]
