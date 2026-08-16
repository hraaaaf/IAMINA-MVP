"""Read-only projection of the governed proactive insight authority.

This module deliberately reuses the deterministic lifecycle, priority and action
helpers from ``proactive_intelligence``. It never refreshes clinical truth, never
creates or updates ``ProactiveInsightState`` rows and never consumes delivery or
attention-budget state. The Dashboard may read this projection; only the explicit
POST command may mutate proactive delivery bookkeeping.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.proactive_intelligence import (
    ATTENTION_BUDGET,
    ATTENTION_COOLDOWN_HOURS,
    ProactiveInsight,
    _build_item,
    _delivery_signature,
    _derive_action,
    _derive_relevance,
    _derive_state,
    _priority_key,
)

PreviewStatus = Literal["available", "cooldown", "no_change", "insufficient_data"]


@dataclass(frozen=True)
class ProactivePreview:
    status: PreviewStatus
    attention_budget: Literal["one_non_urgent_item_per_24h"]
    cooldown_until: datetime | None
    pending_count: int
    item: ProactiveInsight | None


def _validate_patient_id(patient_id: int) -> None:
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")


def _transient_state(
    observation: ClinicalObservationState,
    prior: ProactiveInsightState | None,
) -> ProactiveInsightState:
    """Derive the existing authority in memory without persisting product state."""

    state = _derive_state(observation, prior)
    relevance = _derive_relevance(observation, state)
    action_class = _derive_action(relevance)
    signature = _delivery_signature(
        observation=observation,
        state=state,
        relevance=relevance,
        action_class=action_class,
    )
    return ProactiveInsightState(
        observation=observation,
        state=state,
        clinical_relevance=relevance,
        action_class=action_class,
        escalation_class=ProactiveInsightState.ESCALATION_NONE,
        last_observation_fingerprint=observation.last_evidence_fingerprint,
        current_signature=signature,
        last_delivered_signature=(prior.last_delivered_signature if prior else ""),
        last_surfaced_at=(prior.last_surfaced_at if prior else None),
    )


def preview_proactive_insights(
    *,
    patient_id: int,
    evaluated_at: datetime | None = None,
) -> ProactivePreview:
    """Preview at most one governed insight without any clinical or delivery write.

    The function reads the already-persisted Clinical Twin. It intentionally does
    not call ``refresh_personal_response_memory`` because safe Dashboard reads must
    not mutate clinical truth. If no governed observation exists, it fails closed.
    """

    _validate_patient_id(patient_id)
    evaluated_at = evaluated_at or timezone.now()

    observations = list(
        ClinicalObservationState.objects.filter(patient_id=patient_id).order_by(
            "observation_key"
        )
    )
    if not observations:
        return ProactivePreview(
            status="insufficient_data",
            attention_budget=ATTENTION_BUDGET,
            cooldown_until=None,
            pending_count=0,
            item=None,
        )

    existing_by_observation = {
        row.observation_id: row
        for row in ProactiveInsightState.objects.filter(
            observation__patient_id=patient_id
        )
    }
    pending: list[tuple[ClinicalObservationState, ProactiveInsightState]] = []
    for observation in observations:
        prior = existing_by_observation.get(observation.id)
        projected = _transient_state(observation, prior)
        if projected.last_delivered_signature != projected.current_signature:
            pending.append((observation, projected))

    if not pending:
        return ProactivePreview(
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
            return ProactivePreview(
                status="cooldown",
                attention_budget=ATTENTION_BUDGET,
                cooldown_until=cooldown_until,
                pending_count=len(pending),
                item=None,
            )

    observation, projected = max(
        pending,
        key=lambda item: _priority_key(item[0], item[1]),
    )
    return ProactivePreview(
        status="available",
        attention_budget=ATTENTION_BUDGET,
        cooldown_until=None,
        pending_count=len(pending),
        item=_build_item(
            observation,
            projected,
            surface_now=False,
            interruption_cost="eligible",
        ),
    )


__all__ = ["ProactivePreview", "preview_proactive_insights"]
