"""
IAmina semantic compressor.

Transforms SQL-first KPIs plus approved deterministic observations into a compact
narration context. It never upgrades insufficient/manual data into a CGM target
judgment and never treats the absence of an eligible observation as proof that
"everything is normal".
"""

from __future__ import annotations

from dataclasses import dataclass

from ..clinical.engine import ClinicalPattern
from .sql_analytics import AnalyticalKPIs


@dataclass(frozen=True)
class CompressedContext:
    kpi_summary: str
    pattern_summary: str
    full_pivot_text: str


def _eligible_cgm_window(kpis: AnalyticalKPIs) -> bool:
    return (
        kpis.days_with_data >= 14
        and kpis.cgm_active_pct is not None
        and kpis.cgm_active_pct >= 70.0
    )


def _build_kpi_narrative(kpis: AnalyticalKPIs) -> str:
    """Build a descriptive KPI packet without unsupported target claims."""
    if not kpis.has_sufficient_data:
        return (
            f"DATA SUFFICIENCY: insufficient for the current analytical snapshot "
            f"({kpis.log_count} readings across {kpis.days_with_data} day(s)). "
            "Do not infer normality, deterioration, causality, or treatment action."
        )

    lines = [
        f"ANALYSIS WINDOW: {kpis.days_with_data} days | {kpis.log_count} recorded readings.",
        "DETERMINISTIC SQL METRICS:",
    ]

    if kpis.avg_glucose is not None:
        lines.append(f"  • Recorded mean glucose: {kpis.avg_glucose} mg/dL.")

    if kpis.gmi is not None:
        lines.append(
            f"  • GMI estimate: {kpis.gmi}% ({kpis.gmi_basis}). "
            "GMI is an estimate from glucose data and is not equivalent to a laboratory A1C."
        )

    cgm_eligible = _eligible_cgm_window(kpis)
    if kpis.cv_pct is not None:
        if cgm_eligible:
            cv_context = (
                "within the ADA 2026 general CGM reference (≤36%)"
                if kpis.cv_pct <= 36.0
                else "above the ADA 2026 general CGM reference (>36%)"
            )
            lines.append(
                f"  • CGM coefficient of variation: {kpis.cv_pct}% — {cv_context}; "
                f"CGM active {kpis.cgm_active_pct}% across {kpis.days_with_data} days."
            )
        else:
            lines.append(
                f"  • Recorded-data coefficient of variation: {kpis.cv_pct}%. "
                "Do not apply the CGM ≤36% reference because valid ≥14-day/≥70% CGM "
                "wear has not been established for this window."
            )

    if kpis.tir_pct is not None:
        if cgm_eligible:
            lines.append(
                f"  • CGM Time In Range 70–180 mg/dL: {kpis.tir_pct}%. "
                "General targets require individual clinical context."
            )
        else:
            lines.append(
                f"  • Fraction of recorded values in 70–180 mg/dL: {kpis.tir_pct}%. "
                "Do not present this sparse/manual ratio as a validated CGM TIR target assessment."
            )

    if kpis.tar_pct is not None:
        lines.append(f"  • Fraction of recorded values >180 mg/dL: {kpis.tar_pct}%.")
    if kpis.tbr_pct is not None:
        lines.append(f"  • Fraction of recorded values <70 mg/dL: {kpis.tbr_pct}%.")

    lines.append(
        "INTERPRETATION LIMIT: metrics describe the eligible recorded data; they do not "
        "diagnose a condition or authorize a medication/dose change."
    )
    return "\n".join(lines)


def _build_pattern_summary(patterns: list[ClinicalPattern]) -> str:
    """Serialize evidence-qualified observations for structured narration."""
    if not patterns:
        return (
            "ELIGIBLE DETERMINISTIC OBSERVATIONS: none surfaced by the currently enabled "
            "rules. This does NOT mean all clinical indicators are normal."
        )

    lines = ["ELIGIBLE DETERMINISTIC OBSERVATIONS:"]
    for index, pattern in enumerate(patterns, 1):
        lines.append(f"  {index}. {pattern.narration_evidence()}")
    return "\n".join(lines)


def _chat_observation_evidence(patterns: list[ClinicalPattern]) -> str:
    """Return descriptive evidence only; machine identifiers stay deterministic-only."""
    if not patterns:
        return ""

    observations = [
        f"Observation {index}: {pattern.evidence}"
        for index, pattern in enumerate(patterns[:3], 1)
    ]
    return (
        "Evidence-qualified deterministic observations (descriptive only): "
        + " ".join(observations)
        + " Use these observations only as stated; do not infer a named mechanism, "
        "diagnosis, cause, prescription, dose or treatment change."
    )


def build_chat_context(kpis: AnalyticalKPIs, patterns: list[ClinicalPattern]) -> str:
    """Minimal chat context using approved evidence, never detector identifiers."""
    if not kpis.has_sufficient_data:
        return (
            f"Recorded data are limited ({kpis.log_count} glucose log(s)). "
            "Do not infer normality or causality."
        )

    parts: list[str] = []
    if kpis.avg_glucose is not None:
        parts.append(f"recorded mean glucose {kpis.avg_glucose} mg/dL")
    if kpis.gmi is not None:
        parts.append(f"GMI estimate {kpis.gmi}%")
    if _eligible_cgm_window(kpis) and kpis.tir_pct is not None:
        parts.append(f"eligible CGM TIR {kpis.tir_pct}%")

    kpi_line = "Current deterministic metrics: " + ", ".join(parts) + "." if parts else ""
    observation_line = _chat_observation_evidence(patterns)
    return " ".join(filter(None, [kpi_line, observation_line]))


def compress(
    kpis: AnalyticalKPIs,
    patterns: list[ClinicalPattern],
    patient_language: str = "fr",
) -> CompressedContext:
    """Return the minimized, evidence-qualified text passed to the narrator."""
    kpi_summary = _build_kpi_narrative(kpis)
    pattern_summary = _build_pattern_summary(patterns)

    language_map = {
        "fr": "French",
        "ar-MA": "Moroccan Darija",
        "ar": "Modern Standard Arabic",
        "en": "English",
    }
    output_language = language_map.get(patient_language, "French")
    instruction = (
        f"OUTPUT LANGUAGE: Respond in {output_language}. "
        "Explain only the supplied deterministic metrics/observations. "
        "Do not add a diagnosis, causal mechanism, prescription, dose, treatment change, "
        "or unsupported normality claim. Preserve uncertainty and data-sufficiency limits."
    )

    full_pivot_text = "\n\n".join([kpi_summary, pattern_summary, instruction])
    return CompressedContext(
        kpi_summary=kpi_summary,
        pattern_summary=pattern_summary,
        full_pivot_text=full_pivot_text,
    )
