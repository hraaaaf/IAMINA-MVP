"""Compatibility adapter between the chassis document contract and diabetes.

This module is intentionally condition-owned. The chassis contract never imports
this module or any diabetes type.
"""
from __future__ import annotations

from core.contracts.document_extraction import (
    DocumentExtraction,
    ExtractedField,
    ExtractedRecord,
)
from diabetes.services.documents.schema import (
    GlucoseReading,
    LabValues,
    MedicationEntry,
    PulperOutput,
)

_LAB_FIELDS = (
    ("hba1c_pct", "%"),
    ("fasting_glucose_mgdl", "mg/dL"),
    ("total_cholesterol_mgdl", "mg/dL"),
    ("hdl_mgdl", "mg/dL"),
    ("ldl_mgdl", "mg/dL"),
    ("triglycerides_mgdl", "mg/dL"),
    ("creatinine_umol", "umol/L"),
    ("report_date", None),
)


def to_neutral(output: PulperOutput) -> DocumentExtraction:
    fields: list[ExtractedField] = []
    for code, unit in _LAB_FIELDS:
        value = getattr(output.lab_values, code)
        if value is not None:
            fields.append(
                ExtractedField(
                    code=code,
                    value=value,
                    unit=unit,
                    confidence=output.confidence,
                )
            )

    if output.clinical_notes:
        fields.append(
            ExtractedField(
                code="clinical_notes",
                value=output.clinical_notes,
                confidence=output.confidence,
            )
        )

    records: list[ExtractedRecord] = []
    for reading in output.glucose_readings:
        reading_fields = [
            ExtractedField(
                code="value_mgdl",
                value=reading.value_mgdl,
                unit="mg/dL",
                confidence=output.confidence,
            )
        ]
        for code in ("timestamp", "context", "original_value", "original_unit"):
            value = getattr(reading, code)
            if value is not None:
                reading_fields.append(
                    ExtractedField(
                        code=code,
                        value=value,
                        confidence=output.confidence,
                    )
                )
        records.append(
            ExtractedRecord(
                record_type="glucose_reading",
                fields=tuple(reading_fields),
            )
        )

    for medication in output.medications:
        medication_fields = [
            ExtractedField(
                code="name",
                value=medication.name,
                confidence=output.confidence,
            )
        ]
        for code in ("dose", "frequency", "drug_type"):
            value = getattr(medication, code)
            if value is not None:
                medication_fields.append(
                    ExtractedField(
                        code=code,
                        value=value,
                        confidence=output.confidence,
                    )
                )
        records.append(
            ExtractedRecord(
                record_type="medication",
                fields=tuple(medication_fields),
            )
        )

    return DocumentExtraction(
        document_type=output.document_type,
        source_format=output.source_format,
        confidence=output.confidence,
        fields=tuple(fields),
        records=tuple(records),
        warnings=tuple(output.warnings),
        errors=tuple(output.errors),
        extracted_text=output.raw_text or None,
    )


def from_neutral(extraction: DocumentExtraction) -> PulperOutput:
    field_map = {item.code: item.value for item in extraction.fields}

    lab_values = LabValues(
        hba1c_pct=_optional_float(field_map.get("hba1c_pct")),
        fasting_glucose_mgdl=_optional_float(field_map.get("fasting_glucose_mgdl")),
        total_cholesterol_mgdl=_optional_float(field_map.get("total_cholesterol_mgdl")),
        hdl_mgdl=_optional_float(field_map.get("hdl_mgdl")),
        ldl_mgdl=_optional_float(field_map.get("ldl_mgdl")),
        triglycerides_mgdl=_optional_float(field_map.get("triglycerides_mgdl")),
        creatinine_umol=_optional_float(field_map.get("creatinine_umol")),
        report_date=_optional_str(field_map.get("report_date")),
    )

    readings: list[GlucoseReading] = []
    medications: list[MedicationEntry] = []

    for record in extraction.records:
        values = {item.code: item.value for item in record.fields}
        if record.record_type == "glucose_reading":
            value_mgdl = _optional_float(values.get("value_mgdl"))
            if value_mgdl is None:
                continue
            readings.append(
                GlucoseReading(
                    value_mgdl=value_mgdl,
                    timestamp=_optional_str(values.get("timestamp")),
                    context=_optional_str(values.get("context")),
                    original_value=_optional_float(values.get("original_value")),
                    original_unit=_optional_str(values.get("original_unit")),
                )
            )
        elif record.record_type == "medication":
            name = _optional_str(values.get("name"))
            if not name:
                continue
            medications.append(
                MedicationEntry(
                    name=name,
                    dose=_optional_str(values.get("dose")),
                    frequency=_optional_str(values.get("frequency")),
                    drug_type=_optional_str(values.get("drug_type")),
                )
            )

    return PulperOutput(
        document_type=extraction.document_type,
        source_format=extraction.source_format,
        confidence=extraction.confidence,
        glucose_readings=readings,
        lab_values=lab_values,
        medications=medications,
        clinical_notes=_optional_str(field_map.get("clinical_notes")) or "",
        raw_text=extraction.extracted_text or "",
        warnings=list(extraction.warnings),
        errors=list(extraction.errors),
    )


def _optional_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_str(value) -> str | None:
    if value is None:
        return None
    return str(value)
