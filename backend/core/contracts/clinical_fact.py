"""Disease-neutral canonical clinical fact contract.

IAMINA keeps this contract deliberately smaller than FHIR while preserving the
pieces required for lossless interoperability mappings: subject, coded concept,
value, UCUM unit, clinically relevant time, source/provenance, confidence and
review decision.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from string import hexdigits
from types import MappingProxyType
from typing import Any, Mapping

LOINC_SYSTEM = "http://loinc.org"
UCUM_SYSTEM = "http://unitsofmeasure.org"


class ClinicalFactSource(StrEnum):
    DOCUMENT = "document"
    CGM = "cgm"
    MANUAL = "manual"
    API = "api"
    IMPORT = "import"
    VOICE = "voice"
    DEMO = "demo"


class ClinicalFactDecision(StrEnum):
    ACCEPTED = "accepted"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ClinicalCoding:
    """Optional interoperable coding for the clinical concept."""

    system: str
    code: str
    display: str | None = None

    def __post_init__(self) -> None:
        if not self.system.strip():
            raise ValueError("coding system is required")
        if not self.code.strip():
            raise ValueError("coding code is required")
        if self.display is not None and not self.display.strip():
            raise ValueError("coding display cannot be blank")


@dataclass(frozen=True, slots=True)
class ClinicalFactProvenance:
    """Traceability for one normalized fact without retaining raw documents."""

    source_ref: str
    adapter: str
    adapter_version: str
    source_sha256: str | None = None
    raw_value: str | None = None
    extractor: str | None = None
    extractor_version: str | None = None
    schema_version: str | None = None
    extractor_model: str | None = None
    parser_model: str | None = None
    prompt_version: str | None = None
    evidence_verified: bool = False

    def __post_init__(self) -> None:
        if not self.source_ref.strip():
            raise ValueError("source_ref is required")
        if not self.adapter.strip():
            raise ValueError("adapter is required")
        if not self.adapter_version.strip():
            raise ValueError("adapter_version is required")
        for name in (
            "extractor",
            "extractor_version",
            "schema_version",
            "extractor_model",
            "parser_model",
            "prompt_version",
        ):
            value = getattr(self, name)
            if value is not None and not value.strip():
                raise ValueError(f"{name} cannot be blank")
        if self.source_sha256 is not None:
            digest = self.source_sha256.strip().lower()
            if len(digest) != 64 or any(char not in hexdigits for char in digest):
                raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
            object.__setattr__(self, "source_sha256", digest)


@dataclass(frozen=True, slots=True)
class CanonicalClinicalFact:
    """One patient-linked clinical fact after source normalization."""

    subject_ref: str
    concept: str
    value: Any
    source_type: ClinicalFactSource
    source_ref: str
    effective_at: str | None = None
    unit: str | None = None
    unit_system: str | None = None
    codings: tuple[ClinicalCoding, ...] = ()
    confidence: float = 1.0
    decision: ClinicalFactDecision = ClinicalFactDecision.REVIEW_REQUIRED
    context: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: ClinicalFactProvenance | None = None

    def __post_init__(self) -> None:
        if not self.subject_ref.strip():
            raise ValueError("subject_ref is required")
        if not self.concept.strip():
            raise ValueError("concept is required")
        if not self.source_ref.strip():
            raise ValueError("source_ref is required")
        if not isinstance(self.source_type, ClinicalFactSource):
            raise ValueError("source_type must be a ClinicalFactSource")
        if not isinstance(self.decision, ClinicalFactDecision):
            raise ValueError("decision must be a ClinicalFactDecision")
        if isinstance(self.confidence, bool) or not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.effective_at is not None and not self.effective_at.strip():
            raise ValueError("effective_at cannot be blank")
        if self.unit is not None and not self.unit.strip():
            raise ValueError("unit cannot be blank")
        if self.unit is None and self.unit_system is not None:
            raise ValueError("unit_system requires unit")
        if self.unit_system is not None and not self.unit_system.strip():
            raise ValueError("unit_system cannot be blank")
        if self.provenance is not None and self.provenance.source_ref != self.source_ref:
            raise ValueError("provenance source_ref conflicts with fact source_ref")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))
