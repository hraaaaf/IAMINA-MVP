"""Single source of truth for persisted diabetes log inputs.

This contract is intentionally technical. It defines storage/input admissibility,
not treatment targets or diagnostic thresholds.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Literal

from django.utils import timezone

GLUCOSE_MIN_MG_DL = 30.0
GLUCOSE_MAX_MG_DL = 600.0
MMOL_L_TO_MG_DL = 18.016
LOGGED_AT_FUTURE_TOLERANCE = timedelta(minutes=5)

GlycemicContext = Literal["", "fasting", "pre_meal", "post_meal", "other"]
MealType = Literal[
    "",
    "fasting",
    "breakfast",
    "lunch",
    "snack",
    "dinner",
    "iftar",
    "suhoor",
    "other",
]
YesNo = Literal["", "yes", "no"]
SleepQuality = Literal["", "good", "bad"]
FatigueLevel = Literal["", "ok", "tired"]
LogSource = Literal["manual", "voice", "cgm", "import", "demo"]

GLYCEMIC_CONTEXT_VALUES = ("", "fasting", "pre_meal", "post_meal", "other")
MEAL_TYPE_VALUES = (
    "",
    "fasting",
    "breakfast",
    "lunch",
    "snack",
    "dinner",
    "iftar",
    "suhoor",
    "other",
)
EXERCISE_VALUES = ("", "yes", "no")
STRESS_VALUES = ("", "yes", "no")
SLEEP_VALUES = ("", "good", "bad")
FATIGUE_VALUES = ("", "ok", "tired")
SICK_VALUES = ("", "no", "yes")
SOURCE_VALUES = ("manual", "voice", "cgm", "import", "demo")

_UNIT_FACTORS = {
    "mg/dl": 1.0,
    "mgdl": 1.0,
    "g/l": 100.0,
    "gl": 100.0,
    "mmol/l": MMOL_L_TO_MG_DL,
    "mmol": MMOL_L_TO_MG_DL,
    "mmoll": MMOL_L_TO_MG_DL,
}


class LogInputValidationError(ValueError):
    """Raised when a log input cannot be normalized safely."""


def _normalise_unit(unit: str) -> str:
    return str(unit).strip().lower().replace(" ", "").replace("-", "")


def validate_mg_dl(value: float) -> float:
    """Validate canonical mg/dL storage bounds."""
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise LogInputValidationError("Glucose value must be numeric.") from exc

    if not math.isfinite(numeric):
        raise LogInputValidationError("Glucose value must be finite.")
    if not (GLUCOSE_MIN_MG_DL <= numeric <= GLUCOSE_MAX_MG_DL):
        raise LogInputValidationError(
            f"Glucose value must be between {GLUCOSE_MIN_MG_DL:g} and "
            f"{GLUCOSE_MAX_MG_DL:g} mg/dL."
        )
    return numeric


def convert_glucose_to_mg_dl(value: float, unit: str) -> float:
    """Normalize supported glucose units to canonical mg/dL storage."""
    factor = _UNIT_FACTORS.get(_normalise_unit(unit))
    if factor is None:
        raise LogInputValidationError(
            "Unknown glucose unit. Accepted: mg/dL, g/L, mmol/L."
        )
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise LogInputValidationError("Glucose value must be numeric.") from exc
    if not math.isfinite(numeric):
        raise LogInputValidationError("Glucose value must be finite.")
    return round(validate_mg_dl(numeric * factor), 1)


def validate_logged_at(
    value: datetime | None,
    *,
    now: datetime | None = None,
) -> datetime | None:
    """Reject ambiguous or materially future-dated measurement timestamps."""
    if value is None:
        return None
    if timezone.is_naive(value):
        raise LogInputValidationError("logged_at must include a timezone offset.")

    reference = now or timezone.now()
    if timezone.is_naive(reference):
        raise ValueError("reference time must be timezone-aware")
    if value > reference + LOGGED_AT_FUTURE_TOLERANCE:
        raise LogInputValidationError(
            "logged_at cannot be more than 5 minutes in the future."
        )
    return value
