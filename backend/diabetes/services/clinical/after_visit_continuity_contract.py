"""Bounded P2-COMPANION-6 after-visit continuity contract.

This module records explicit post-consultation facts and descriptive interval state.
It never infers treatment efficacy, diagnosis, causality, dosing or treatment changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import isfinite


class AfterVisitFactKind(StrEnum):
    PATIENT_RECORDED = "patient_recorded"
    CLINICIAN_RECORDED = "clinician_recorded"
    GOVERNED_DERIVATION = "governed_derivation"


class AfterVisitChangeKind(StrEnum):
    CURRENT_STATE = "current_state"
    NEW_SINCE_VISIT = "new_since_visit"
    PERSISTING_SINCE_VISIT = "persisting_since_visit"
    IMPROVING_DESCRIPTIVELY = "improving_descriptively"
    RESOLVED_SINCE_VISIT = "resolved_since_visit"
    UNKNOWN = "unknown"


class AfterVisitNextStep(StrEnum):
    MONITOR = "monitor"
    COLLECT_MISSING_DATA = "collect_missing_data"
    FOLLOW_UP_RECORD = "follow_up_record"
    PREPARE_CLINICIAN_DISCUSSION = "prepare_clinician_discussion"


@dataclass(frozen=True, slots=True)
class VisitAnchor:
    occurred_at: datetime
    source: str

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("visit anchor must be timezone-aware")
        if not self.source.strip():
            raise ValueError("visit anchor source is required")


@dataclass(frozen=True, slots=True)
class AfterVisitFact:
    key: str
    value: str | int | float | bool
    fact_kind: AfterVisitFactKind
    source: str
    recorded_at: datetime
    change_kind: AfterVisitChangeKind = AfterVisitChangeKind.CURRENT_STATE
    allowed_next_step: AfterVisitNextStep = AfterVisitNextStep.MONITOR
    evidence_id: str | None = None
    missing_data: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.source.strip():
            raise ValueError("fact key and source are required")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("fact timestamp must be timezone-aware")
        if isinstance(self.value, float) and not isfinite(self.value):
            raise ValueError("numeric fact value must be finite")
        if self.fact_kind is AfterVisitFactKind.GOVERNED_DERIVATION and not self.evidence_id:
            raise ValueError("governed derivation requires evidence_id")
        if self.change_kind is AfterVisitChangeKind.UNKNOWN:
            if self.allowed_next_step is not AfterVisitNextStep.COLLECT_MISSING_DATA:
                raise ValueError("unknown change may only collect missing data")
            if not self.missing_data:
                raise ValueError("unknown change requires explicit missing data")
        if self.allowed_next_step is AfterVisitNextStep.PREPARE_CLINICIAN_DISCUSSION:
            if self.fact_kind is not AfterVisitFactKind.CLINICIAN_RECORDED:
                raise ValueError(
                    "clinician discussion authority requires an explicit clinician-recorded fact"
                )


@dataclass(frozen=True, slots=True)
class AfterVisitContinuityEnvelope:
    visit_anchor: VisitAnchor
    window_end: datetime
    facts: tuple[AfterVisitFact, ...]
    missing_data: tuple[str, ...] = ()
    limitations: tuple[str, ...] = (
        "continuity_record_only",
        "temporal_association_is_not_treatment_efficacy",
        "clinician_remains_medical_decision_authority",
        "no_diagnosis_prescription_dose_or_treatment_change_authority",
    )

    def __post_init__(self) -> None:
        if self.window_end.tzinfo is None or self.window_end.utcoffset() is None:
            raise ValueError("window_end must be timezone-aware")
        if self.window_end <= self.visit_anchor.occurred_at:
            raise ValueError("window_end must follow visit anchor")
        for fact in self.facts:
            if not (self.visit_anchor.occurred_at <= fact.recorded_at <= self.window_end):
                raise ValueError("after-visit fact falls outside continuity window")


__all__ = [
    "AfterVisitChangeKind",
    "AfterVisitContinuityEnvelope",
    "AfterVisitFact",
    "AfterVisitFactKind",
    "AfterVisitNextStep",
    "VisitAnchor",
]
