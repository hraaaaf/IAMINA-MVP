"""Retired lifestyle-correlation prototype.

This compatibility module intentionally returns no clinical correlation. The
previous implementation used legacy negative/default context values as synthetic
controls and exposed an uncalibrated numeric "confidence". That conflicts with
IAmina's current clinical-data contract.

Use ``personal_response.compute_personal_response`` for evidence-qualified,
positive-context longitudinal observations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LifestyleCorrelation:
    """Legacy response shape retained only to avoid unsafe import breakage."""

    factor: str
    impact_percent: float
    confidence: float
    sample_size: int
    human_insight: str


def analyze_lifestyle_impact(patient, window_days: int = 21) -> list[LifestyleCorrelation]:
    """Fail closed: unvalidated causal/correlation authority is retired."""
    _ = (patient, window_days)
    return []
