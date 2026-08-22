"""Disease-neutral structured document extraction contracts.

The chassis may describe what was extracted and how certain the extraction was,
but it must not encode diabetes, hypertension, nutrition, or other condition
semantics. Condition modules translate these generic records through adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from string import hexdigits
from typing import TypeAlias

ScalarValue: TypeAlias = str | int | float | bool | None


class ExtractionStage(str, Enum):
    """Lifecycle stage reached by a neutral document extraction."""

    EXTRACTED = "extracted"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    DECIDED = "decided"
    PERSISTED = "persisted"


class ExtractionDecision(str, Enum):
    """Neutral disposition for an extracted field."""

    ACCEPTED = "accepted"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class FieldProvenance:
    """Disease-neutral evidence metadata for one extracted field."""

    source_sha256: str
    source_ref: str
    extractor: str
    extractor_version: str
    schema_version: str
    extractor_model: str | None = None
    parser_model: str | None = None
    prompt_version: str | None = None
    evidence_verified: bool = False

    def __post_init__(self) -> None:
        digest = self.source_sha256.strip().lower()
        if len(digest) != 64 or any(char not in hexdigits for char in digest):
            raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
        object.__setattr__(self, "source_sha256", digest)

        for name in (
            "source_ref",
            "extractor",
            "extractor_version",
            "schema_version",
        ):
            value = getattr(self, name)
            if not value.strip():
                raise ValueError(f"{name} is required")

        for name in ("extractor_model", "parser_model", "prompt_version"):
            value = getattr(self, name)
            if value is not None and not value.strip():
                raise ValueError(f"{name} cannot be blank")


@dataclass(frozen=True, slots=True)
class ExtractedField:
    code: str
    value: ScalarValue
    unit: str | None = None
    confidence: float | None = None
    verified: bool = False
    source_ref: str | None = None
    decision: ExtractionDecision = ExtractionDecision.REVIEW_REQUIRED
    decision_reason: str | None = None
    raw_value: ScalarValue = None
    provenance: FieldProvenance | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("field code is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("field confidence must be between 0 and 1")
        if not isinstance(self.decision, ExtractionDecision):
            raise ValueError("field decision must be an ExtractionDecision")
        if self.decision_reason is not None and not self.decision_reason.strip():
            raise ValueError("field decision_reason cannot be blank")

        if self.provenance is not None:
            if self.source_ref is None:
                object.__setattr__(self, "source_ref", self.provenance.source_ref)
            elif self.source_ref != self.provenance.source_ref:
                raise ValueError("field source_ref conflicts with provenance source_ref")

        if self.verified:
            if self.decision is ExtractionDecision.REJECTED:
                raise ValueError("a verified field cannot be rejected")
            if self.decision is ExtractionDecision.REVIEW_REQUIRED:
                object.__setattr__(self, "decision", ExtractionDecision.ACCEPTED)


@dataclass(frozen=True, slots=True)
class ExtractedRecord:
    record_type: str
    fields: tuple[ExtractedField, ...] = ()
    source_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.record_type.strip():
            raise ValueError("record_type is required")


@dataclass(frozen=True, slots=True)
class DocumentExtraction:
    document_type: str
    source_format: str
    confidence: float
    fields: tuple[ExtractedField, ...] = ()
    records: tuple[ExtractedRecord, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    extracted_text: str | None = None
    stage: ExtractionStage = ExtractionStage.EXTRACTED

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("document confidence must be between 0 and 1")
        if not isinstance(self.stage, ExtractionStage):
            raise ValueError("document stage must be an ExtractionStage")

    def field(self, code: str) -> ExtractedField | None:
        return next((item for item in self.fields if item.code == code), None)

    def records_of_type(self, record_type: str) -> tuple[ExtractedRecord, ...]:
        return tuple(item for item in self.records if item.record_type == record_type)
