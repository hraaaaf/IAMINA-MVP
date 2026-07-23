from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from statistics import mean
from typing import Optional

from django.utils import timezone

from diabetes.models import LogEntry


@dataclass
class GlucosePrediction:
    hours_ahead: int
    predicted_value: float
    confidence: float
    contributing_factors: list[str]


def _linear_regression(points: list[tuple[float, float]]) -> tuple[float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_mean = mean(xs)
    y_mean = mean(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return 0.0, y_mean

    slope = sum((x - x_mean) * (y - y_mean) for x, y in points) / denom
    intercept = y_mean - slope * x_mean
    return slope, intercept


def predict_glucose(patient, hours_ahead: int = 2) -> Optional[GlucosePrediction]:
    """
    Lightweight short-horizon glucose prediction from recent LogEntry rows.

    Model:
    - linear trend on recent glucose readings over time
    - small deterministic adjustments from the latest wellness indicators
    - clamped to physiological app bounds
    """
    since = timezone.now() - timedelta(days=21)
    entries = list(
        LogEntry.objects.filter(
            patient=patient,
            blood_sugar__isnull=False,
            created_at__gte=since,
        ).order_by("created_at")
    )

    if len(entries) < 3:
        return None

    origin = entries[0].effective_time
    points = [
        ((entry.effective_time - origin).total_seconds() / 3600.0, float(entry.blood_sugar))
        for entry in entries
    ]
    slope, intercept = _linear_regression(points)
    target_x = points[-1][0] + float(hours_ahead)
    predicted = slope * target_x + intercept

    latest = entries[-1]
    contributing_factors: list[str] = []

    if latest.stressed == "yes":
        predicted += 12.0
        contributing_factors.append("stress")
    if latest.sleep_quality == "bad":
        predicted += 10.0
        contributing_factors.append("poor_sleep")
    if latest.exercised == "yes":
        predicted -= 8.0
        contributing_factors.append("recent_activity")
    if getattr(latest, "fatigue_level", "ok") != "ok":
        predicted += 6.0
        contributing_factors.append("fatigue")

    predicted = round(min(max(predicted, 30.0), 600.0), 1)

    # Confidence scales with sample size and penalizes very steep trends.
    sample_bonus = min(len(entries), 12) * 0.03
    slope_penalty = min(abs(slope) / 10.0, 0.2)
    confidence = round(max(0.25, min(0.9, 0.45 + sample_bonus - slope_penalty)), 2)

    if not contributing_factors:
        contributing_factors.append("recent_glucose_trend")

    return GlucosePrediction(
        hours_ahead=hours_ahead,
        predicted_value=predicted,
        confidence=confidence,
        contributing_factors=contributing_factors,
    )
