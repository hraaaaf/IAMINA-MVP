"""Deterministic pre→post meal analytics from explicitly linked episodes only.

ANALYSIS-7 never guesses that two readings belong to the same meal. A pair exists
only when both rows carry the same explicit ``meal_episode_id``. The resulting
delta is descriptive evidence, not causality, treatment response, or a clinical
target assessment.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median
from typing import Literal
from uuid import UUID

from django.db.models import Q
from django.utils import timezone

from diabetes.contracts import log_entry as log_input
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.personal_response import (
    MAX_WINDOW_DAYS,
    MIN_DISTINCT_DAYS,
    MIN_OBSERVATIONS,
)

DEFAULT_WINDOW_DAYS = 90
EVIDENCE_ID = "rule.personal-response.repetition.v1"
_LIMITATIONS = (
    "explicit_episode_link_only_no_temporal_pairing_inference",
    "pre_post_delta_is_descriptive_not_causal",
    "no_clinical_target_or_treatment_response_interpretation",
    "no_diagnosis_treatment_dose_or_future_prediction",
)


@dataclass(frozen=True, slots=True)
class PairedMealEpisode:
    episode_id: UUID
    meal_type: str
    pre_at: datetime
    post_at: datetime
    pre_glucose_mg_dl: float
    post_glucose_mg_dl: float
    delta_mg_dl: float
    elapsed_minutes: float


@dataclass(frozen=True, slots=True)
class PairedMealPattern:
    meal_type: str
    pairs: int
    distinct_days: int
    median_pre_glucose_mg_dl: float
    median_post_glucose_mg_dl: float
    median_delta_mg_dl: float
    evidence_density: Literal["limited", "moderate", "strong"]
    evidence_id: str = EVIDENCE_ID


@dataclass(frozen=True, slots=True)
class PairedMealResponseResult:
    status: Literal["ready", "insufficient_data"]
    window_days: int
    explicit_episode_count: int
    complete_pair_count: int
    incomplete_or_invalid_episode_count: int
    pairs: tuple[PairedMealEpisode, ...]
    patterns: tuple[PairedMealPattern, ...]
    evidence_id: str
    limitations: tuple[str, ...]


def _event_at(entry: LogEntry) -> datetime:
    return entry.logged_at or entry.created_at


def _evidence_density(pairs: int, distinct_days: int) -> Literal[
    "limited", "moderate", "strong"
]:
    """Product repeatability grade, never probability or clinical confidence."""
    if pairs >= 8 and distinct_days >= 4:
        return "strong"
    if pairs >= 5 and distinct_days >= 3:
        return "moderate"
    return "limited"


def _window_entries(*, patient_id: int, window_days: int) -> list[LogEntry]:
    now = timezone.now()
    cutoff = now - timedelta(days=window_days)
    return list(
        LogEntry.objects.filter(
            patient_id=patient_id,
            meal_episode_id__isnull=False,
            glycemic_context__in=log_input.PAIRED_MEAL_CONTEXT_VALUES,
        )
        .exclude(source="demo")
        .filter(
            Q(logged_at__gte=cutoff, logged_at__lte=now)
            | Q(
                logged_at__isnull=True,
                created_at__gte=cutoff,
                created_at__lte=now,
            )
        )
        .order_by("logged_at", "created_at", "id")
    )


def _pair_episode(episode_id: UUID, entries: list[LogEntry]) -> PairedMealEpisode | None:
    pre = [entry for entry in entries if entry.glycemic_context == "pre_meal"]
    post = [entry for entry in entries if entry.glycemic_context == "post_meal"]
    if len(pre) != 1 or len(post) != 1:
        return None

    pre_entry = pre[0]
    post_entry = post[0]
    if (
        pre_entry.meal_type != post_entry.meal_type
        or pre_entry.meal_type not in log_input.PAIRED_MEAL_TYPE_VALUES
    ):
        return None

    pre_at = _event_at(pre_entry)
    post_at = _event_at(post_entry)
    if post_at <= pre_at:
        return None

    pre_glucose = float(pre_entry.blood_sugar)
    post_glucose = float(post_entry.blood_sugar)
    elapsed_minutes = round((post_at - pre_at).total_seconds() / 60.0, 1)
    return PairedMealEpisode(
        episode_id=episode_id,
        meal_type=pre_entry.meal_type,
        pre_at=pre_at,
        post_at=post_at,
        pre_glucose_mg_dl=pre_glucose,
        post_glucose_mg_dl=post_glucose,
        delta_mg_dl=round(post_glucose - pre_glucose, 1),
        elapsed_minutes=elapsed_minutes,
    )


def _patterns(pairs: tuple[PairedMealEpisode, ...]) -> tuple[PairedMealPattern, ...]:
    grouped: dict[str, list[PairedMealEpisode]] = defaultdict(list)
    for pair in pairs:
        grouped[pair.meal_type].append(pair)

    patterns: list[PairedMealPattern] = []
    for meal_type, meal_pairs in grouped.items():
        distinct_days = len({pair.pre_at.date() for pair in meal_pairs})
        if len(meal_pairs) < MIN_OBSERVATIONS or distinct_days < MIN_DISTINCT_DAYS:
            continue
        patterns.append(
            PairedMealPattern(
                meal_type=meal_type,
                pairs=len(meal_pairs),
                distinct_days=distinct_days,
                median_pre_glucose_mg_dl=round(
                    float(median(pair.pre_glucose_mg_dl for pair in meal_pairs)), 1
                ),
                median_post_glucose_mg_dl=round(
                    float(median(pair.post_glucose_mg_dl for pair in meal_pairs)), 1
                ),
                median_delta_mg_dl=round(
                    float(median(pair.delta_mg_dl for pair in meal_pairs)), 1
                ),
                evidence_density=_evidence_density(len(meal_pairs), distinct_days),
            )
        )

    patterns.sort(key=lambda item: (-item.pairs, item.meal_type))
    return tuple(patterns)


def compute_paired_meal_response(
    *,
    patient_id: int,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> PairedMealResponseResult:
    """Return only exact patient-scoped pre/post pairs from explicit meal episodes."""
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")

    window_days = max(7, min(int(window_days), MAX_WINDOW_DAYS))
    entries = _window_entries(patient_id=patient_id, window_days=window_days)
    grouped: dict[UUID, list[LogEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.meal_episode_id].append(entry)

    pairs = tuple(
        sorted(
            (
                pair
                for episode_id, episode_entries in grouped.items()
                if (pair := _pair_episode(episode_id, episode_entries)) is not None
            ),
            key=lambda pair: (pair.pre_at, str(pair.episode_id)),
        )
    )
    explicit_episode_count = len(grouped)
    return PairedMealResponseResult(
        status="ready" if pairs else "insufficient_data",
        window_days=window_days,
        explicit_episode_count=explicit_episode_count,
        complete_pair_count=len(pairs),
        incomplete_or_invalid_episode_count=explicit_episode_count - len(pairs),
        pairs=pairs,
        patterns=_patterns(pairs),
        evidence_id=EVIDENCE_ID,
        limitations=_LIMITATIONS,
    )
