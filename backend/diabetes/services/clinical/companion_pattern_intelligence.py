"""Deterministic patient-companion projection of governed Clinical Twin patterns.

This module does not detect new patterns and does not create clinical truth. It
projects already-governed ``ClinicalObservationState`` rows into a bounded,
auditable structure that a later companion surface may explain. The projection
contains descriptive longitudinal semantics only: first observed, recurrence,
persistence, descriptive movement relative to the patient's own eligible window
baseline, resolution, evidence density and provenance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.services.clinical.companion_evidence_uncertainty import (
    CompanionEvidenceContext,
    build_companion_evidence_context,
)
from diabetes.services.clinical.personal_response import (
    MAX_WINDOW_DAYS,
    MIN_DISTINCT_DAYS,
    MIN_OBSERVATIONS,
)

PatternCurrentState = Literal["active", "resolved"]
BaselineDirection = Literal[
    "above_personal_window_baseline",
    "aligned_with_personal_window_baseline",
    "below_personal_window_baseline",
]
BaselineMovement = Literal[
    "initial_or_unknown",
    "toward_personal_window_baseline",
    "stable_relative_to_personal_window_baseline",
    "away_from_personal_window_baseline",
]
PatternMarker = Literal[
    "persisting",
    "recurring",
    "improving_descriptively",
    "resolved",
]
ProjectionStatus = Literal["ready", "no_governed_patterns"]

SOURCE_VERSION = "companion-personal-pattern-intelligence.v1"

_COMMON_LIMITATIONS = (
    "observational_association_only",
    "personal_window_baseline_is_descriptive_not_a_clinical_target",
    "evidence_density_is_repeatability_not_probability_or_clinical_confidence",
    "no_diagnosis_causality_treatment_response_or_future_prediction",
)

_APPROVED_RECORDED_CONTEXT: dict[str, dict[str, str]] = {
    "context:stress": {"source_field": "stressed", "recorded_value": "yes"},
    "context:activity": {"source_field": "exercised", "recorded_value": "yes"},
    "context:illness": {"source_field": "is_sick", "recorded_value": "yes"},
    "context:poor_sleep": {"source_field": "sleep_quality", "recorded_value": "bad"},
    "context:fatigue": {"source_field": "fatigue_level", "recorded_value": "tired"},
    "meal:breakfast": {"glycemic_context": "post_meal", "meal_type": "breakfast"},
    "meal:lunch": {"glycemic_context": "post_meal", "meal_type": "lunch"},
    "meal:dinner": {"glycemic_context": "post_meal", "meal_type": "dinner"},
    "meal:snack": {"glycemic_context": "post_meal", "meal_type": "snack"},
    "meal:suhoor": {"glycemic_context": "post_meal", "meal_type": "suhoor"},
    "meal:iftar": {"glycemic_context": "post_meal", "meal_type": "iftar"},
}


@dataclass(frozen=True, slots=True)
class CompanionPatternItem:
    observation_key: str
    kind: str
    current_state: PatternCurrentState
    markers: tuple[PatternMarker, ...]
    first_observed_at: datetime
    last_observed_at: datetime
    state_changed_at: datetime
    recurrence_count: int
    evidence_density: str
    evidence_density_trend: str
    observations: int
    distinct_days: int
    observation_median_glucose_mg_dl: float
    personal_window_median_glucose_mg_dl: float
    baseline_delta_mg_dl: float
    baseline_direction: BaselineDirection
    baseline_movement: BaselineMovement
    evidence_window_days: int
    evidence_id: str
    producer: str
    recorded_context: tuple[tuple[str, str], ...]
    limitations: tuple[str, ...]
    evidence_context: CompanionEvidenceContext
    source_version: str = SOURCE_VERSION


@dataclass(frozen=True, slots=True)
class CompanionPatternResult:
    status: ProjectionStatus
    patterns: tuple[CompanionPatternItem, ...]
    limitations: tuple[str, ...]
    source_version: str = SOURCE_VERSION


def _validate_patient_id(patient_id: int) -> None:
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")


def _finite(value: object, *, field: str) -> float:
    if type(value) not in {int, float}:
        raise ValueError(f"{field} must be numeric")
    resolved = float(value)
    if not math.isfinite(resolved):
        raise ValueError(f"{field} must be finite")
    return resolved


def _validate_observation(row: ClinicalObservationState) -> None:
    if row.truth_kind != ClinicalObservationState.DETERMINISTIC_TRUTH_KIND:
        raise ValueError("pattern has unapproved truth kind")
    if row.producer != ClinicalObservationState.APPROVED_PRODUCER:
        raise ValueError("pattern has unapproved producer")
    if row.evidence_id != ClinicalObservationState.APPROVED_EVIDENCE_ID:
        raise ValueError("pattern has unapproved evidence ID")
    if row.kind not in {
        ClinicalObservationState.KIND_CONTEXT,
        ClinicalObservationState.KIND_MEAL,
    }:
        raise ValueError("pattern has unapproved kind")
    if row.status not in {
        ClinicalObservationState.STATUS_ACTIVE,
        ClinicalObservationState.STATUS_INACTIVE,
    }:
        raise ValueError("pattern has unapproved lifecycle status")
    if row.evidence_strength not in {
        ClinicalObservationState.EVIDENCE_LIMITED,
        ClinicalObservationState.EVIDENCE_MODERATE,
        ClinicalObservationState.EVIDENCE_STRONG,
    }:
        raise ValueError("pattern has unapproved evidence density")
    if row.previous_evidence_strength and row.previous_evidence_strength not in {
        ClinicalObservationState.EVIDENCE_LIMITED,
        ClinicalObservationState.EVIDENCE_MODERATE,
        ClinicalObservationState.EVIDENCE_STRONG,
    }:
        raise ValueError("pattern has unapproved previous evidence density")
    if row.evidence_strength_trend not in {
        ClinicalObservationState.TREND_INITIAL,
        ClinicalObservationState.TREND_STABLE,
        ClinicalObservationState.TREND_STRENGTHENING,
        ClinicalObservationState.TREND_WEAKENING,
    }:
        raise ValueError("pattern has unapproved evidence-density trend")
    if row.evidence_strength_trend == ClinicalObservationState.TREND_INITIAL:
        if row.previous_evidence_strength:
            raise ValueError("initial evidence-density trend cannot have previous density")
    elif not row.previous_evidence_strength:
        raise ValueError("non-initial evidence-density trend requires previous density")
    if row.recurrence_count < 1:
        raise ValueError("pattern recurrence_count must be positive")
    if row.observations < MIN_OBSERVATIONS:
        raise ValueError("pattern does not meet minimum observation count")
    if row.distinct_days < MIN_DISTINCT_DAYS:
        raise ValueError("pattern does not meet minimum distinct-day count")
    if row.evidence_window_days != MAX_WINDOW_DAYS:
        raise ValueError("pattern does not use the canonical evidence window")
    if row.first_seen_at > row.last_seen_at:
        raise ValueError("pattern first_seen_at must not follow last_seen_at")
    if not isinstance(row.context_modifiers, dict):
        raise ValueError("pattern recorded context must be a mapping")
    if any(
        type(key) is not str or type(value) is not str
        for key, value in row.context_modifiers.items()
    ):
        raise ValueError("pattern recorded context must contain string pairs only")
    try:
        approved_context = _APPROVED_RECORDED_CONTEXT[row.observation_key]
    except KeyError as exc:
        raise ValueError("pattern has unapproved observation key") from exc
    if row.context_modifiers != approved_context:
        raise ValueError("pattern recorded context does not match governed key")
    expected_kind = (
        ClinicalObservationState.KIND_MEAL
        if row.observation_key.startswith("meal:")
        else ClinicalObservationState.KIND_CONTEXT
    )
    if row.kind != expected_kind:
        raise ValueError("pattern kind does not match governed observation key")

    current_delta = _finite(row.baseline_delta_mg_dl, field="baseline_delta_mg_dl")
    _finite(
        row.observation_median_glucose_mg_dl,
        field="observation_median_glucose_mg_dl",
    )
    _finite(
        row.window_median_glucose_mg_dl,
        field="window_median_glucose_mg_dl",
    )

    has_previous = row.previous_baseline_delta_mg_dl is not None
    has_change = row.baseline_delta_change_mg_dl is not None
    if has_previous != has_change:
        raise ValueError("pattern baseline history is incomplete")
    if has_previous:
        previous_delta = _finite(
            row.previous_baseline_delta_mg_dl,
            field="previous_baseline_delta_mg_dl",
        )
        stored_change = _finite(
            row.baseline_delta_change_mg_dl,
            field="baseline_delta_change_mg_dl",
        )
        expected_change = round(current_delta - previous_delta, 1)
        if not math.isclose(stored_change, expected_change, abs_tol=0.05):
            raise ValueError("pattern baseline change is internally inconsistent")


def _baseline_direction(delta: float) -> BaselineDirection:
    if delta > 0:
        return "above_personal_window_baseline"
    if delta < 0:
        return "below_personal_window_baseline"
    return "aligned_with_personal_window_baseline"


def _baseline_movement(row: ClinicalObservationState) -> BaselineMovement:
    if row.previous_baseline_delta_mg_dl is None:
        return "initial_or_unknown"
    previous = float(row.previous_baseline_delta_mg_dl)
    current = float(row.baseline_delta_mg_dl)
    if abs(current) < abs(previous):
        return "toward_personal_window_baseline"
    if abs(current) > abs(previous):
        return "away_from_personal_window_baseline"
    return "stable_relative_to_personal_window_baseline"


def _markers(
    row: ClinicalObservationState,
    *,
    movement: BaselineMovement,
) -> tuple[PatternMarker, ...]:
    if row.status == ClinicalObservationState.STATUS_INACTIVE:
        return ("resolved",)

    markers: list[PatternMarker] = ["persisting"]
    if row.recurrence_count > 1:
        markers.append("recurring")
    if movement == "toward_personal_window_baseline":
        markers.append("improving_descriptively")
    return tuple(markers)


def _pattern_missing_data(
    row: ClinicalObservationState,
    *,
    movement: BaselineMovement,
    current_state: PatternCurrentState,
) -> tuple[str, ...]:
    missing: list[str] = []
    if row.evidence_strength_trend == ClinicalObservationState.TREND_INITIAL:
        missing.append("previous_evidence_density_not_available")
    if movement == "initial_or_unknown":
        missing.append("previous_baseline_relative_delta_not_available")
    if current_state == "resolved":
        missing.append("current_active_evidence_not_available_after_resolution")
    return tuple(missing)


def _project(row: ClinicalObservationState) -> CompanionPatternItem:
    _validate_observation(row)
    baseline_delta = float(row.baseline_delta_mg_dl)
    movement = _baseline_movement(row)
    current_state: PatternCurrentState = (
        "active"
        if row.status == ClinicalObservationState.STATUS_ACTIVE
        else "resolved"
    )
    limitations = list(_COMMON_LIMITATIONS)
    if current_state == "resolved":
        limitations.append(
            "numeric_pattern_values_describe_last_eligible_active_evidence"
        )
    if movement == "toward_personal_window_baseline":
        limitations.append(
            "improving_descriptively_does_not_mean_treatment_response_or_outcome"
        )

    limitations_tuple = tuple(limitations)
    evidence_context = build_companion_evidence_context(
        evidence_id=row.evidence_id,
        producer=row.producer,
        evidence_density=row.evidence_strength,
        evidence_density_trend=row.evidence_strength_trend,
        missing_data=_pattern_missing_data(
            row,
            movement=movement,
            current_state=current_state,
        ),
        limitations=limitations_tuple,
    )

    return CompanionPatternItem(
        observation_key=row.observation_key,
        kind=row.kind,
        current_state=current_state,
        markers=_markers(row, movement=movement),
        first_observed_at=row.first_seen_at,
        last_observed_at=row.last_seen_at,
        state_changed_at=row.status_changed_at,
        recurrence_count=row.recurrence_count,
        evidence_density=row.evidence_strength,
        evidence_density_trend=row.evidence_strength_trend,
        observations=row.observations,
        distinct_days=row.distinct_days,
        observation_median_glucose_mg_dl=float(
            row.observation_median_glucose_mg_dl
        ),
        personal_window_median_glucose_mg_dl=float(
            row.window_median_glucose_mg_dl
        ),
        baseline_delta_mg_dl=baseline_delta,
        baseline_direction=_baseline_direction(baseline_delta),
        baseline_movement=movement,
        evidence_window_days=row.evidence_window_days,
        evidence_id=row.evidence_id,
        producer=row.producer,
        recorded_context=tuple(sorted(row.context_modifiers.items())),
        limitations=limitations_tuple,
        evidence_context=evidence_context,
    )


def project_personal_pattern_intelligence(
    *,
    patient_id: int,
) -> CompanionPatternResult:
    """Project all governed longitudinal observations for one patient read-only."""

    _validate_patient_id(patient_id)
    rows = list(
        ClinicalObservationState.objects.filter(patient_id=patient_id).order_by(
            "observation_key"
        )
    )
    patterns = tuple(_project(row) for row in rows)
    if not patterns:
        return CompanionPatternResult(
            status="no_governed_patterns",
            patterns=(),
            limitations=(
                "no_eligible_governed_personal_patterns_available",
                "absence_of_pattern_is_not_evidence_of_absence_of_clinical_issue",
            ),
        )
    return CompanionPatternResult(
        status="ready",
        patterns=patterns,
        limitations=(
            "projection_reads_existing_clinical_twin_truth_only",
            "presentation_order_is_not_clinical_priority",
        ),
    )
