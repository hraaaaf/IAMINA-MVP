"""Patient companion UX API.

Safe reads stay read-only. The explicit smart-suggestion command is a POST
because it consumes deterministic proactive delivery state and the non-urgent
attention budget.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Literal

from ninja import Router
from pydantic import BaseModel

from diabetes.services.clinical.companion_overview import build_companion_overview
from diabetes.services.clinical.companion_smart_suggestions import (
    evaluate_companion_smart_suggestion,
)

router = Router(tags=["companion"])


class CompanionPatternOut(BaseModel):
    observation_key: str
    current_state: str
    markers: list[str]
    evidence_density: str
    recurrence_count: int
    baseline_direction: str
    baseline_movement: str
    first_observed_at: datetime
    last_observed_at: datetime
    evidence_id: str
    source_version: str
    limitations: list[str]


class CompanionChangeOut(BaseModel):
    observation_key: str
    change_kind: str
    evidence_strength: str
    missing_data: list[str]
    source_version: str


class CompanionAfterVisitOut(BaseModel):
    status: Literal["recorded", "no_recorded_visit"]
    anchor_id: int | None
    occurred_at: datetime | None
    source: str | None
    fact_count: int
    latest_fact_at: datetime | None


class CompanionOverviewOut(BaseModel):
    pattern_status: str
    review_status: str
    review_anchor_captured_at: datetime | None
    patterns: list[CompanionPatternOut]
    changes_since_review: list[CompanionChangeOut]
    after_visit: CompanionAfterVisitOut
    safety_notice: str
    source_version: Literal["companion-overview.v1"]


class CompanionNextActionSuggestionOut(BaseModel):
    suggestion_class: Literal[
        "UNDERSTAND_DATA",
        "MONITOR",
        "PREPARE_CLINICIAN_DISCUSSION",
    ]
    observation_key: str
    reason: str
    proactive_state: str
    change_since_review: str | None
    missing_data: list[str]
    limitations: list[str]
    proactive_source_version: str
    pattern_source_version: str
    source_version: str


class CompanionNextActionOut(BaseModel):
    status: Literal["suggested", "cooldown", "no_change", "insufficient_data"]
    attention_budget: Literal["one_non_urgent_item_per_24h"]
    pending_count: int
    safety_notice: str
    suggestion: CompanionNextActionSuggestionOut | None


@router.get("/companion/overview", response=CompanionOverviewOut)
def companion_overview(request):
    """Return governed companion state without consuming proactive attention budget."""

    return asdict(build_companion_overview(patient_id=request.user.id))


@router.post("/companion/next-action/evaluate/", response=CompanionNextActionOut)
def companion_next_action(request):
    """Consume at most one bounded non-urgent suggestion after explicit user action."""

    result = evaluate_companion_smart_suggestion(patient_id=request.user.id)
    suggestion = result.suggestion
    return {
        "status": result.status,
        "attention_budget": result.attention_budget,
        "pending_count": result.pending_count,
        "safety_notice": (
            "Explicit non-prescriptive companion step only. This command may consume "
            "the non-urgent attention budget. It never diagnoses, prescribes, changes "
            "treatment, or replaces deterministic emergency routing."
        ),
        "suggestion": None
        if suggestion is None
        else {
            "suggestion_class": suggestion.suggestion_class,
            "observation_key": suggestion.observation_key,
            "reason": suggestion.reason,
            "proactive_state": suggestion.proactive_state,
            "change_since_review": suggestion.change_since_review,
            "missing_data": list(suggestion.missing_data),
            "limitations": list(suggestion.limitations),
            "proactive_source_version": suggestion.proactive_source_version,
            "pattern_source_version": suggestion.pattern_source_version,
            "source_version": suggestion.source_version,
        },
    }
