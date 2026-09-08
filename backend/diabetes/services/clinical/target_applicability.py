"""Fail-closed authority for patient-specific glucose target assessment.

ANALYSIS-6 deliberately separates three concepts that legacy fields blurred:
configured range, clinically confirmed target authority, and measured CGM
attainment. IAmina never invents a target from demographics or a guideline.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from django.utils import timezone

from diabetes.contracts import log_entry as log_input
from diabetes.models import DiabetesProfile
from diabetes.services.clinical.evidence_registry import get_evidence

TARGET_SUPPORTING_EVIDENCE_ID = "source.ada.2026.section6"
_TARGET_LIMITATION = (
    "Patient-specific target comparison only. It does not diagnose control, infer a cause, "
    "or authorize a medication, dose, device-setting, diet, or treatment change."
)


@dataclass(frozen=True)
class TargetAuthority:
    verified: bool
    reason_code: str
    provenance: str
    population_context: str
    target_low_mg_dl: float | None
    target_high_mg_dl: float | None
    target_time_in_range_goal_pct: float | None
    confirmed_at: datetime | None
    evidence_id: str = TARGET_SUPPORTING_EVIDENCE_ID
    limitation: str = _TARGET_LIMITATION

    def to_metadata(self) -> dict[str, object]:
        return {
            "verified": self.verified,
            "reason_code": self.reason_code,
            "provenance": self.provenance,
            "population_context": self.population_context,
            "target_low_mg_dl": self.target_low_mg_dl,
            "target_high_mg_dl": self.target_high_mg_dl,
            "target_time_in_range_goal_pct": self.target_time_in_range_goal_pct,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "evidence_id": self.evidence_id,
            "limitation": self.limitation,
        }


def unavailable_target_authority(reason_code: str) -> TargetAuthority:
    """Build a neutral authority snapshot when no usable target profile exists."""
    get_evidence(TARGET_SUPPORTING_EVIDENCE_ID)
    return TargetAuthority(
        verified=False,
        reason_code=reason_code,
        provenance="unknown",
        population_context="unknown",
        target_low_mg_dl=None,
        target_high_mg_dl=None,
        target_time_in_range_goal_pct=None,
        confirmed_at=None,
    )


def _snapshot(profile: DiabetesProfile, *, reason_code: str, verified: bool = False) -> TargetAuthority:
    return TargetAuthority(
        verified=verified,
        reason_code=reason_code,
        provenance=str(profile.target_range_provenance),
        population_context=str(profile.target_population_context),
        target_low_mg_dl=float(profile.target_range_low),
        target_high_mg_dl=float(profile.target_range_high),
        target_time_in_range_goal_pct=(
            float(profile.target_time_in_range_goal_pct)
            if profile.target_time_in_range_goal_pct is not None
            else None
        ),
        confirmed_at=profile.target_confirmed_at,
    )


def assess_target_authority(
    profile: DiabetesProfile,
    *,
    now: datetime | None = None,
) -> TargetAuthority:
    """Verify whether stored target fields may support a normative comparison.

    The range is eligible only when it was explicitly clinician-confirmed, has a
    documented population/applicability context, includes an explicit percentage
    goal, and carries a non-future confirmation timestamp. Demographic fields never
    auto-promote a guideline target.
    """
    # Force a registry lookup so a deleted/renamed supporting source fails loudly in
    # tests/release review rather than silently creating an orphaned target contract.
    get_evidence(TARGET_SUPPORTING_EVIDENCE_ID)

    if profile.target_range_provenance != "clinician_confirmed":
        return _snapshot(profile, reason_code="target_not_clinician_confirmed")
    if profile.diabetes_type is None:
        return _snapshot(profile, reason_code="target_diabetes_type_unknown")
    if profile.target_population_context == "unknown":
        return _snapshot(profile, reason_code="target_population_unknown")
    if profile.target_confirmed_at is None:
        return _snapshot(profile, reason_code="target_confirmation_missing")

    current = now or timezone.now()
    if profile.target_confirmed_at > current:
        return _snapshot(profile, reason_code="target_confirmation_future")

    low = float(profile.target_range_low)
    high = float(profile.target_range_high)
    if not (isfinite(low) and isfinite(high)):
        return _snapshot(profile, reason_code="target_range_non_finite")
    if not (
        log_input.GLUCOSE_MIN_MG_DL <= low < high <= log_input.GLUCOSE_MAX_MG_DL
    ):
        return _snapshot(profile, reason_code="target_range_invalid")

    goal = profile.target_time_in_range_goal_pct
    if goal is None:
        return _snapshot(profile, reason_code="target_percentage_goal_missing")
    goal_value = float(goal)
    if not isfinite(goal_value) or not (0.0 <= goal_value <= 100.0):
        return _snapshot(profile, reason_code="target_percentage_goal_invalid")

    return _snapshot(
        profile,
        reason_code="target_authority_verified",
        verified=True,
    )


def build_target_assessment(
    authority: TargetAuthority,
    *,
    cgm_verified: bool,
    target_range_pct: float | None,
) -> dict[str, object]:
    """Compare verified CGM time-in-range with a verified patient-specific goal."""
    base = authority.to_metadata()
    base["target_range_pct"] = None
    base["status"] = "unavailable"

    if not authority.verified:
        return base
    if not cgm_verified:
        base["reason_code"] = "target_cgm_window_not_verified"
        return base
    if target_range_pct is None or not isfinite(float(target_range_pct)):
        base["reason_code"] = "target_range_metric_unavailable"
        return base

    measured = round(float(target_range_pct), 1)
    goal = float(authority.target_time_in_range_goal_pct)
    base["target_range_pct"] = measured
    base["reason_code"] = "target_goal_comparison_available"
    base["status"] = (
        "meets_confirmed_goal" if measured >= goal else "below_confirmed_goal"
    )
    return base


def target_narration_evidence(assessment: dict[str, object]) -> str:
    """Return an LLM-safe evidence sentence only for an authorized comparison."""
    status = assessment.get("status")
    if status not in {"meets_confirmed_goal", "below_confirmed_goal"}:
        return ""

    measured = float(assessment["target_range_pct"])
    low = float(assessment["target_low_mg_dl"])
    high = float(assessment["target_high_mg_dl"])
    goal = float(assessment["target_time_in_range_goal_pct"])
    relation = "meets" if status == "meets_confirmed_goal" else "is below"
    return (
        "CLINICIAN-CONFIRMED TARGET EVIDENCE: verified CGM time inside the explicitly "
        f"confirmed {low:g}–{high:g} mg/dL range is {measured:g}%; this {relation} the "
        f"recorded minimum goal of {goal:g}%. {_TARGET_LIMITATION}"
    )
