"""Disease-neutral structured document extraction contracts.

The chassis may describe what was extracted and how certain the extraction was,
but it must not encode diabetes, hypertension, nutrition, or other condition
semantics. Condition modules translate these generic records through adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

ScalarValue: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class ExtractedField:
    code: str
    value: ScalarValue
    unit: str | None = None
    confidence: float | None = None
    verified: bool = False
    source_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("field code is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("field confidence must be between 0 and 1")


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

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("document confidence must be between 0 and 1")

    def field(self, code: str) -> ExtractedField | None:
        return next((item for item in self.fields if item.code == code), None)

    def records_of_type(self, record_type: str) -> tuple[ExtractedRecord, ...]:
        return tuple(item for item in self.records if item.record_type == record_type)
