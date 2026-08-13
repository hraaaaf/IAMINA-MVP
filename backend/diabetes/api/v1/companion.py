"""Read-only patient companion UX API."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Literal

from ninja import Router
from pydantic import BaseModel

from diabetes.services.clinical.companion_overview import build_companion_overview

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


@router.get("/companion/overview", response=CompanionOverviewOut)
def companion_overview(request):
    """Return governed companion state without consuming proactive attention budget."""

    return asdict(build_companion_overview(patient_id=request.user.id))
