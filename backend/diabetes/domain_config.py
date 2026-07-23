"""
DiabetesDomainConfig — single source of truth for all diabetes-specific constants.

Phase A of the chassis refactor: extract hardcoded domain constants so the
engine layers (router, shield, clinical detectors) contain zero magic numbers.

In Phase B this dataclass will implement a DomainConfig protocol defined in
platform/ and be registered at startup. For now it is imported directly.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DiabetesDomainConfig:

    # ── Routing urgency thresholds (mg/dL) ───────────────────────────────────
    # Used by llm/router.py to classify a message as URGENT before any LLM call.
    urgency_low: float = 54.0    # Level 2 hypoglycemia (ADA definition)
    urgency_high: float = 300.0  # Severe hyperglycemia

    # ── Vital emergency thresholds (mg/dL) ───────────────────────────────────
    # Used by clinical/shield.py to bypass AI entirely and return a pre-canned
    # emergency message. Intentionally wider than urgency thresholds.
    vital_low: float = 54.0
    vital_high: float = 400.0

    # ── Time In Range bounds (mg/dL) ─────────────────────────────────────────
    # ADA standard range used for TIR/TAR/TBR SQL computation.
    tir_low: float = 70.0
    tir_high: float = 180.0

    # ── Analytical thresholds ────────────────────────────────────────────────
    cv_stability_max: float = 36.0  # CV% ≤ this → glycemia is "stable" (ADA)
    min_entries_for_kpis: int = 5   # Fewer readings → KPIs are not meaningful

    # ── Clinical detector thresholds (mg/dL unless noted) ───────────────────
    # Dawn phenomenon
    dawn_morning_high: float = 145.0
    dawn_night_high: float = 130.0
    dawn_delta: float = 30.0

    # Post-exercise hypoglycemia
    post_exercise_hypo: float = 72.0

    # Stress hyperglycemia
    stress_delta: float = 25.0

    # Sleep impact
    sleep_delta: float = 20.0

    # High glycemic variability
    variability_stdev_max: float = 50.0

    # Food sensitivity peak
    food_sensitivity_peak: float = 185.0

    # Somogyi rebound
    somogyi_night_hypo: float = 72.0
    somogyi_morning_hyper: float = 165.0

    # ── Domain identity ──────────────────────────────────────────────────────
    companion_name: str = "IAmina"
    domain_description: str = "diabetes management"
    unit: str = "mg/dL"


# Module-level singleton — import this everywhere instead of using literals.
DIABETES_CONFIG = DiabetesDomainConfig()

# Chassis-compatible domain context built from the config.
# Inject this into IAmina and route() calls from the tracking capsule.
# DEPRECATED path removed — import directly from core contracts (ADR-0008)
from core.contracts.companion_identity import CompanionIdentity  # noqa: E402

DIABETES_DOMAIN_CTX = CompanionIdentity(
    companion_name=DIABETES_CONFIG.companion_name,
    domain_description=DIABETES_CONFIG.domain_description,
    unit=DIABETES_CONFIG.unit,
)
