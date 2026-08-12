"""Bounded deterministic smart suggestions for the IAmina patient companion.

This layer creates no clinical truth and no independent priority system. It may
only translate one already-surfaced non-urgent proactive insight into a bounded
companion suggestion, while attaching the matching P2-COMPANION-2/3 governed
pattern and evidence/uncertainty envelope. Emergency routing remains upstream
and separate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from django.db import transaction

from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.companion_change import (
    compare_since_last_companion_review,
)
from diabetes.services.clinical.companion_evidence_uncertainty import (
    CompanionEvidenceContext,
)
from diabetes.services.clinical.companion_pattern_intelligence import (
    CompanionPatternItem,
    project_personal_pattern_intelligence,
)
from diabetes.services.clinical.proactive_intelligence import (
    ATTENTION_BUDGET,
    ProactiveInsight,
    evaluate_proactive_insights,
)

SOURCE_VERSION = "companion-smart-suggestions.v1"

SuggestionClass = Literal[
    "UNDERSTAND_DATA",
    "MONITOR",
    "COLLECT_MISSING_DATA",
    "LEARN",
    "PREPARE_CLINICIAN_DISCUSSION",
    "FOLLOW_UP_RECORD",
]
SuggestionStatus = Literal[
    "suggested",
    "cooldown",
    "no_change",
    "insufficient_data",
]

ALLOWED_SUGGESTION_CLASSES: tuple[SuggestionClass, ...] = (
    "UNDERSTAND_DATA",
    "MONITOR",
    "COLLECT_MISSING_DATA",
    "LEARN",
    "PREPARE_CLINICIAN_DISCUSSION",
    "FOLLOW_UP_RECORD",
)

# V1 intentionally activates only classes whose runtime authority already exists.
# The remaining contract classes fail closed until a later LOT adds the required
# actionable-missing-data, education-catalogue or after-visit authority.
ACTIVE_V1_SUGGESTION_CLASSES: tuple[SuggestionClass, ...] = (
    "UNDERSTAND_DATA",
    "MONITOR",
    "PREPARE_CLINICIAN_DISCUSSION",
)

_COMMON_LIMITATIONS = (
    "suggestion_is_non_prescriptive_companion_support_only",
    "no_diagnosis_causality_prediction_or_treatment_inference",
    "no_medication_or_insulin_dose_change_authority",
    "deterministic_emergency_routing_remains_separate_and_upstream",
)


@dataclass(frozen=True, slots=True)
class CompanionSmartSuggestion:
    suggestion_class: SuggestionClass
    observation_key: str
    reason: str
    proactive_state: str
    change_since_review: str | None
    evidence_context: CompanionEvidenceContext
    missing_data: tuple[str, ...]
    limitations: tuple[str, ...]
    proactive_source_version: str
    pattern_source_version: str
    source_version: str = SOURCE_VERSION


@dataclass(frozen=True, slots=True)
class CompanionSmartSuggestionResult:
    status: SuggestionStatus
    attention_budget: Literal["one_non_urgent_item_per_24h"]
    pending_count: int
    suggestion: CompanionSmartSuggestion | None
    source_version: str = SOURCE_VERSION


def _validate_patient_id(patient_id: int) -> None:
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")


def _derive_suggestion_class(item: ProactiveInsight) -> SuggestionClass:
    """Translate existing proactive authority without expanding it."""

    if item.escalation_class != ProactiveInsightState.ESCALATION_NONE:
        raise ValueError("companion suggestion cannot consume escalation authority")
    if item.priority.safety_time_sensitivity != "non_urgent_observation":
        raise ValueError("companion suggestion may consume non-urgent observations only")
    if item.priority.actionability != item.allowed_next_step:
        raise ValueError("proactive actionability is internally inconsistent")

    if item.allowed_next_step == ProactiveInsightState.ACTION_PREPARE_CLINICIAN_DISCUSSION:
        return "PREPARE_CLINICIAN_DISCUSSION"
    if item.allowed_next_step != ProactiveInsightState.ACTION_MONITOR:
        raise ValueError("proactive action is outside companion suggestion authority")

    if item.state == ProactiveInsightState.STATE_NEW:
        return "UNDERSTAND_DATA"
    if item.state in {
        ProactiveInsightState.STATE_MONITORING,
        ProactiveInsightState.STATE_IMPROVING,
        ProactiveInsightState.STATE_RESOLVED,
    }:
        return "MONITOR"
    raise ValueError("proactive state has no approved V1 companion suggestion mapping")


def _reason(item: ProactiveInsight, suggestion_class: SuggestionClass) -> str:
    if suggestion_class == "UNDERSTAND_DATA":
        return "first_eligible_observation_explain_before_follow_up"
    if suggestion_class == "PREPARE_CLINICIAN_DISCUSSION":
        return "existing_proactive_authority_marks_observation_review_worthy"
    if item.state == ProactiveInsightState.STATE_IMPROVING:
        return "continue_observing_descriptive_movement_without_treatment_inference"
    if item.state == ProactiveInsightState.STATE_RESOLVED:
        return "continue_observing_without_assuming_permanent_resolution"
    return "continue_observing_after_material_supporting_evidence_change"


def _matching_pattern(
    *,
    patient_id: int,
    proactive_item: ProactiveInsight,
) -> CompanionPatternItem:
    pattern_result = project_personal_pattern_intelligence(patient_id=patient_id)
    matches = tuple(
        pattern
        for pattern in pattern_result.patterns
        if pattern.observation_key == proactive_item.observation_key
    )
    if len(matches) != 1:
        raise ValueError("surfaced proactive insight must match exactly one governed pattern")
    pattern = matches[0]
    provenance = pattern.evidence_context.provenance
    if pattern.evidence_id != proactive_item.evidence_id:
        raise ValueError("proactive insight and governed pattern evidence IDs differ")
    if provenance.evidence_id != pattern.evidence_id:
        raise ValueError("pattern evidence envelope does not match governed evidence ID")
    if provenance.producer != pattern.producer:
        raise ValueError("pattern evidence envelope does not match governed producer")
    return pattern


def _change_since_review(
    *,
    patient_id: int,
    pattern: CompanionPatternItem,
) -> str | None:
    result = compare_since_last_companion_review(patient_id=patient_id)
    if result.status != "ready":
        return None
    matches = tuple(
        item for item in result.changes if item.observation_key == pattern.observation_key
    )
    if len(matches) > 1:
        raise ValueError("change-since-review contains duplicate observation keys")
    if not matches:
        return None
    change = matches[0]
    if change.evidence_id != pattern.evidence_id or change.producer != pattern.producer:
        raise ValueError("change-since-review provenance differs from governed pattern")
    if (
        change.evidence_context.provenance.evidence_id
        != pattern.evidence_context.provenance.evidence_id
    ):
        raise ValueError("change-since-review evidence envelope differs from governed pattern")
    return change.change_kind


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


@transaction.atomic
def evaluate_companion_smart_suggestion(
    *,
    patient_id: int,
    evaluated_at: datetime | None = None,
) -> CompanionSmartSuggestionResult:
    """Return at most one bounded suggestion under the existing attention budget.

    ``COLLECT_MISSING_DATA``, ``LEARN`` and ``FOLLOW_UP_RECORD`` are part of the
    canonical companion class vocabulary but are intentionally not emitted in V1:
    their prerequisite authorities are not yet implemented. Unknown authority
    therefore fails closed rather than being improvised here.

    The transaction is intentionally wider than the proactive delivery write: if
    provenance or companion-envelope validation fails afterwards, the attention
    budget is not consumed by a suggestion that was never safely produced.
    """

    _validate_patient_id(patient_id)
    proactive = evaluate_proactive_insights(
        patient_id=patient_id,
        evaluated_at=evaluated_at,
    )
    if proactive.item is None:
        return CompanionSmartSuggestionResult(
            status=proactive.status,
            attention_budget=ATTENTION_BUDGET,
            pending_count=proactive.pending_count,
            suggestion=None,
        )

    pattern = _matching_pattern(
        patient_id=patient_id,
        proactive_item=proactive.item,
    )
    suggestion_class = _derive_suggestion_class(proactive.item)
    if suggestion_class not in ACTIVE_V1_SUGGESTION_CLASSES:
        raise ValueError("suggestion class is not active in P2-COMPANION-4 V1")

    evidence_context = pattern.evidence_context
    return CompanionSmartSuggestionResult(
        status="suggested",
        attention_budget=ATTENTION_BUDGET,
        pending_count=proactive.pending_count,
        suggestion=CompanionSmartSuggestion(
            suggestion_class=suggestion_class,
            observation_key=pattern.observation_key,
            reason=_reason(proactive.item, suggestion_class),
            proactive_state=proactive.item.state,
            change_since_review=_change_since_review(
                patient_id=patient_id,
                pattern=pattern,
            ),
            evidence_context=evidence_context,
            missing_data=evidence_context.uncertainty.missing_data,
            limitations=_dedupe(pattern.limitations + _COMMON_LIMITATIONS),
            proactive_source_version=proactive.item.source_version,
            pattern_source_version=pattern.source_version,
        ),
    )
