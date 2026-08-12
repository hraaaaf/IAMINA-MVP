"""Retired glucose-prediction prototype.

The previous helper fit a linear trend to sparse Journal values, added fixed
wellness offsets, and emitted an uncalibrated confidence number. It had no
population/modality validation or prospective calibration and therefore must not
produce patient- or clinician-facing prediction authority.

A future prediction feature requires its own validation LOT. Until then this
compatibility symbol fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GlucosePrediction:
    """Legacy shape retained so accidental imports fail safely at runtime."""

    hours_ahead: int
    predicted_value: float
    confidence: float
    contributing_factors: list[str]


def predict_glucose(patient, hours_ahead: int = 2) -> Optional[GlucosePrediction]:
    """Return no prediction until a validated prediction contract exists."""
    _ = (patient, hours_ahead)
    return None
