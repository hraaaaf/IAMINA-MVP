"""Compatibility adapter between the chassis document contract and diabetes.

This module is intentionally condition-owned. The chassis contract never imports
this module or any diabetes type.
"""
from __future__ import annotations

from core.contracts.document_extraction import (
    DocumentExtraction,
    ExtractedField,
    ExtractedRecord,
    FieldProvenance,
)
from diabetes.services.documents.schema import (
    FieldEvidence,
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
                _to_field(
                    output,
                    code=code,
                    value=value,
                    unit=unit,
                    evidence=output.lab_values.evidence.get(code),
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
            _to_field(
                output,
                code="value_mgdl",
                value=reading.value_mgdl,
                unit="mg/dL",
                evidence=reading.evidence.get("value_mgdl"),
            )
        ]
        for code in ("timestamp", "context", "original_value", "original_unit"):
            value = getattr(reading, code)
            if value is not None:
                reading_fields.append(
                    _to_field(
                        output,
                        code=code,
                        value=value,
                        evidence=reading.evidence.get(code),
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
            _to_field(
                output,
                code="name",
                value=medication.name,
                evidence=medication.evidence.get("name"),
            )
        ]
        for code in ("dose", "frequency", "drug_type"):
            value = getattr(medication, code)
            if value is not None:
                medication_fields.append(
                    _to_field(
                        output,
                        code=code,
                        value=value,
                        evidence=medication.evidence.get(code),
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
    field_items = {item.code: item for item in extraction.fields}
    field_map = {code: item.value for code, item in field_items.items()}

    lab_values = LabValues(
        hba1c_pct=_optional_float(field_map.get("hba1c_pct")),
        fasting_glucose_mgdl=_optional_float(field_map.get("fasting_glucose_mgdl")),
        total_cholesterol_mgdl=_optional_float(
            field_map.get("total_cholesterol_mgdl")
        ),
        hdl_mgdl=_optional_float(field_map.get("hdl_mgdl")),
        ldl_mgdl=_optional_float(field_map.get("ldl_mgdl")),
        triglycerides_mgdl=_optional_float(field_map.get("triglycerides_mgdl")),
        creatinine_umol=_optional_float(field_map.get("creatinine_umol")),
        report_date=_optional_str(field_map.get("report_date")),
        evidence={
            code: evidence
            for code, item in field_items.items()
            if code in {name for name, _ in _LAB_FIELDS}
            if (evidence := _from_field_evidence(item)) is not None
        },
    )

    readings: list[GlucoseReading] = []
    medications: list[MedicationEntry] = []

    for record in extraction.records:
        items = {item.code: item for item in record.fields}
        values = {code: item.value for code, item in items.items()}
        evidence = {
            code: converted
            for code, item in items.items()
            if (converted := _from_field_evidence(item)) is not None
        }

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
                    evidence=evidence,
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
                    evidence=evidence,
                )
            )

    provenance = _first_provenance(extraction)

    return PulperOutput(
        document_type=extraction.document_type,
        source_format=extraction.source_format,
        confidence=extraction.confidence,
        glucose_readings=readings,
        lab_values=lab_values,
        medications=medications,
        clinical_notes=_optional_str(field_map.get("clinical_notes")) or "",
        source_sha256=provenance.source_sha256 if provenance else "",
        extractor=provenance.extractor if provenance else "",
        extractor_version=provenance.extractor_version if provenance else "",
        extractor_model=provenance.extractor_model if provenance else None,
        schema_version=provenance.schema_version if provenance else "pulper-output-v2",
        parser_model=provenance.parser_model if provenance else None,
        prompt_version=provenance.prompt_version if provenance else None,
        raw_text=extraction.extracted_text or "",
        warnings=list(extraction.warnings),
        errors=list(extraction.errors),
    )


def provenance_snapshot(output: PulperOutput) -> dict:
    """Compact persisted evidence; intentionally excludes the full extracted text."""
    if not output.source_sha256:
        return {}

    fields: dict[str, dict] = {}
    for code, _ in _LAB_FIELDS:
        value = getattr(output.lab_values, code)
        evidence = output.lab_values.evidence.get(code)
        if value is not None and evidence is not None:
            fields[f"lab_values.{code}"] = _evidence_payload(value, evidence)

    records: list[dict] = []
    for index, reading in enumerate(output.glucose_readings):
        record_fields: dict[str, dict] = {}
        for code in ("value_mgdl", "timestamp", "context", "original_value", "original_unit"):
            value = getattr(reading, code)
            evidence = reading.evidence.get(code)
            if value is not None and evidence is not None:
                record_fields[code] = _evidence_payload(value, evidence)
        if record_fields:
            records.append(
                {
                    "record_type": "glucose_reading",
                    "index": index,
                    "fields": record_fields,
                }
            )

    for index, medication in enumerate(output.medications):
        record_fields = {}
        for code in ("name", "dose", "frequency", "drug_type"):
            value = getattr(medication, code)
            evidence = medication.evidence.get(code)
            if value is not None and evidence is not None:
                record_fields[code] = _evidence_payload(value, evidence)
        if record_fields:
            records.append(
                {
                    "record_type": "medication",
                    "index": index,
                    "fields": record_fields,
                }
            )

    return {
        "source_sha256": output.source_sha256,
        "extractor": output.extractor,
        "extractor_version": output.extractor_version,
        "extractor_model": output.extractor_model,
        "schema_version": output.schema_version,
        "parser_model": output.parser_model,
        "prompt_version": output.prompt_version,
        "fields": fields,
        "records": records,
    }


def _to_field(
    output: PulperOutput,
    *,
    code: str,
    value,
    unit: str | None = None,
    evidence: FieldEvidence | None = None,
) -> ExtractedField:
    provenance = _to_field_provenance(output, evidence)
    return ExtractedField(
        code=code,
        value=value,
        unit=unit,
        confidence=output.confidence,
        source_ref=evidence.source_ref if evidence else None,
        raw_value=evidence.raw_value if evidence else None,
        provenance=provenance,
    )


def _to_field_provenance(
    output: PulperOutput,
    evidence: FieldEvidence | None,
) -> FieldProvenance | None:
    if (
        evidence is None
        or not evidence.source_ref
        or not output.source_sha256
        or not output.extractor
        or not output.extractor_version
        or not output.schema_version
    ):
        return None

    return FieldProvenance(
        source_sha256=output.source_sha256,
        source_ref=evidence.source_ref,
        extractor=output.extractor,
        extractor_version=output.extractor_version,
        extractor_model=output.extractor_model,
        schema_version=output.schema_version,
        parser_model=output.parser_model,
        prompt_version=output.prompt_version,
        evidence_verified=evidence.verified,
    )


def _from_field_evidence(field: ExtractedField) -> FieldEvidence | None:
    if field.raw_value is None and field.source_ref is None:
        return None
    return FieldEvidence(
        raw_value=None if field.raw_value is None else str(field.raw_value),
        source_ref=field.source_ref,
        verified=bool(field.provenance and field.provenance.evidence_verified),
    )


def _first_provenance(extraction: DocumentExtraction) -> FieldProvenance | None:
    for field in extraction.fields:
        if field.provenance is not None:
            return field.provenance
    for record in extraction.records:
        for field in record.fields:
            if field.provenance is not None:
                return field.provenance
    return None


def _evidence_payload(value, evidence: FieldEvidence) -> dict:
    return {
        "normalized_value": value,
        "raw_value": evidence.raw_value,
        "source_ref": evidence.source_ref,
        "evidence_verified": evidence.verified,
    }


def _optional_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_str(value) -> str | None:
    if value is None:
        return None
    return str(value)
