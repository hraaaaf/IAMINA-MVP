"""Read-only P2-COMPANION-7 overview projection for patient UX.

This module composes already-certified companion projections. It creates no
clinical truth, consumes no proactive attention budget and performs no writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from diabetes.models.after_visit import AfterVisitAnchor
from diabetes.services.clinical.companion_change import compare_since_last_companion_review
from diabetes.services.clinical.companion_pattern_intelligence import (
    project_personal_pattern_intelligence,
)

SOURCE_VERSION = "companion-overview.v1"


@dataclass(frozen=True, slots=True)
class CompanionOverviewPattern:
    observation_key: str
    current_state: str
    markers: tuple[str, ...]
    evidence_density: str
    recurrence_count: int
    baseline_direction: str
    baseline_movement: str
    first_observed_at: datetime
    last_observed_at: datetime
    evidence_id: str
    source_version: str
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompanionOverviewChange:
    observation_key: str
    change_kind: str
    evidence_strength: str
    missing_data: tuple[str, ...]
    source_version: str


@dataclass(frozen=True, slots=True)
class CompanionOverviewAfterVisit:
    status: Literal["recorded", "no_recorded_visit"]
    anchor_id: int | None
    occurred_at: datetime | None
    source: str | None
    fact_count: int
    latest_fact_at: datetime | None


@dataclass(frozen=True, slots=True)
class CompanionOverview:
    pattern_status: str
    review_status: str
    review_anchor_captured_at: datetime | None
    patterns: tuple[CompanionOverviewPattern, ...]
    changes_since_review: tuple[CompanionOverviewChange, ...]
    after_visit: CompanionOverviewAfterVisit
    safety_notice: str = (
        "Companion support only. Observations are descriptive and do not diagnose, "
        "infer treatment efficacy, prescribe, advise doses or change treatment."
    )
    source_version: str = SOURCE_VERSION


def _validate_patient_id(patient_id: int) -> None:
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")


def _after_visit(patient_id: int) -> CompanionOverviewAfterVisit:
    anchor = (
        AfterVisitAnchor.objects.filter(patient_id=patient_id)
        .order_by("-occurred_at", "-id")
        .first()
    )
    if anchor is None:
        return CompanionOverviewAfterVisit(
            status="no_recorded_visit",
            anchor_id=None,
            occurred_at=None,
            source=None,
            fact_count=0,
            latest_fact_at=None,
        )

    facts = anchor.facts.order_by("-recorded_at", "-id")
    latest = facts.first()
    return CompanionOverviewAfterVisit(
        status="recorded",
        anchor_id=anchor.id,
        occurred_at=anchor.occurred_at,
        source=anchor.source,
        fact_count=facts.count(),
        latest_fact_at=latest.recorded_at if latest is not None else None,
    )


def build_companion_overview(*, patient_id: int) -> CompanionOverview:
    """Compose governed companion state without consuming proactive delivery state."""

    _validate_patient_id(patient_id)
    pattern_result = project_personal_pattern_intelligence(patient_id=patient_id)
    change_result = compare_since_last_companion_review(patient_id=patient_id)

    patterns = tuple(
        CompanionOverviewPattern(
            observation_key=item.observation_key,
            current_state=item.current_state,
            markers=tuple(item.markers),
            evidence_density=item.evidence_density,
            recurrence_count=item.recurrence_count,
            baseline_direction=item.baseline_direction,
            baseline_movement=item.baseline_movement,
            first_observed_at=item.first_observed_at,
            last_observed_at=item.last_observed_at,
            evidence_id=item.evidence_id,
            source_version=item.source_version,
            limitations=item.limitations,
        )
        for item in pattern_result.patterns
    )
    changes = tuple(
        CompanionOverviewChange(
            observation_key=item.observation_key,
            change_kind=item.change_kind,
            evidence_strength=item.evidence_strength,
            missing_data=item.missing_data,
            source_version=item.source_version,
        )
        for item in change_result.changes
    )

    return CompanionOverview(
        pattern_status=pattern_result.status,
        review_status=change_result.status,
        review_anchor_captured_at=change_result.anchor_captured_at,
        patterns=patterns,
        changes_since_review=changes,
        after_visit=_after_visit(patient_id),
    )


__all__ = ["CompanionOverview", "build_companion_overview"]
