"""
Document Pulper — Standardised output schema (Phase 12).

PulperOutput is the SINGLE format that flows from any extractor through the
shield and into the store.  Every field is nullable so partial extraction is
valid; the shield decides whether confidence is sufficient to persist.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FieldEvidence:
    """Verified pointer from a normalized value back to source evidence."""

    raw_value: Optional[str] = None
    source_ref: Optional[str] = None
    verified: bool = False


@dataclass
class GlucoseReading:
    value_mgdl:    float
    timestamp:     Optional[str]   = None   # ISO-8601 or None
    context:       Optional[str]   = None   # fasting|post_meal|bedtime|random
    original_value: Optional[float] = None
    original_unit:  Optional[str]  = None   # "mg/dL" | "mmol/L"
    evidence: Dict[str, FieldEvidence] = field(default_factory=dict)


@dataclass
class LabValues:
    hba1c_pct:              Optional[float] = None
    fasting_glucose_mgdl:   Optional[float] = None
    total_cholesterol_mgdl: Optional[float] = None
    hdl_mgdl:               Optional[float] = None
    ldl_mgdl:               Optional[float] = None
    triglycerides_mgdl:     Optional[float] = None
    creatinine_umol:        Optional[float] = None
    report_date:            Optional[str]   = None   # "YYYY-MM-DD"
    evidence: Dict[str, FieldEvidence] = field(default_factory=dict)


@dataclass
class MedicationEntry:
    name:      str
    dose:      Optional[str] = None
    frequency: Optional[str] = None
    drug_type: Optional[str] = None   # oral|insulin_basal|insulin_rapid|other
    evidence: Dict[str, FieldEvidence] = field(default_factory=dict)


@dataclass
class PulperOutput:
    # ── Classification ───────────────────────────────────────────────────────
    document_type:  str   = 'unknown'   # lab_report|cgm_export|glucose_log|prescription|medical_report|unknown
    source_format:  str   = 'unknown'   # pdf|pdf_scanned|image|excel|csv|docx|unknown
    confidence:     float = 0.0         # 0.0–1.0

    # ── Extracted data ───────────────────────────────────────────────────────
    glucose_readings: List[GlucoseReading] = field(default_factory=list)
    lab_values:       LabValues            = field(default_factory=LabValues)
    medications:      List[MedicationEntry]= field(default_factory=list)
    clinical_notes:   str                  = ''

    # ── Provenance ────────────────────────────────────────────────────────────
    source_sha256:     str           = ''
    extractor:         str           = ''
    extractor_version: str           = ''
    extractor_model:   Optional[str] = None
    schema_version:    str           = 'pulper-output-v2'
    parser_model:      Optional[str] = None
    prompt_version:    Optional[str] = None

    # ── Audit / debug ────────────────────────────────────────────────────────
    raw_text:   str        = ''
    warnings:   List[str]  = field(default_factory=list)
    errors:     List[str]  = field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        """True when there is at least something to persist and confidence is acceptable."""
        has_data = (
            bool(self.glucose_readings)
            or self.lab_values.hba1c_pct is not None
            or self.lab_values.fasting_glucose_mgdl is not None
            or bool(self.medications)
            or bool(self.clinical_notes)
        )
        return has_data and self.confidence >= 0.3

    @property
    def needs_review(self) -> bool:
        """True when data is present but confidence is low — show UI warning."""
        return self.is_usable and self.confidence < 0.7
