from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from statistics import mean

from django.utils import timezone

from diabetes.models import LogEntry


@dataclass
class LifestyleCorrelation:
    factor: str          # "sleep", "stress", "activity"
    impact_percent: float
    confidence: float
    sample_size: int
    human_insight: str   # e.g. "Your Tuesdays run 23% higher on short sleep"


def _confidence(sample_size: int, impact_percent: float) -> float:
    base = 0.35 + min(sample_size, 12) * 0.04 + min(abs(impact_percent), 60.0) / 200.0
    return round(min(base, 0.95), 2)


def _build_correlation(
    factor: str,
    active_values: list[float],
    baseline_values: list[float],
    higher_phrase: str,
    lower_phrase: str,
) -> LifestyleCorrelation | None:
    if len(active_values) < 2 or len(baseline_values) < 2:
        return None

    avg_active = mean(active_values)
    avg_baseline = mean(baseline_values)
    if avg_baseline <= 0:
        return None

    impact_percent = round(((avg_active - avg_baseline) / avg_baseline) * 100.0, 1)
    if abs(impact_percent) < 5.0:
        return None

    direction_phrase = higher_phrase if impact_percent > 0 else lower_phrase
    human_insight = (
        f"{factor.capitalize()}: average glucose runs {abs(impact_percent):.0f}% "
        f"{direction_phrase} ({avg_active:.0f} vs {avg_baseline:.0f} mg/dL)."
    )

    sample_size = len(active_values) + len(baseline_values)
    return LifestyleCorrelation(
        factor=factor,
        impact_percent=impact_percent,
        confidence=_confidence(sample_size, impact_percent),
        sample_size=sample_size,
        human_insight=human_insight,
    )


def analyze_lifestyle_impact(patient, window_days: int = 21) -> list[LifestyleCorrelation]:
    """
    Compute simple lifestyle correlations from recent LogEntry rows.

    This implementation is intentionally conservative:
    - uses existing scalar lifestyle columns as source of truth
    - returns only factors with enough contrast and enough data
    - expresses effect size as percentage difference vs baseline
    """
    since = timezone.now() - timedelta(days=window_days)
    entries = list(
        LogEntry.objects.filter(
            patient=patient,
            blood_sugar__isnull=False,
            created_at__gte=since,
        ).order_by("created_at")
    )

    if len(entries) < 4:
        return []

    stressed_yes = [float(e.blood_sugar) for e in entries if e.stressed == "yes"]
    stressed_no = [float(e.blood_sugar) for e in entries if e.stressed == "no"]
    sleep_bad = [float(e.blood_sugar) for e in entries if e.sleep_quality == "bad"]
    sleep_good = [float(e.blood_sugar) for e in entries if e.sleep_quality == "good"]
    exercise_yes = [float(e.blood_sugar) for e in entries if e.exercised == "yes"]
    exercise_no = [float(e.blood_sugar) for e in entries if e.exercised == "no"]

    correlations = [
        _build_correlation("stress", stressed_yes, stressed_no, "higher on stressed days", "lower on stressed days"),
        _build_correlation("sleep", sleep_bad, sleep_good, "higher after poor sleep", "lower after poor sleep"),
        _build_correlation("activity", exercise_yes, exercise_no, "higher on exercise days", "lower on exercise days"),
    ]

    return sorted(
        [c for c in correlations if c is not None],
        key=lambda item: abs(item.impact_percent),
        reverse=True,
    )
