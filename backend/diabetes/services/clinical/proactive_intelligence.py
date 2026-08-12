"""Deterministic prioritization and lifecycle for proactive diabetes insights.

This layer consumes only approved ``ClinicalObservationState`` rows. It never
creates clinical truth, diagnoses, treatment recommendations, or emergency
authority. Deterministic emergency routing remains a separate upstream concern.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from django.db import transaction
from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.evidence_registry import get_evidence
from diabetes.services.clinical.observation_memory import refresh_personal_response_memory

PROACTIVE_RULE_VERSION = "proactive.personal-response.lifecycle.v1"
ATTENTION_COOLDOWN_HOURS = 24
ATTENTION_BUDGET = "one_non_urgent_item_per_24h"

_EVIDENCE_RANK = {"limited": 0, "moderate": 1, "strong": 2}
_STATE_RANK = {
    ProactiveInsightState.STATE_MONITORING: 0,
    ProactiveInsightState.STATE_RESOLVED: 1,
    ProactiveInsightState.STATE_NEW: 2,
    ProactiveInsightState.STATE_IMPROVING: 3,
    ProactiveInsightState.STATE_PERSISTING: 4,
}
_RELEVANCE_RANK = {
    ProactiveInsightState.RELEVANCE_OBSERVATIONAL: 0,
    ProactiveInsightState.RELEVANCE_REVIEW_WORTHY: 1,
}
_ACTION_RANK = {
    ProactiveInsightState.ACTION_MONITOR: 0,
    ProactiveInsightState.ACTION_PREPARE_CLINICIAN_DISCUSSION: 1,
}


@dataclass(frozen=True)
class PriorityVector:
    safety_time_sensitivity: Literal["non_urgent_observation"]
    clinical_relevance: Literal["observational", "review_worthy"]
    persistence: str
    change_from_personal_baseline_mg_dl: float
    evidence_density: Literal["limited", "moderate", "strong"]
    actionability: Literal["MONITOR", "PREPARE_CLINICIAN_DISCUSSION"]
    evidence_maturity: str
    interruption_cost: Literal["eligible", "cooldown"]


@dataclass(frozen=True)
class ProactiveInsight:
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
    limitations_or_missing_data: tuple[str, ...]
    allowed_next_step: Literal["MONITOR", "PREPARE_CLINICIAN_DISCUSSION"]
    escalation_class: Literal["none"]
    evidence_id: str
    source_version: str
    priority: PriorityVector


@dataclass(frozen=True)
class ProactiveEvaluation:
    status: Literal["surfaced", "cooldown", "no_change", "insufficient_data"]
    attention_budget: Literal["one_non_urgent_item_per_24h"]
    cooldown_until: datetime | None
    pending_count: int
    item: ProactiveInsight | None


def _data_eligible(result) -> bool:
    return (
        result.total_readings >= result.minimum_observations
        and result.distinct_days >= result.minimum_distinct_days
        and result.window_median_glucose_mg_dl is not None
    )


def _moves_toward_personal_baseline(
    observation: ClinicalObservationState,
    *,
    support_changed: bool,
) -> bool:
    previous = observation.previous_baseline_delta_mg_dl
    if not support_changed or previous is None:
        return False
    return abs(observation.baseline_delta_mg_dl) < abs(previous)


def _derive_state(
    observation: ClinicalObservationState,
    prior: ProactiveInsightState | None,
) -> str:
    if observation.status == ClinicalObservationState.STATUS_INACTIVE:
        return ProactiveInsightState.STATE_RESOLVED

    if prior is None:
        return ProactiveInsightState.STATE_NEW

    support_changed = (
        prior.last_observation_fingerprint != observation.last_evidence_fingerprint
    )
    if not support_changed:
        return prior.state

    if _moves_toward_personal_baseline(
        observation,
        support_changed=support_changed,
    ):
        return ProactiveInsightState.STATE_IMPROVING

    if (
        observation.recurrence_count >= 2
        or observation.evidence_strength
        in (
            ClinicalObservationState.EVIDENCE_MODERATE,
            ClinicalObservationState.EVIDENCE_STRONG,
        )
    ):
        return ProactiveInsightState.STATE_PERSISTING

    return ProactiveInsightState.STATE_MONITORING


def _derive_relevance(observation: ClinicalObservationState, state: str) -> str:
    if (
        state == ProactiveInsightState.STATE_PERSISTING
        or observation.recurrence_count >= 2
        or observation.evidence_strength == ClinicalObservationState.EVIDENCE_STRONG
    ):
        return ProactiveInsightState.RELEVANCE_REVIEW_WORTHY
    return ProactiveInsightState.RELEVANCE_OBSERVATIONAL


def _derive_action(relevance: str) -> str:
    if relevance == ProactiveInsightState.RELEVANCE_REVIEW_WORTHY:
        return ProactiveInsightState.ACTION_PREPARE_CLINICIAN_DISCUSSION
    return ProactiveInsightState.ACTION_MONITOR


def _delivery_signature(
    *,
    observation: ClinicalObservationState,
    state: str,
    relevance: str,
    action_class: str,
) -> str:
    payload = {
        "observation_key": observation.observation_key,
        "status": observation.status,
        "state": state,
        "clinical_relevance": relevance,
        "action_class": action_class,
        "evidence_strength": observation.evidence_strength,
        "recurrence_count": observation.recurrence_count,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _what_changed(state: str) -> str:
    return {
        ProactiveInsightState.STATE_NEW: "first_eligible_observation",
        ProactiveInsightState.STATE_MONITORING: "new_supporting_evidence",
        ProactiveInsightState.STATE_PERSISTING: "repeated_eligible_evidence",
        ProactiveInsightState.STATE_IMPROVING: "association_moved_toward_personal_baseline",
        ProactiveInsightState.STATE_RESOLVED: "observation_no_longer_meets_repeatability_rule",
    }[state]


def _why_now(state: str) -> str:
    return {
        ProactiveInsightState.STATE_NEW: "first_eligible_occurrence",
        ProactiveInsightState.STATE_MONITORING: "supporting_evidence_changed",
        ProactiveInsightState.STATE_PERSISTING: "persistence_or_evidence_density_changed",
        ProactiveInsightState.STATE_IMPROVING: "eligible_change_toward_personal_baseline",
        ProactiveInsightState.STATE_RESOLVED: "eligible_90_day_refresh_marked_observation_inactive",
    }[state]


def _persistence_label(
    observation: ClinicalObservationState,
    state: str,
) -> str:
    if state == ProactiveInsightState.STATE_RESOLVED:
        return "eligible_absence"
    if observation.recurrence_count >= 2:
        return "recurrent_episode"
    if state == ProactiveInsightState.STATE_PERSISTING:
        return "continuing_eligible_evidence"
    if state == ProactiveInsightState.STATE_NEW:
        return "first_eligible_episode"
    return "monitoring_episode"


def _limitations(observation: ClinicalObservationState) -> tuple[str, ...]:
    values = [
        "observational_association_only",
        "no_causality_diagnosis_or_treatment_inference",
    ]
    if observation.evidence_strength == ClinicalObservationState.EVIDENCE_LIMITED:
        values.append("limited_repeatability")
    return tuple(values)


def _priority_vector(
    observation: ClinicalObservationState,
    insight_state: ProactiveInsightState,
    *,
    interruption_cost: Literal["eligible", "cooldown"],
) -> PriorityVector:
    evidence = get_evidence(observation.evidence_id)
    return PriorityVector(
        safety_time_sensitivity="non_urgent_observation",
        clinical_relevance=insight_state.clinical_relevance,
        persistence=_persistence_label(observation, insight_state.state),
        change_from_personal_baseline_mg_dl=observation.baseline_delta_mg_dl,
        evidence_density=observation.evidence_strength,
        actionability=insight_state.action_class,
        evidence_maturity=evidence.evidence_maturity.value,
        interruption_cost=interruption_cost,
    )


def _priority_key(
    observation: ClinicalObservationState,
    insight_state: ProactiveInsightState,
) -> tuple[object, ...]:
    return (
        _RELEVANCE_RANK[insight_state.clinical_relevance],
        _ACTION_RANK[insight_state.action_class],
        _STATE_RANK[insight_state.state],
        _EVIDENCE_RANK[observation.evidence_strength],
        observation.recurrence_count,
        observation.distinct_days,
        observation.observations,
        observation.last_seen_at,
        observation.observation_key,
    )


def _build_item(
    observation: ClinicalObservationState,
    insight_state: ProactiveInsightState,
    *,
    surface_now: bool,
    interruption_cost: Literal["eligible", "cooldown"],
) -> ProactiveInsight:
    return ProactiveInsight(
        observation_key=observation.observation_key,
        kind=observation.kind,
        state=insight_state.state,
        surface_now=surface_now,
        what_changed=_what_changed(insight_state.state),
        why_it_is_surfacing_now=_why_now(insight_state.state),
        evidence_window_days=observation.evidence_window_days,
        personal_baseline_comparison_mg_dl=observation.baseline_delta_mg_dl,
        observations=observation.observations,
        distinct_days=observation.distinct_days,
        evidence_density=observation.evidence_strength,
        limitations_or_missing_data=_limitations(observation),
        allowed_next_step=insight_state.action_class,
        escalation_class=ProactiveInsightState.ESCALATION_NONE,
        evidence_id=observation.evidence_id,
        source_version=PROACTIVE_RULE_VERSION,
        priority=_priority_vector(
            observation,
            insight_state,
            interruption_cost=interruption_cost,
        ),
    )


@transaction.atomic
def evaluate_proactive_insights(
    *,
    patient_id: int,
    evaluated_at: datetime | None = None,
) -> ProactiveEvaluation:
    """Refresh the clinical twin, update proactive state, and surface at most one item.

    The 24-hour attention budget is a product interruption-cost rule for these
    non-urgent descriptive observations. It never applies to deterministic
    emergency routing.
    """
    evaluated_at = evaluated_at or timezone.now()
    result = refresh_personal_response_memory(patient_id=patient_id)

    if not _data_eligible(result):
        return ProactiveEvaluation(
            status="insufficient_data",
            attention_budget=ATTENTION_BUDGET,
            cooldown_until=None,
            pending_count=0,
            item=None,
        )

    observations = list(
        ClinicalObservationState.objects.select_for_update()
        .filter(patient_id=patient_id)
        .order_by("observation_key")
    )
    existing_by_observation = {
        row.observation_id: row
        for row in ProactiveInsightState.objects.select_for_update().filter(
            observation__patient_id=patient_id
        )
    }

    pending: list[tuple[ClinicalObservationState, ProactiveInsightState]] = []

    for observation in observations:
        prior = existing_by_observation.get(observation.id)
        state = _derive_state(observation, prior)
        relevance = _derive_relevance(observation, state)
        action_class = _derive_action(relevance)
        signature = _delivery_signature(
            observation=observation,
            state=state,
            relevance=relevance,
            action_class=action_class,
        )

        if prior is None:
            insight_state = ProactiveInsightState.objects.create(
                observation=observation,
                state=state,
                clinical_relevance=relevance,
                action_class=action_class,
                escalation_class=ProactiveInsightState.ESCALATION_NONE,
                last_observation_fingerprint=observation.last_evidence_fingerprint,
                current_signature=signature,
            )
        else:
            insight_state = prior
            insight_state.state = state
            insight_state.clinical_relevance = relevance
            insight_state.action_class = action_class
            insight_state.last_observation_fingerprint = (
                observation.last_evidence_fingerprint
            )
            insight_state.current_signature = signature
            insight_state.save(
                update_fields=(
                    "state",
                    "clinical_relevance",
                    "action_class",
                    "last_observation_fingerprint",
                    "current_signature",
                    "updated_at",
                )
            )

        if insight_state.last_delivered_signature != insight_state.current_signature:
            pending.append((observation, insight_state))

    if not pending:
        return ProactiveEvaluation(
            status="no_change",
            attention_budget=ATTENTION_BUDGET,
            cooldown_until=None,
            pending_count=0,
            item=None,
        )

    most_recent_surface = (
        ProactiveInsightState.objects.filter(
            observation__patient_id=patient_id,
            last_surfaced_at__isnull=False,
        )
        .order_by("-last_surfaced_at")
        .first()
    )
    if most_recent_surface and most_recent_surface.last_surfaced_at is not None:
        cooldown_until = most_recent_surface.last_surfaced_at + timedelta(
            hours=ATTENTION_COOLDOWN_HOURS
        )
        if evaluated_at < cooldown_until:
            return ProactiveEvaluation(
                status="cooldown",
                attention_budget=ATTENTION_BUDGET,
                cooldown_until=cooldown_until,
                pending_count=len(pending),
                item=None,
            )

    observation, insight_state = max(
        pending,
        key=lambda item: _priority_key(item[0], item[1]),
    )
    insight_state.last_delivered_signature = insight_state.current_signature
    insight_state.last_surfaced_at = evaluated_at
    insight_state.save(
        update_fields=(
            "last_delivered_signature",
            "last_surfaced_at",
            "updated_at",
        )
    )

    return ProactiveEvaluation(
        status="surfaced",
        attention_budget=ATTENTION_BUDGET,
        cooldown_until=evaluated_at + timedelta(hours=ATTENTION_COOLDOWN_HOURS),
        pending_count=max(0, len(pending) - 1),
        item=_build_item(
            observation,
            insight_state,
            surface_now=True,
            interruption_cost="eligible",
        ),
    )
