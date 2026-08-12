"""Executable authority contract for clinician consultation briefs.

P2-DOCTOR starts with a deterministic structured contract before any new
clinician/patient UX or narrator integration.  The contract deliberately carries
facts/derivations, provenance, comparison semantics and uncertainty only.  It is
not a diagnosis, prescription, treatment plan or free-form clinical reasoning
surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from core.contracts.truth import TruthKind

CONSULTATION_BRIEF_SCHEMA_VERSION = "consultation-brief.v1"


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


@dataclass(frozen=True)
class ConsultationReviewCheckpoint:
    """Explicit prior-review anchor required for any since-review statement."""

    reviewed_at: datetime
    source: str

    def __post_init__(self) -> None:
        if not self.source or not self.source.strip():
            raise ValueError("review checkpoint source is required")


@dataclass(frozen=True)
class ConsultationEvidenceItem:
    """One evidence-qualified fact or deterministic derivation in the brief."""

    key: str
    value: Any
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
        if not self.key or not self.key.strip():
            raise ValueError("consultation evidence key is required")
        if not self.source or not self.source.strip():
            raise ValueError("consultation evidence source is required")
        if not self.source_version or not self.source_version.strip():
            raise ValueError("consultation evidence source_version is required")
        if self.truth_kind not in _ALLOWED_TRUTH_KINDS:
            raise ValueError(
                f"{self.truth_kind.value} is not authorized for consultation brief truth"
            )
        if self.truth_kind is TruthKind.DETERMINISTIC_DERIVATION:
            if not self.evidence_id or not self.evidence_id.strip():
                raise ValueError(
                    "deterministic consultation derivations require an evidence_id"
                )
        elif self.evidence_id is not None:
            raise ValueError("observed facts must not masquerade as governed derivations")
        if self.evidence_window_days is not None and self.evidence_window_days <= 0:
            raise ValueError("evidence_window_days must be positive when present")
        if self.evidence_density is not None and self.truth_kind is not TruthKind.DETERMINISTIC_DERIVATION:
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
            if self.review_checkpoint is None:
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
