"""Deterministic personal-response patterns for the Journal.

This module intentionally does not perform causal inference, prediction, treatment
recommendation or statistical significance testing. It summarizes repeated,
explicitly recorded observations and exposes their evidence basis.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median
from typing import Iterable, Literal

from django.db.models import Q, QuerySet
from django.utils import timezone

from diabetes.models.entry import LogEntry

EvidenceStrength = Literal["limited", "moderate", "strong"]
PatternKind = Literal["context", "meal"]

MIN_OBSERVATIONS = 3
MIN_DISTINCT_DAYS = 2
DEFAULT_WINDOW_DAYS = 90
MAX_WINDOW_DAYS = 90
MAX_PATTERNS = 5

# Only positive/explicit states are eligible. Historical negative/neutral values
# are deliberately never used as a control group because older schemas could
# materialize defaults such as ``no``/``good``/``ok``.
_CONTEXT_FACTORS: tuple[tuple[str, str, str], ...] = (
    ("stress", "stressed", "yes"),
    ("activity", "exercised", "yes"),
    ("illness", "is_sick", "yes"),
    ("poor_sleep", "sleep_quality", "bad"),
    ("fatigue", "fatigue_level", "tired"),
)
_MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack", "suhoor", "iftar")


@dataclass(frozen=True)
class PersonalResponsePattern:
    key: str
    kind: PatternKind
    observations: int
    distinct_days: int
    median_glucose_mg_dl: float
    window_median_glucose_mg_dl: float
    first_observed_at: datetime
    last_observed_at: datetime
    confidence: EvidenceStrength


@dataclass(frozen=True)
class PersonalResponseResult:
    status: Literal["ready", "insufficient_data"]
    window_days: int
    total_readings: int
    distinct_days: int
    window_median_glucose_mg_dl: float | None
    minimum_observations: int
    minimum_distinct_days: int
    patterns: tuple[PersonalResponsePattern, ...]


def _event_at(entry: LogEntry) -> datetime:
    return entry.logged_at or entry.created_at


def _median_glucose(entries: Iterable[LogEntry]) -> float:
    values = [float(entry.blood_sugar) for entry in entries]
    return round(float(median(values)), 1)


def _confidence(observations: int, distinct_days: int) -> EvidenceStrength:
    """Product evidence grade, never a probability or clinical confidence score."""
    if observations >= 8 and distinct_days >= 4:
        return "strong"
    if observations >= 5 and distinct_days >= 3:
        return "moderate"
    return "limited"


def _eligible_pattern(
    *,
    key: str,
    kind: PatternKind,
    entries: list[LogEntry],
    window_median: float,
) -> PersonalResponsePattern | None:
    if len(entries) < MIN_OBSERVATIONS:
        return None

    ordered = sorted(entries, key=_event_at)
    distinct_days = len({_event_at(entry).date() for entry in ordered})
    if distinct_days < MIN_DISTINCT_DAYS:
        return None

    return PersonalResponsePattern(
        key=key,
        kind=kind,
        observations=len(ordered),
        distinct_days=distinct_days,
        median_glucose_mg_dl=_median_glucose(ordered),
        window_median_glucose_mg_dl=window_median,
        first_observed_at=_event_at(ordered[0]),
        last_observed_at=_event_at(ordered[-1]),
        confidence=_confidence(len(ordered), distinct_days),
    )


def _window_queryset(patient_id: int, window_days: int) -> QuerySet[LogEntry]:
    now = timezone.now()
    cutoff = now - timedelta(days=window_days)
    return (
        LogEntry.objects.filter(patient_id=patient_id)
        .exclude(source="demo")
        .filter(Q(logged_at__gte=cutoff) | Q(logged_at__isnull=True, created_at__gte=cutoff))
        .order_by("logged_at", "created_at", "id")
    )


def compute_personal_response(
    *,
    patient_id: int,
    window_days: int = DEFAULT_WINDOW_DAYS,
    max_patterns: int | None = MAX_PATTERNS,
) -> PersonalResponseResult:
    """Return repeated observational patterns for one authenticated patient.

    Eligibility is deliberately conservative:
    - at least 3 matching measurements;
    - spread over at least 2 distinct days;
    - context patterns use only explicit positive observations;
    - meal patterns require an explicit ``post_meal`` measurement context;
    - demo entries are excluded;
    - no negative/neutral context is ever treated as a control cohort;
    - analysis is bounded to 90 days to keep patient-scoped reads predictable.

    ``max_patterns=None`` is reserved for internal deterministic consumers such as
    the P2 clinical observation lifecycle. Patient-facing callers keep the capped
    default so presentation ranking cannot accidentally become persistence logic.
    """
    window_days = max(7, min(int(window_days), MAX_WINDOW_DAYS))
    entries = list(_window_queryset(patient_id, window_days))
    distinct_days = len({_event_at(entry).date() for entry in entries})

    if len(entries) < MIN_OBSERVATIONS or distinct_days < MIN_DISTINCT_DAYS:
        return PersonalResponseResult(
            status="insufficient_data",
            window_days=window_days,
            total_readings=len(entries),
            distinct_days=distinct_days,
            window_median_glucose_mg_dl=None,
            minimum_observations=MIN_OBSERVATIONS,
            minimum_distinct_days=MIN_DISTINCT_DAYS,
            patterns=(),
        )

    window_median = _median_glucose(entries)
    patterns: list[PersonalResponsePattern] = []

    for key, field_name, explicit_value in _CONTEXT_FACTORS:
        matching = [entry for entry in entries if getattr(entry, field_name) == explicit_value]
        pattern = _eligible_pattern(
            key=f"context:{key}",
            kind="context",
            entries=matching,
            window_median=window_median,
        )
        if pattern is not None:
            patterns.append(pattern)

    for meal_type in _MEAL_TYPES:
        matching = [
            entry
            for entry in entries
            if entry.glycemic_context == "post_meal" and entry.meal_type == meal_type
        ]
        pattern = _eligible_pattern(
            key=f"meal:{meal_type}",
            kind="meal",
            entries=matching,
            window_median=window_median,
        )
        if pattern is not None:
            patterns.append(pattern)

    confidence_rank = {"limited": 0, "moderate": 1, "strong": 2}
    patterns.sort(
        key=lambda item: (
            confidence_rank[item.confidence],
            item.observations,
            item.distinct_days,
            item.last_observed_at,
        ),
        reverse=True,
    )

    if max_patterns is None:
        selected_patterns = tuple(patterns)
    else:
        selected_patterns = tuple(patterns[: max(0, int(max_patterns))])

    return PersonalResponseResult(
        status="ready" if patterns else "insufficient_data",
        window_days=window_days,
        total_readings=len(entries),
        distinct_days=distinct_days,
        window_median_glucose_mg_dl=window_median,
        minimum_observations=MIN_OBSERVATIONS,
        minimum_distinct_days=MIN_DISTINCT_DAYS,
        patterns=selected_patterns,
    )
