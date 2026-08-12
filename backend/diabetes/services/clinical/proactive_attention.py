"""Deterministic attention budget over the certified clinical observation memory.

This module decides which already-governed observation deserves product attention.
It does not diagnose, predict, prescribe, calculate risk, or deliver a notification.
Deterministic emergency handling is an upstream prerequisite: callers must provide
an explicit CLEAR clearance before any proactive state is created or surfaced.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from django.db import transaction
from django.utils import timezone

from diabetes.models.clinical_insight import ClinicalInsightState
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.services.clinical.evidence_registry import (
    PERSONAL_RESPONSE_EVIDENCE_ID,
    ClinicalAuthority,
    get_evidence,
)
from diabetes.services.clinical.observation_memory import (
    PRODUCER_ID as OBSERVATION_PRODUCER_ID,
)
from diabetes.services.clinical.observation_memory import refresh_personal_response_memory


class EmergencyClearance(StrEnum):
    """Proof that canonical deterministic emergency handling ran first."""

    UNKNOWN = "unknown"
    CLEAR = "clear"
    ACTIVE = "active"


@dataclass(frozen=True)
class PriorityVector:
    """Auditable dimensions used for lexicographic attention ordering.

    This is deliberately not collapsed into a scalar score.
    """

    safety_time_sensitivity: str
    clinical_relevance: str
    persistence: str
    baseline_distance_mg_dl: float
    evidence_strength: str
    evidence_maturity: str
    actionability: str
    interruption_cost: str
    observations: int
    distinct_days: int
    recurrence_count: int
    last_seen_at: datetime


@dataclass(frozen=True)
class ProactiveInsightCandidate:
    observation_key: str
    lifecycle_state: str
    allowed_next_step: str
    what_changed: tuple[str, ...]
    why_it_is_surfacing_now: tuple[str, ...]
    evidence_window_days: int
    personal_baseline_delta_mg_dl: float
    evidence_density: dict[str, object]
    limitations_or_missing_data: str
    escalation_class: str
    source_version: str
    priority_vector: PriorityVector


@dataclass(frozen=True)
class ProactiveDecision:
    candidate: ProactiveInsightCandidate | None
    suppression_reason: str | None = None


_EVIDENCE_RANK = {"limited": 0, "moderate": 1, "strong": 2}
_STATE_PRIORITY = {
    ClinicalInsightState.STATE_PERSISTING: 5,
    ClinicalInsightState.STATE_IMPROVING: 4,
    ClinicalInsightState.STATE_NEW: 3,
    ClinicalInsightState.STATE_MONITORING: 2,
    ClinicalInsightState.STATE_RESOLVED: 1,
}
_ACTION_PRIORITY = {
    ClinicalInsightState.ACTION_MONITOR: 1,
    ClinicalInsightState.ACTION_COLLECT_MISSING_DATA: 0,
}


def _hash_payload(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _dataset_eligible(result: object) -> bool:
    return bool(
        getattr(result, "total_readings", 0) >= getattr(result, "minimum_observations", 0)
        and getattr(result, "distinct_days", 0) >= getattr(result, "minimum_distinct_days", 0)
        and getattr(result, "window_median_glucose_mg_dl", None) is not None
    )


def _source_material_fingerprint(
    observation: ClinicalObservationState,
    *,
    dataset_eligible: bool,
) -> str:
    return _hash_payload(
        {
            "observation_key": observation.observation_key,
            "status": observation.status,
            "recurrence_count": observation.recurrence_count,
            "evidence_strength": observation.evidence_strength,
            "observations": observation.observations,
            "distinct_days": observation.distinct_days,
            "observation_median": observation.observation_median_glucose_mg_dl,
            "window_median": observation.window_median_glucose_mg_dl,
            "baseline_delta": observation.baseline_delta_mg_dl,
            "previous_baseline_delta": observation.previous_baseline_delta_mg_dl,
            "baseline_delta_change": observation.baseline_delta_change_mg_dl,
            "first_seen_at": observation.first_seen_at.isoformat(),
            "last_seen_at": observation.last_seen_at.isoformat(),
            "dataset_eligible": dataset_eligible,
        }
    )


def _decision_fingerprint(
    *,
    material_fingerprint: str,
    lifecycle_state: str,
    allowed_next_step: str,
) -> str:
    return _hash_payload(
        {
            "material_fingerprint": material_fingerprint,
            "lifecycle_state": lifecycle_state,
            "allowed_next_step": allowed_next_step,
        }
    )


def _moves_toward_recorded_baseline(observation: ClinicalObservationState) -> bool:
    previous = observation.previous_baseline_delta_mg_dl
    current = observation.baseline_delta_mg_dl
    if previous is None or observation.baseline_delta_change_mg_dl is None:
        return False
    return abs(current) < abs(previous)


def _resolution_criterion_met(
    observation: ClinicalObservationState,
    *,
    dataset_eligible: bool,
    now: datetime,
) -> bool:
    if not dataset_eligible or observation.status != ClinicalObservationState.STATUS_INACTIVE:
        return False
    # Product-resolution horizon equals the governed evidence window. This is not
    # a claim that a disease/problem resolved; it means the descriptive observation
    # has had no supporting sighting across a full eligible evidence horizon.
    resolution_cutoff = now - timedelta(days=observation.evidence_window_days)
    return observation.last_seen_at <= resolution_cutoff


def _lifecycle_state(
    observation: ClinicalObservationState,
    insight: ClinicalInsightState,
    *,
    created: bool,
    material_changed: bool,
    dataset_eligible: bool,
    now: datetime,
) -> str:
    if observation.status == ClinicalObservationState.STATUS_INACTIVE:
        if _resolution_criterion_met(
            observation,
            dataset_eligible=dataset_eligible,
            now=now,
        ):
            return ClinicalInsightState.STATE_RESOLVED
        if not dataset_eligible:
            return insight.lifecycle_state
        return ClinicalInsightState.STATE_MONITORING

    if created:
        return ClinicalInsightState.STATE_NEW

    if (
        insight.lifecycle_state == ClinicalInsightState.STATE_NEW
        and not insight.last_surfaced_decision_fingerprint
    ):
        return ClinicalInsightState.STATE_NEW

    if not material_changed:
        if insight.lifecycle_state in (
            ClinicalInsightState.STATE_PERSISTING,
            ClinicalInsightState.STATE_IMPROVING,
        ):
            return insight.lifecycle_state
        return ClinicalInsightState.STATE_MONITORING

    if _moves_toward_recorded_baseline(observation):
        return ClinicalInsightState.STATE_IMPROVING

    if observation.recurrence_count >= 2:
        return ClinicalInsightState.STATE_PERSISTING

    return ClinicalInsightState.STATE_MONITORING


def _reason_codes(
    observation: ClinicalObservationState,
    insight: ClinicalInsightState,
    *,
    created: bool,
    dataset_eligible: bool,
    lifecycle_state: str,
) -> list[str]:
    if created:
        if observation.status == ClinicalObservationState.STATUS_ACTIVE:
            return ["first_eligible_observation"]
        return ["existing_observation_initialized"]

    reasons: list[str] = []
    if insight.source_status_snapshot != observation.status:
        reasons.append(
            "observation_reactivated"
            if observation.status == ClinicalObservationState.STATUS_ACTIVE
            else "observation_no_longer_active"
        )

    if observation.recurrence_count > insight.recurrence_count_snapshot:
        reasons.append("activation_episode_recurred")

    previous_rank = _EVIDENCE_RANK.get(insight.evidence_strength_snapshot, -1)
    current_rank = _EVIDENCE_RANK[observation.evidence_strength]
    if insight.evidence_strength_snapshot and current_rank > previous_rank:
        reasons.append("evidence_strengthened")
    elif insight.evidence_strength_snapshot and current_rank < previous_rank:
        reasons.append("evidence_weakened")

    previous_delta = insight.baseline_delta_snapshot_mg_dl
    current_delta = observation.baseline_delta_mg_dl
    if previous_delta is not None and previous_delta != current_delta:
        if abs(current_delta) < abs(previous_delta):
            reasons.append("moved_toward_recorded_baseline")
        elif abs(current_delta) > abs(previous_delta):
            reasons.append("moved_away_from_recorded_baseline")
        else:
            reasons.append("baseline_relationship_changed")

    if observation.observations != insight.observations_snapshot:
        reasons.append("supporting_observations_changed")
    if observation.distinct_days != insight.distinct_days_snapshot:
        reasons.append("supporting_days_changed")

    if dataset_eligible != insight.dataset_eligible_snapshot:
        reasons.append(
            "data_eligibility_restored"
            if dataset_eligible
            else "data_became_insufficient"
        )

    if lifecycle_state != insight.lifecycle_state:
        reasons.append(f"lifecycle_{lifecycle_state}")

    return list(dict.fromkeys(reasons))


def _persistence_class(observation: ClinicalObservationState) -> str:
    if observation.recurrence_count >= 2:
        return "recurrent_activation"
    if observation.evidence_strength == ClinicalObservationState.EVIDENCE_STRONG:
        return "dense_first_episode"
    return "first_episode"


def _priority_vector(
    observation: ClinicalObservationState,
    *,
    lifecycle_state: str,
    allowed_next_step: str,
    evidence_maturity: str,
    changed: bool,
) -> PriorityVector:
    return PriorityVector(
        safety_time_sensitivity="routine_non_emergency",
        clinical_relevance="governed_descriptive_observation",
        persistence=_persistence_class(observation),
        baseline_distance_mg_dl=round(abs(observation.baseline_delta_mg_dl), 1),
        evidence_strength=observation.evidence_strength,
        evidence_maturity=evidence_maturity,
        actionability=allowed_next_step,
        interruption_cost="surface_material_change" if changed else "suppress_unchanged",
        observations=observation.observations,
        distinct_days=observation.distinct_days,
        recurrence_count=observation.recurrence_count,
        last_seen_at=observation.last_seen_at,
    )


def _candidate_sort_key(candidate: ProactiveInsightCandidate) -> tuple[object, ...]:
    vector = candidate.priority_vector
    return (
        -_STATE_PRIORITY[candidate.lifecycle_state],
        -_EVIDENCE_RANK[vector.evidence_strength],
        -_ACTION_PRIORITY[candidate.allowed_next_step],
        -vector.recurrence_count,
        -vector.baseline_distance_mg_dl,
        -vector.observations,
        -vector.distinct_days,
        -vector.last_seen_at.timestamp(),
        candidate.observation_key,
    )


def _validate_source(observation: ClinicalObservationState) -> None:
    if observation.truth_kind != ClinicalObservationState.DETERMINISTIC_TRUTH_KIND:
        raise ValueError("proactive attention requires deterministic clinical observation truth")
    if observation.producer != OBSERVATION_PRODUCER_ID:
        raise ValueError("proactive attention received an unapproved observation producer")
    if observation.evidence_id != PERSONAL_RESPONSE_EVIDENCE_ID:
        raise ValueError("proactive attention received an unapproved evidence rule")


def _build_candidate(
    observation: ClinicalObservationState,
    insight: ClinicalInsightState,
    *,
    evidence_maturity: str,
    limitations: str,
    changed: bool,
) -> ProactiveInsightCandidate:
    reasons = tuple(str(code) for code in insight.pending_reason_codes)
    return ProactiveInsightCandidate(
        observation_key=observation.observation_key,
        lifecycle_state=insight.lifecycle_state,
        allowed_next_step=insight.allowed_next_step,
        what_changed=reasons,
        why_it_is_surfacing_now=reasons,
        evidence_window_days=observation.evidence_window_days,
        personal_baseline_delta_mg_dl=observation.baseline_delta_mg_dl,
        evidence_density={
            "grade": observation.evidence_strength,
            "observations": observation.observations,
            "distinct_days": observation.distinct_days,
            "recurrence_count": observation.recurrence_count,
        },
        limitations_or_missing_data=(
            "Current data are insufficient for a fresh governed personal-response refresh."
            if insight.allowed_next_step == ClinicalInsightState.ACTION_COLLECT_MISSING_DATA
            else limitations
        ),
        escalation_class="none",
        source_version=f"{observation.evidence_id}@{observation.producer}",
        priority_vector=_priority_vector(
            observation,
            lifecycle_state=insight.lifecycle_state,
            allowed_next_step=insight.allowed_next_step,
            evidence_maturity=evidence_maturity,
            changed=changed,
        ),
    )


@transaction.atomic
def select_next_proactive_insight(
    *,
    patient_id: int,
    emergency_clearance: EmergencyClearance = EmergencyClearance.UNKNOWN,
) -> ProactiveDecision:
    """Return at most one changed deterministic insight and mark it as surfaced.

    The default is fail-closed: proactive attention is unavailable until a caller
    proves that canonical deterministic emergency handling ran first and is CLEAR.
    This service performs no message generation or notification delivery.
    """
    try:
        clearance = EmergencyClearance(emergency_clearance)
    except ValueError:
        clearance = EmergencyClearance.UNKNOWN

    if clearance is EmergencyClearance.ACTIVE:
        return ProactiveDecision(candidate=None, suppression_reason="deterministic_emergency_active")
    if clearance is not EmergencyClearance.CLEAR:
        return ProactiveDecision(candidate=None, suppression_reason="emergency_clearance_required")

    result = refresh_personal_response_memory(patient_id=patient_id)
    dataset_eligible = _dataset_eligible(result)
    now = timezone.now()

    evidence = get_evidence(PERSONAL_RESPONSE_EVIDENCE_ID)
    if evidence.clinical_authority is not ClinicalAuthority.GOVERNED_RULE:
        return ProactiveDecision(candidate=None, suppression_reason="source_rule_not_governed")
    if evidence.supersession_state != "current":
        return ProactiveDecision(candidate=None, suppression_reason="source_rule_superseded")

    observations = list(
        ClinicalObservationState.objects.select_for_update()
        .filter(patient_id=patient_id)
        .order_by("observation_key")
    )
    if not observations:
        return ProactiveDecision(candidate=None, suppression_reason="no_governed_observations")

    candidates: list[tuple[ProactiveInsightCandidate, ClinicalInsightState, str]] = []

    for observation in observations:
        _validate_source(observation)
        insight, created = ClinicalInsightState.objects.select_for_update().get_or_create(
            observation=observation,
            defaults={"observation_key": observation.observation_key},
        )
        if insight.observation_key != observation.observation_key:
            raise ValueError("proactive insight observation key mismatch")

        material_fingerprint = _source_material_fingerprint(
            observation,
            dataset_eligible=dataset_eligible,
        )
        material_changed = (
            created or material_fingerprint != insight.last_material_fingerprint
        )
        lifecycle_state = _lifecycle_state(
            observation,
            insight,
            created=created,
            material_changed=material_changed,
            dataset_eligible=dataset_eligible,
            now=now,
        )
        allowed_next_step = (
            ClinicalInsightState.ACTION_MONITOR
            if dataset_eligible
            else ClinicalInsightState.ACTION_COLLECT_MISSING_DATA
        )
        decision_fingerprint = _decision_fingerprint(
            material_fingerprint=material_fingerprint,
            lifecycle_state=lifecycle_state,
            allowed_next_step=allowed_next_step,
        )
        decision_changed = decision_fingerprint != insight.last_decision_fingerprint

        if decision_changed:
            reasons = _reason_codes(
                observation,
                insight,
                created=created,
                dataset_eligible=dataset_eligible,
                lifecycle_state=lifecycle_state,
            )
            if not reasons and material_fingerprint != insight.last_material_fingerprint:
                reasons = ["evidence_support_changed"]
            if (
                lifecycle_state == ClinicalInsightState.STATE_RESOLVED
                and "lifecycle_resolved" not in reasons
            ):
                reasons.append("resolution_window_completed")
            insight.pending_reason_codes = reasons

        insight.lifecycle_state = lifecycle_state
        insight.allowed_next_step = allowed_next_step
        insight.source_status_snapshot = observation.status
        insight.recurrence_count_snapshot = observation.recurrence_count
        insight.evidence_strength_snapshot = observation.evidence_strength
        insight.baseline_delta_snapshot_mg_dl = observation.baseline_delta_mg_dl
        insight.observations_snapshot = observation.observations
        insight.distinct_days_snapshot = observation.distinct_days
        insight.dataset_eligible_snapshot = dataset_eligible
        insight.last_material_fingerprint = material_fingerprint
        insight.last_decision_fingerprint = decision_fingerprint
        insight.save()

        pending = decision_fingerprint != insight.last_surfaced_decision_fingerprint
        waiting_for_resolution = (
            observation.status == ClinicalObservationState.STATUS_INACTIVE
            and lifecycle_state == ClinicalInsightState.STATE_MONITORING
            and dataset_eligible
        )
        never_surfaced_resolution = (
            lifecycle_state == ClinicalInsightState.STATE_RESOLVED
            and insight.surface_count == 0
        )
        if not pending or waiting_for_resolution or never_surfaced_resolution:
            continue

        candidate = _build_candidate(
            observation,
            insight,
            evidence_maturity=evidence.evidence_maturity.value,
            limitations=evidence.limitations,
            changed=True,
        )
        candidates.append((candidate, insight, material_fingerprint))

    if not candidates:
        return ProactiveDecision(candidate=None, suppression_reason="attention_budget_suppressed")

    candidate, selected_state, selected_material_fingerprint = min(
        candidates,
        key=lambda item: _candidate_sort_key(item[0]),
    )

    surfaced_state = selected_state.lifecycle_state
    if surfaced_state == ClinicalInsightState.STATE_NEW:
        # NEW is the state of the item that is returned. Once it has been surfaced,
        # the stored lifecycle moves to MONITORING without creating a second attention
        # event on the next identical read.
        selected_state.lifecycle_state = ClinicalInsightState.STATE_MONITORING
        acknowledged_fingerprint = _decision_fingerprint(
            material_fingerprint=selected_material_fingerprint,
            lifecycle_state=ClinicalInsightState.STATE_MONITORING,
            allowed_next_step=selected_state.allowed_next_step,
        )
        selected_state.last_decision_fingerprint = acknowledged_fingerprint
        selected_state.last_surfaced_decision_fingerprint = acknowledged_fingerprint
    else:
        selected_state.last_surfaced_decision_fingerprint = selected_state.last_decision_fingerprint

    if selected_state.first_surfaced_at is None:
        selected_state.first_surfaced_at = now
    selected_state.last_surfaced_at = now
    selected_state.surface_count += 1
    selected_state.pending_reason_codes = []
    selected_state.save()

    return ProactiveDecision(candidate=candidate)
