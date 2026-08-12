"""Persisted lifecycle for deterministic personal-response observations.

The clinical twin stores observation history only. It never accepts companion
state, heuristic/model inference, diagnosis state or treatment semantics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.services.clinical.evidence_registry import PERSONAL_RESPONSE_EVIDENCE_ID
from diabetes.services.clinical.personal_response import (
    MAX_PATTERNS,
    MAX_WINDOW_DAYS,
    PersonalResponsePattern,
    PersonalResponseResult,
    compute_personal_response,
)

PRODUCER_ID = "diabetes.personal_response.v1"

_CONTEXT_MODIFIERS = {
    "context:stress": {"source_field": "stressed", "recorded_value": "yes"},
    "context:activity": {"source_field": "exercised", "recorded_value": "yes"},
    "context:illness": {"source_field": "is_sick", "recorded_value": "yes"},
    "context:poor_sleep": {"source_field": "sleep_quality", "recorded_value": "bad"},
    "context:fatigue": {"source_field": "fatigue_level", "recorded_value": "tired"},
}
_MEAL_KEYS = frozenset(
    {
        "meal:breakfast",
        "meal:lunch",
        "meal:dinner",
        "meal:snack",
        "meal:suhoor",
        "meal:iftar",
    }
)
_EVIDENCE_RANK = {"limited": 0, "moderate": 1, "strong": 2}


def _context_modifiers(pattern: PersonalResponsePattern) -> dict[str, str]:
    if pattern.kind == "context":
        try:
            return dict(_CONTEXT_MODIFIERS[pattern.key])
        except KeyError as exc:
            raise ValueError(f"unsupported personal-response observation key: {pattern.key}") from exc

    if pattern.kind == "meal" and pattern.key in _MEAL_KEYS:
        return {
            "glycemic_context": "post_meal",
            "meal_type": pattern.key.removeprefix("meal:"),
        }

    raise ValueError(f"unsupported personal-response observation key: {pattern.key}")


def _evidence_fingerprint(pattern: PersonalResponsePattern) -> str:
    """Fingerprint only supporting evidence, not the moving window baseline."""
    payload = {
        "key": pattern.key,
        "observations": pattern.observations,
        "distinct_days": pattern.distinct_days,
        "median_glucose_mg_dl": pattern.median_glucose_mg_dl,
        "first_observed_at": pattern.first_observed_at.isoformat(),
        "last_observed_at": pattern.last_observed_at.isoformat(),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _evidence_trend(previous: str, current: str) -> str:
    if not previous:
        return ClinicalObservationState.TREND_INITIAL
    previous_rank = _EVIDENCE_RANK[previous]
    current_rank = _EVIDENCE_RANK[current]
    if current_rank > previous_rank:
        return ClinicalObservationState.TREND_STRENGTHENING
    if current_rank < previous_rank:
        return ClinicalObservationState.TREND_WEAKENING
    return ClinicalObservationState.TREND_STABLE


def _baseline_delta(pattern: PersonalResponsePattern) -> float:
    return round(
        pattern.median_glucose_mg_dl - pattern.window_median_glucose_mg_dl,
        1,
    )


def _eligible_refresh(result: PersonalResponseResult) -> bool:
    return (
        result.total_readings >= result.minimum_observations
        and result.distinct_days >= result.minimum_distinct_days
        and result.window_median_glucose_mg_dl is not None
    )


def _public_result(result: PersonalResponseResult) -> PersonalResponseResult:
    return replace(result, patterns=result.patterns[:MAX_PATTERNS])


@transaction.atomic
def refresh_personal_response_memory(
    *,
    patient_id: int,
    truth_kind: TruthKind = TruthKind.DETERMINISTIC_DERIVATION,
) -> PersonalResponseResult:
    """Refresh the canonical 90-day observation lifecycle for one patient.

    The caller cannot choose a shorter clinical-memory window. This prevents a
    display query such as ``?days=7`` from changing the longitudinal active state.
    The function returns the normal capped personal-response result for callers.
    """
    try:
        resolved_truth_kind = TruthKind(truth_kind)
    except ValueError as exc:
        raise ValueError("unsupported clinical observation truth kind") from exc
    if resolved_truth_kind is not TruthKind.DETERMINISTIC_DERIVATION:
        raise ValueError(
            f"{resolved_truth_kind.value} cannot enter the longitudinal clinical observation store"
        )

    # Serialize canonical refreshes per patient. Explicit source erasure takes
    # the same lock before purging/rebuilding derived state, so a concurrent
    # refresh cannot re-materialize an aggregate computed from an erased source.
    get_user_model().objects.select_for_update().only("pk").get(pk=patient_id)

    result = compute_personal_response(
        patient_id=patient_id,
        window_days=MAX_WINDOW_DAYS,
        max_patterns=None,
    )
    if not _eligible_refresh(result):
        return _public_result(result)

    existing_by_key = {
        row.observation_key: row
        for row in ClinicalObservationState.objects.select_for_update().filter(patient_id=patient_id)
    }
    active_keys: set[str] = set()
    refresh_time = timezone.now()

    for pattern in result.patterns:
        modifiers = _context_modifiers(pattern)
        fingerprint = _evidence_fingerprint(pattern)
        baseline_delta = _baseline_delta(pattern)
        row = existing_by_key.get(pattern.key)

        if row is None:
            ClinicalObservationState.objects.create(
                patient_id=patient_id,
                observation_key=pattern.key,
                kind=pattern.kind,
                truth_kind=TruthKind.DETERMINISTIC_DERIVATION.value,
                status=ClinicalObservationState.STATUS_ACTIVE,
                first_seen_at=pattern.first_observed_at,
                last_seen_at=pattern.last_observed_at,
                status_changed_at=refresh_time,
                recurrence_count=1,
                evidence_strength=pattern.confidence,
                previous_evidence_strength="",
                evidence_strength_trend=ClinicalObservationState.TREND_INITIAL,
                observations=pattern.observations,
                distinct_days=pattern.distinct_days,
                observation_median_glucose_mg_dl=pattern.median_glucose_mg_dl,
                window_median_glucose_mg_dl=pattern.window_median_glucose_mg_dl,
                baseline_delta_mg_dl=baseline_delta,
                previous_baseline_delta_mg_dl=None,
                baseline_delta_change_mg_dl=None,
                evidence_window_days=MAX_WINDOW_DAYS,
                evidence_id=PERSONAL_RESPONSE_EVIDENCE_ID,
                producer=PRODUCER_ID,
                context_modifiers=modifiers,
                last_evidence_fingerprint=fingerprint,
            )
            active_keys.add(pattern.key)
            continue

        support_changed = row.last_evidence_fingerprint != fingerprint
        previous_baseline = row.baseline_delta_mg_dl
        baseline_changed = previous_baseline != baseline_delta
        was_inactive = row.status == ClinicalObservationState.STATUS_INACTIVE

        if support_changed:
            row.previous_evidence_strength = row.evidence_strength
            row.evidence_strength_trend = _evidence_trend(
                row.evidence_strength,
                pattern.confidence,
            )

        if baseline_changed:
            row.previous_baseline_delta_mg_dl = previous_baseline
            row.baseline_delta_change_mg_dl = round(baseline_delta - previous_baseline, 1)

        row.kind = pattern.kind
        row.status = ClinicalObservationState.STATUS_ACTIVE
        if was_inactive:
            row.recurrence_count += 1
            row.status_changed_at = refresh_time
        row.first_seen_at = min(row.first_seen_at, pattern.first_observed_at)
        row.last_seen_at = max(row.last_seen_at, pattern.last_observed_at)
        row.evidence_strength = pattern.confidence
        row.observations = pattern.observations
        row.distinct_days = pattern.distinct_days
        row.observation_median_glucose_mg_dl = pattern.median_glucose_mg_dl
        row.window_median_glucose_mg_dl = pattern.window_median_glucose_mg_dl
        row.baseline_delta_mg_dl = baseline_delta
        row.evidence_window_days = MAX_WINDOW_DAYS
        row.evidence_id = PERSONAL_RESPONSE_EVIDENCE_ID
        row.producer = PRODUCER_ID
        row.context_modifiers = modifiers
        row.last_evidence_fingerprint = fingerprint
        row.save()
        active_keys.add(pattern.key)

    for key, row in existing_by_key.items():
        if key in active_keys or row.status != ClinicalObservationState.STATUS_ACTIVE:
            continue
        row.status = ClinicalObservationState.STATUS_INACTIVE
        row.status_changed_at = refresh_time
        row.save(update_fields=("status", "status_changed_at", "last_refreshed_at"))

    return _public_result(result)
