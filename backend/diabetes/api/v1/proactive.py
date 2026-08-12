"""Patient-scoped deterministic proactive insight command surface."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Literal

from ninja import Router
from pydantic import BaseModel

from diabetes.services.clinical.proactive_intelligence import evaluate_proactive_insights

router = Router(tags=["proactive-insights"])


class PriorityVectorOut(BaseModel):
    safety_time_sensitivity: Literal["non_urgent_observation"]
    clinical_relevance: Literal["observational", "review_worthy"]
    persistence: str
    change_from_personal_baseline_mg_dl: float
    evidence_density: Literal["limited", "moderate", "strong"]
    actionability: Literal["MONITOR", "PREPARE_CLINICIAN_DISCUSSION"]
    evidence_maturity: str
    interruption_cost: Literal["eligible", "cooldown"]


class ProactiveInsightOut(BaseModel):
    observation_key: str
    kind: Literal["context", "meal"]
    state: Literal["new", "monitoring", "persisting", "improving", "resolved"]
    surface_now: bool
    what_changed: str
    why_it_is_surfacing_now: str
    evidence_window_days: int
    personal_baseline_comparison_mg_dl: float
    observations: int
    distinct_days: int
    evidence_density: Literal["limited", "moderate", "strong"]
    limitations_or_missing_data: list[str]
    allowed_next_step: Literal["MONITOR", "PREPARE_CLINICIAN_DISCUSSION"]
    escalation_class: Literal["none"]
    evidence_id: str
    source_version: str
    priority: PriorityVectorOut


class ProactiveFeedOut(BaseModel):
    status: Literal["surfaced", "cooldown", "no_change", "insufficient_data"]
    attention_budget: Literal["one_non_urgent_item_per_24h"]
    cooldown_until: datetime | None
    pending_count: int
    safety_notice: str
    item: ProactiveInsightOut | None


@router.post("/proactive-insights/evaluate/", response=ProactiveFeedOut)
def evaluate_proactive_insight(request):
    """Explicitly evaluate and consume at most one non-urgent insight candidate.

    This is intentionally a POST because a surfaced item updates deterministic
    delivery bookkeeping (`last_surfaced_at` and delivery signature). Safe GET
    requests must not consume the patient's attention budget.
    """
    result = evaluate_proactive_insights(patient_id=request.user.id)
    return {
        "status": result.status,
        "attention_budget": result.attention_budget,
        "cooldown_until": result.cooldown_until,
        "pending_count": result.pending_count,
        "safety_notice": (
            "Observational prioritization only. It does not diagnose, prescribe, "
            "change treatment, or replace deterministic emergency routing."
        ),
        "item": asdict(result.item) if result.item is not None else None,
    }
