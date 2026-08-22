"""Diabetes adapters into the chassis-owned CanonicalClinicalFact contract."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from core.contracts.clinical_fact import (
    UCUM_SYSTEM,
    CanonicalClinicalFact,
    ClinicalFactDecision,
    ClinicalFactProvenance,
    ClinicalFactSource,
)
from core.contracts.document_extraction import (
    DocumentExtraction,
    ExtractedField,
    ExtractedRecord,
    ExtractionDecision,
)
from diabetes.models.cgm import CGMReadingRecord
from diabetes.models.entry import LogEntry

_ADAPTER = "diabetes-canonical-facts"
_ADAPTER_VERSION = "1"
_SOURCE_MAP = {
    "manual": ClinicalFactSource.MANUAL,
    "voice": ClinicalFactSource.VOICE,
    "cgm": ClinicalFactSource.CGM,
    "import": ClinicalFactSource.IMPORT,
    "demo": ClinicalFactSource.DEMO,
}
_DECISION_MAP = {
    ExtractionDecision.ACCEPTED: ClinicalFactDecision.ACCEPTED,
    ExtractionDecision.REVIEW_REQUIRED: ClinicalFactDecision.REVIEW_REQUIRED,
    ExtractionDecision.REJECTED: ClinicalFactDecision.REJECTED,
}
_CANONICAL_UCUM_UNITS = frozenset({"mg/dL", "%", "umol/L"})
_LAB_CONCEPTS = {
    "hba1c_pct": ("hba1c", "%"),
    "fasting_glucose_mgdl": ("glucose", "mg/dL"),
    "total_cholesterol_mgdl": ("total_cholesterol", "mg/dL"),
    "hdl_mgdl": ("hdl_cholesterol", "mg/dL"),
    "ldl_mgdl": ("ldl_cholesterol", "mg/dL"),
    "triglycerides_mgdl": ("triglycerides", "mg/dL"),
    "creatinine_umol": ("creatinine", "umol/L"),
}


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _number(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _subject(patient_id: int | str) -> str:
    return f"patient:{patient_id}"


def _decision(value: ExtractionDecision) -> ClinicalFactDecision:
    return _DECISION_MAP[value]


def _combined_decision(*values: ExtractionDecision) -> ClinicalFactDecision:
    """Use the most conservative decision among fields actually used by a fact."""
    if ExtractionDecision.REJECTED in values:
        return ClinicalFactDecision.REJECTED
    if ExtractionDecision.REVIEW_REQUIRED in values:
        return ClinicalFactDecision.REVIEW_REQUIRED
    return ClinicalFactDecision.ACCEPTED


def _provenance(
    source_ref: str,
    *,
    source_sha256: str | None = None,
    raw_value=None,
    extractor: str | None = None,
    extractor_version: str | None = None,
    schema_version: str | None = None,
    extractor_model: str | None = None,
    parser_model: str | None = None,
    prompt_version: str | None = None,
    evidence_verified: bool = False,
) -> ClinicalFactProvenance:
    return ClinicalFactProvenance(
        source_ref=source_ref,
        source_sha256=source_sha256,
        adapter=_ADAPTER,
        adapter_version=_ADAPTER_VERSION,
        raw_value=None if raw_value is None else str(raw_value),
        extractor=extractor,
        extractor_version=extractor_version,
        schema_version=schema_version,
        extractor_model=extractor_model,
        parser_model=parser_model,
        prompt_version=prompt_version,
        evidence_verified=evidence_verified,
    )


def from_log_entry(log: LogEntry) -> CanonicalClinicalFact:
    """Map manual, voice, imported or legacy log glucose to one fact."""
    source_type = _SOURCE_MAP.get(log.source, ClinicalFactSource.API)
    source_ref = f"log_entry:{log.pk or log.client_uuid or 'pending'}"
    return CanonicalClinicalFact(
        subject_ref=_subject(log.patient_id),
        concept="glucose",
        value=float(log.blood_sugar),
        unit="mg/dL",
        unit_system=UCUM_SYSTEM,
        effective_at=_iso(log.effective_time),
        source_type=source_type,
        source_ref=source_ref,
        decision=ClinicalFactDecision.ACCEPTED,
        context=log.glycemic_context or log.meal_type or None,
        provenance=_provenance(source_ref),
    )


def from_cgm_reading(reading: CGMReadingRecord) -> CanonicalClinicalFact:
    """Map a normalized live CGM transport row without changing its value."""
    source_ref = f"cgm:{reading.source}:{reading.dedupe_key}"
    return CanonicalClinicalFact(
        subject_ref=_subject(reading.patient_id),
        concept="glucose",
        value=int(reading.glucose_mg_dl),
        unit="mg/dL",
        unit_system=UCUM_SYSTEM,
        effective_at=_iso(reading.recorded_at),
        source_type=ClinicalFactSource.CGM,
        source_ref=source_ref,
        decision=ClinicalFactDecision.ACCEPTED,
        attributes={
            "provider": reading.source,
            "trend": reading.trend or "",
            "device": reading.device or "",
        },
        provenance=_provenance(source_ref, evidence_verified=True),
    )


def from_document_extraction(
    extraction: DocumentExtraction,
    *,
    patient_id: int | str,
    source_ref: str | None = None,
) -> tuple[CanonicalClinicalFact, ...]:
    """Map Pulper neutral output to facts without inventing LOINC semantics."""
    root_ref = source_ref or "document:pending"
    facts: list[CanonicalClinicalFact] = []
    report_date_field = extraction.field("report_date")
    report_date = (
        _iso(report_date_field.value)
        if report_date_field
        and report_date_field.decision is not ExtractionDecision.REJECTED
        else None
    )
    report_date_decisions = (
        (report_date_field.decision,)
        if report_date_field is not None and report_date is not None
        else ()
    )

    for field in extraction.fields:
        mapped = _LAB_CONCEPTS.get(field.code)
        if mapped is None:
            continue
        concept, unit = mapped
        facts.append(
            _fact_from_extracted_field(
                field,
                patient_id=patient_id,
                concept=concept,
                unit=unit,
                effective_at=report_date,
                fallback_ref=f"{root_ref}:{field.code}",
                fallback_confidence=extraction.confidence,
                supporting_decisions=report_date_decisions,
            )
        )

    for index, record in enumerate(extraction.records):
        if record.record_type == "glucose_reading":
            fact = _glucose_record_fact(
                record,
                patient_id=patient_id,
                fallback_ref=f"{root_ref}:glucose:{index}",
                fallback_confidence=extraction.confidence,
            )
            if fact is not None:
                facts.append(fact)
        elif record.record_type == "medication":
            fact = _medication_record_fact(
                record,
                patient_id=patient_id,
                fallback_ref=f"{root_ref}:medication:{index}",
                fallback_confidence=extraction.confidence,
            )
            if fact is not None:
                facts.append(fact)

    return tuple(facts)


def _field_map(record: ExtractedRecord) -> dict[str, ExtractedField]:
    return {field.code: field for field in record.fields}


def _fact_from_extracted_field(
    field: ExtractedField,
    *,
    patient_id: int | str,
    concept: str,
    unit: str | None,
    effective_at: str | None,
    fallback_ref: str,
    fallback_confidence: float,
    context: str | None = None,
    attributes: dict | None = None,
    supporting_decisions: tuple[ExtractionDecision, ...] = (),
) -> CanonicalClinicalFact:
    source_ref = field.source_ref or fallback_ref
    prov = field.provenance
    resolved_unit = field.unit or unit
    return CanonicalClinicalFact(
        subject_ref=_subject(patient_id),
        concept=concept,
        value=_number(field.value),
        unit=resolved_unit,
        unit_system=(
            UCUM_SYSTEM if resolved_unit in _CANONICAL_UCUM_UNITS else None
        ),
        effective_at=effective_at,
        source_type=ClinicalFactSource.DOCUMENT,
        source_ref=source_ref,
        confidence=field.confidence if field.confidence is not None else fallback_confidence,
        decision=_combined_decision(field.decision, *supporting_decisions),
        context=context,
        attributes=attributes or {},
        provenance=_provenance(
            source_ref,
            source_sha256=prov.source_sha256 if prov else None,
            raw_value=field.raw_value,
            extractor=prov.extractor if prov else None,
            extractor_version=prov.extractor_version if prov else None,
            schema_version=prov.schema_version if prov else None,
            extractor_model=prov.extractor_model if prov else None,
            parser_model=prov.parser_model if prov else None,
            prompt_version=prov.prompt_version if prov else None,
            evidence_verified=bool(prov and prov.evidence_verified),
        ),
    )


def _glucose_record_fact(
    record: ExtractedRecord,
    *,
    patient_id: int | str,
    fallback_ref: str,
    fallback_confidence: float,
) -> CanonicalClinicalFact | None:
    fields = _field_map(record)
    value = fields.get("value_mgdl")
    if value is None:
        return None
    timestamp = fields.get("timestamp")
    context = fields.get("context")
    original_value = fields.get("original_value")
    original_unit = fields.get("original_unit")
    timestamp = (
        timestamp
        if timestamp and timestamp.decision is not ExtractionDecision.REJECTED
        else None
    )
    context = (
        context
        if context and context.decision is not ExtractionDecision.REJECTED
        else None
    )
    original_value = (
        original_value
        if original_value and original_value.decision is not ExtractionDecision.REJECTED
        else None
    )
    original_unit = (
        original_unit
        if original_unit and original_unit.decision is not ExtractionDecision.REJECTED
        else None
    )
    used_supporting_fields = tuple(
        field
        for field in (timestamp, context, original_value, original_unit)
        if field is not None
    )
    attributes = {}
    if original_value is not None:
        attributes["original_value"] = _number(original_value.value)
    if original_unit is not None:
        attributes["original_unit"] = str(original_unit.value)
    return _fact_from_extracted_field(
        value,
        patient_id=patient_id,
        concept="glucose",
        unit="mg/dL",
        effective_at=_iso(timestamp.value) if timestamp else None,
        fallback_ref=fallback_ref,
        fallback_confidence=fallback_confidence,
        context=_iso(context.value) if context else None,
        attributes=attributes,
        supporting_decisions=tuple(
            field.decision for field in used_supporting_fields
        ),
    )


def _medication_record_fact(
    record: ExtractedRecord,
    *,
    patient_id: int | str,
    fallback_ref: str,
    fallback_confidence: float,
) -> CanonicalClinicalFact | None:
    fields = _field_map(record)
    name = fields.get("name")
    if name is None or not str(name.value).strip():
        return None
    source_ref = name.source_ref or fallback_ref
    included_attributes = tuple(
        field
        for code in ("dose", "frequency", "drug_type")
        if (field := fields.get(code)) is not None
        and field.decision is not ExtractionDecision.REJECTED
    )
    attributes = {field.code: _number(field.value) for field in included_attributes}
    return CanonicalClinicalFact(
        subject_ref=_subject(patient_id),
        concept="medication",
        value=str(name.value),
        source_type=ClinicalFactSource.DOCUMENT,
        source_ref=source_ref,
        confidence=name.confidence if name.confidence is not None else fallback_confidence,
        decision=_combined_decision(
            name.decision,
            *(field.decision for field in included_attributes),
        ),
        attributes=attributes,
        provenance=_provenance(
            source_ref,
            source_sha256=name.provenance.source_sha256 if name.provenance else None,
            raw_value=name.raw_value,
            extractor=name.provenance.extractor if name.provenance else None,
            extractor_version=(
                name.provenance.extractor_version if name.provenance else None
            ),
            schema_version=name.provenance.schema_version if name.provenance else None,
            extractor_model=name.provenance.extractor_model if name.provenance else None,
            parser_model=name.provenance.parser_model if name.provenance else None,
            prompt_version=name.provenance.prompt_version if name.provenance else None,
            evidence_verified=bool(name.provenance and name.provenance.evidence_verified),
        ),
    )
