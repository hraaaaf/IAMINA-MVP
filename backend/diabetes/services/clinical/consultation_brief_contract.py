"""Executable authority contract for clinician consultation briefs.

P2-DOCTOR starts with a deterministic structured contract before any new
clinician/patient UX or narrator integration. The contract deliberately carries
facts/derivations, provenance, comparison semantics and uncertainty only. It is
not a diagnosis, prescription, treatment plan or free-form clinical reasoning
surface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TypeAlias

from core.contracts.truth import TruthKind
from diabetes.services.clinical.evidence_registry import (
    ClinicalAuthority,
    RecordKind,
    get_evidence,
)

CONSULTATION_BRIEF_SCHEMA_VERSION = "consultation-brief.v1"
ConsultationScalar: TypeAlias = str | int | float | bool | None


class ConsultationComparisonBasis(str, Enum):
    """What the brief is allowed to claim about temporal change."""

    CURRENT_SNAPSHOT = "current_snapshot"
    SINCE_REVIEW_CHECKPOINT = "since_review_checkpoint"


class ConsultationChangeKind(str, Enum):
    """Bounded longitudinal semantics; never treatment response or causality."""

    CURRENT_STATE = "current_state"
    NEW_SINCE_REVIEW = "new_since_review"
    PERSISTING_SINCE_REVIEW = "persisting_since_review"
    IMPROVING_SINCE_REVIEW = "improving_since_review"
    RESOLVED_SINCE_REVIEW = "resolved_since_review"
    UNKNOWN = "unknown"


class ConsultationEvidenceDensity(str, Enum):
    """Repeatability density only; not probability or clinical confidence."""

    LIMITED = "limited"
    MODERATE = "moderate"
    STRONG = "strong"


class ConsultationNextStep(str, Enum):
    """Only non-prescriptive actions authorized by this contract."""

    MONITOR = "MONITOR"
    COLLECT_MISSING_DATA = "COLLECT_MISSING_DATA"
    PREPARE_CLINICIAN_DISCUSSION = "PREPARE_CLINICIAN_DISCUSSION"


class ConsultationAuthority(str, Enum):
    REVIEW_SUPPORT_ONLY = "clinician_review_support_only"


class ConsultationNarrationPolicy(str, Enum):
    APPROVED_STRUCTURED_FIELDS_ONLY = "approved_structured_fields_only"


_ALLOWED_TRUTH_KINDS = frozenset(
    {
        TruthKind.OBSERVED_FACT,
        TruthKind.DETERMINISTIC_DERIVATION,
    }
)

_CHANGE_KINDS_REQUIRING_REVIEW_CHECKPOINT = frozenset(
    {
        ConsultationChangeKind.NEW_SINCE_REVIEW,
        ConsultationChangeKind.PERSISTING_SINCE_REVIEW,
        ConsultationChangeKind.IMPROVING_SINCE_REVIEW,
        ConsultationChangeKind.RESOLVED_SINCE_REVIEW,
    }
)


def _require_nonempty_string(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _validate_string_tuple(name: str, values: object) -> None:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be an immutable tuple")
    for value in values:
        _require_nonempty_string(f"{name} item", value)


def _is_timezone_aware(value: object) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _validate_scalar(value: object) -> None:
    if type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("consultation evidence value must be an immutable scalar")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("consultation evidence float value must be finite")


def _validate_governed_evidence_id(evidence_id: str) -> None:
    try:
        record = get_evidence(evidence_id)
    except KeyError as exc:
        raise ValueError("consultation derivation evidence_id is not registered") from exc

    if record.kind is not RecordKind.RULE:
        raise ValueError("consultation derivation evidence_id must reference a product rule")
    if record.clinical_authority is not ClinicalAuthority.GOVERNED_RULE:
        raise ValueError(
            "consultation derivation requires governed_rule clinical authority"
        )


@dataclass(frozen=True)
class ConsultationReviewCheckpoint:
    """Explicit prior-review anchor required for any since-review statement."""

    reviewed_at: datetime
    source: str

    def __post_init__(self) -> None:
        _require_nonempty_string("review checkpoint source", self.source)
        if not _is_timezone_aware(self.reviewed_at):
            raise ValueError("review checkpoint reviewed_at must be timezone-aware")


@dataclass(frozen=True)
class ConsultationEvidenceItem:
    """One evidence-qualified fact or deterministic derivation in the brief."""

    key: str
    value: ConsultationScalar
    truth_kind: TruthKind
    source: str
    source_version: str
    change_kind: ConsultationChangeKind = ConsultationChangeKind.CURRENT_STATE
    unit: str | None = None
    evidence_id: str | None = None
    evidence_window_days: int | None = None
    evidence_density: ConsultationEvidenceDensity | None = None
    missing_data: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    allowed_next_step: ConsultationNextStep = ConsultationNextStep.MONITOR

    def __post_init__(self) -> None:
        _require_nonempty_string("consultation evidence key", self.key)
        _require_nonempty_string("consultation evidence source", self.source)
        _require_nonempty_string(
            "consultation evidence source_version",
            self.source_version,
        )
        _validate_scalar(self.value)
        _validate_string_tuple("consultation evidence missing_data", self.missing_data)
        _validate_string_tuple("consultation evidence limitations", self.limitations)

        if not isinstance(self.truth_kind, TruthKind):
            raise ValueError("consultation evidence truth_kind must be a TruthKind")
        if self.truth_kind not in _ALLOWED_TRUTH_KINDS:
            raise ValueError(
                f"{self.truth_kind.value} is not authorized for consultation brief truth"
            )
        if not isinstance(self.change_kind, ConsultationChangeKind):
            raise ValueError(
                "consultation evidence change_kind must be a ConsultationChangeKind"
            )
        if not isinstance(self.allowed_next_step, ConsultationNextStep):
            raise ValueError(
                "consultation evidence allowed_next_step must be a ConsultationNextStep"
            )
        if self.evidence_density is not None and not isinstance(
            self.evidence_density,
            ConsultationEvidenceDensity,
        ):
            raise ValueError(
                "consultation evidence evidence_density must be a ConsultationEvidenceDensity"
            )
        if self.unit is not None:
            _require_nonempty_string("consultation evidence unit", self.unit)

        if self.truth_kind is TruthKind.DETERMINISTIC_DERIVATION:
            if self.evidence_id is None:
                raise ValueError(
                    "deterministic consultation derivations require an evidence_id"
                )
            evidence_id = _require_nonempty_string(
                "deterministic consultation evidence_id",
                self.evidence_id,
            )
            _validate_governed_evidence_id(evidence_id)
        elif self.evidence_id is not None:
            raise ValueError("observed facts must not masquerade as governed derivations")

        if self.evidence_window_days is not None:
            if (
                type(self.evidence_window_days) is not int
                or self.evidence_window_days <= 0
            ):
                raise ValueError(
                    "evidence_window_days must be a positive integer when present"
                )
        if (
            self.evidence_density is not None
            and self.truth_kind is not TruthKind.DETERMINISTIC_DERIVATION
        ):
            raise ValueError(
                "evidence_density is reserved for approved deterministic derivations"
            )


@dataclass(frozen=True)
class ConsultationBriefEnvelope:
    """Structured clinician-review dossier that a narrator may only verbalize."""

    window_start: datetime
    window_end: datetime
    comparison_basis: ConsultationComparisonBasis
    items: tuple[ConsultationEvidenceItem, ...]
    review_checkpoint: ConsultationReviewCheckpoint | None = None
    missing_data: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    schema_version: str = CONSULTATION_BRIEF_SCHEMA_VERSION
    authority: ConsultationAuthority = ConsultationAuthority.REVIEW_SUPPORT_ONLY
    narration_policy: ConsultationNarrationPolicy = (
        ConsultationNarrationPolicy.APPROVED_STRUCTURED_FIELDS_ONLY
    )

    def __post_init__(self) -> None:
        if self.schema_version != CONSULTATION_BRIEF_SCHEMA_VERSION:
            raise ValueError("unsupported consultation brief schema version")
        if not isinstance(self.comparison_basis, ConsultationComparisonBasis):
            raise ValueError(
                "consultation brief comparison_basis must be a ConsultationComparisonBasis"
            )
        if not isinstance(self.authority, ConsultationAuthority):
            raise ValueError("consultation brief authority must be a ConsultationAuthority")
        if not isinstance(self.narration_policy, ConsultationNarrationPolicy):
            raise ValueError(
                "consultation brief narration_policy must be a ConsultationNarrationPolicy"
            )
        if not isinstance(self.items, tuple):
            raise ValueError("consultation brief items must be an immutable tuple")
        if not all(isinstance(item, ConsultationEvidenceItem) for item in self.items):
            raise ValueError(
                "consultation brief items must contain ConsultationEvidenceItem values"
            )
        _validate_string_tuple("consultation brief missing_data", self.missing_data)
        _validate_string_tuple("consultation brief limitations", self.limitations)

        if not _is_timezone_aware(self.window_start) or not _is_timezone_aware(
            self.window_end
        ):
            raise ValueError("consultation brief window datetimes must be timezone-aware")
        if self.window_start >= self.window_end:
            raise ValueError("consultation brief window_start must precede window_end")
        if self.comparison_basis is ConsultationComparisonBasis.CURRENT_SNAPSHOT:
            if self.review_checkpoint is not None:
                raise ValueError(
                    "current_snapshot must not carry a review checkpoint or imply change"
                )
            for item in self.items:
                if item.change_kind in _CHANGE_KINDS_REQUIRING_REVIEW_CHECKPOINT:
                    raise ValueError(
                        "since-review change claims require an explicit review checkpoint"
                    )
        elif self.comparison_basis is ConsultationComparisonBasis.SINCE_REVIEW_CHECKPOINT:
            if not isinstance(self.review_checkpoint, ConsultationReviewCheckpoint):
                raise ValueError(
                    "since_review_checkpoint requires an explicit review checkpoint"
                )
            if self.review_checkpoint.reviewed_at >= self.window_end:
                raise ValueError("review checkpoint must precede the brief window end")

    @property
    def has_since_review_claims(self) -> bool:
        return any(
            item.change_kind in _CHANGE_KINDS_REQUIRING_REVIEW_CHECKPOINT
            for item in self.items
        )

    @property
    def can_be_narrated_by_model(self) -> bool:
        """Narration is allowed only as reformulation of this approved envelope."""

        return (
            self.authority is ConsultationAuthority.REVIEW_SUPPORT_ONLY
            and self.narration_policy
            is ConsultationNarrationPolicy.APPROVED_STRUCTURED_FIELDS_ONLY
        )
