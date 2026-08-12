"""
IAmina semantic compressor.

Transforms SQL-first KPIs plus approved deterministic observations into a compact
narration context. It never upgrades insufficient/manual data into a CGM target
judgment and never treats the absence of an eligible observation as proof that
"everything is normal".
"""

from __future__ import annotations

from dataclasses import dataclass

from diabetes.services.clinical.cgm_eligibility import assess_cgm_sufficiency
from diabetes.services.clinical.engine import ClinicalPattern
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


@dataclass(frozen=True)
class CompressedContext:
    kpi_summary: str
    pattern_summary: str
    full_pivot_text: str


def _eligible_cgm_window(kpis: AnalyticalKPIs) -> bool:
    """Use the shared fail-closed CGM sufficiency contract."""
    return assess_cgm_sufficiency(kpis).verified


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

    cgm_sufficiency = assess_cgm_sufficiency(kpis)
    if kpis.gmi is not None:
        if cgm_sufficiency.verified:
            lines.append(
                f"  • GMI: {kpis.gmi}% ({kpis.gmi_basis}). "
                "GMI is derived from CGM mean glucose and is not equivalent to a laboratory A1C."
            )
        else:
            lines.append(
                "  • GMI not surfaced: the current data model cannot verify sensor wear-time/cadence "
                "coverage required for a clinically governed CGM interpretation."
            )

    if kpis.cv_pct is not None:
        if cgm_sufficiency.verified:
            cv_context = (
                "within the ADA 2026 general CGM reference (≤36%)"
                if kpis.cv_pct <= 36.0
                else "above the ADA 2026 general CGM reference (>36%)"
            )
            lines.append(
                f"  • CGM coefficient of variation: {kpis.cv_pct}% — {cv_context}."
            )
        else:
            lines.append(
                f"  • Recorded-data coefficient of variation: {kpis.cv_pct}%. "
                "Do not apply a normative CGM variability reference because true sensor "
                "wear-time/cadence coverage is not available in the current schema."
            )

    if kpis.tir_pct is not None:
        if cgm_sufficiency.verified:
            lines.append(
                f"  • CGM Time In Range 70–180 mg/dL: {kpis.tir_pct}%. "
                "General targets require individual clinical context."
            )
        else:
            lines.append(
                f"  • Fraction of recorded values in 70–180 mg/dL: {kpis.tir_pct}%. "
                "Do not present this as validated CGM TIR or as a population target assessment."
            )

    if kpis.tar_pct is not None:
        lines.append(f"  • Fraction of recorded values >180 mg/dL: {kpis.tar_pct}%.")
    if kpis.tbr_pct is not None:
        lines.append(f"  • Fraction of recorded values <70 mg/dL: {kpis.tbr_pct}%.")

    if kpis.cgm_active_pct is not None:
        lines.append(
            f"  • Rows carrying CGM provenance: {kpis.cgm_active_pct}% of stored readings. "
            "This is provenance, not sensor wear-time."
        )

    lines.append(
        "INTERPRETATION LIMIT: metrics describe the eligible recorded data; they do not "
        "diagnose a condition or authorize a medication/dose change."
    )
    return "\n".join(lines)


def _build_pattern_summary(patterns: list[ClinicalPattern]) -> str:
    """Serialize evidence-qualified observations for narration."""
    if not patterns:
        return (
            "ELIGIBLE DETERMINISTIC OBSERVATIONS: none surfaced by the currently enabled "
            "rules. This does NOT mean all clinical indicators are normal."
        )

    lines = ["ELIGIBLE DETERMINISTIC OBSERVATIONS:"]
    for index, pattern in enumerate(patterns, 1):
        lines.append(f"  {index}. {pattern.narration_evidence()}")
    return "\n".join(lines)


def build_chat_context(kpis: AnalyticalKPIs, patterns: list[ClinicalPattern]) -> str:
    """Minimal chat context; no clinical-alert or treatment language."""
    if not kpis.has_sufficient_data:
        return (
            f"Recorded data are limited ({kpis.log_count} glucose log(s)). "
            "Do not infer normality or causality."
        )

    cgm_sufficiency = assess_cgm_sufficiency(kpis)
    parts: list[str] = []
    if kpis.avg_glucose is not None:
        parts.append(f"recorded mean glucose {kpis.avg_glucose} mg/dL")
    if cgm_sufficiency.verified and kpis.gmi is not None:
        parts.append(f"eligible CGM GMI {kpis.gmi}%")
    if cgm_sufficiency.verified and kpis.tir_pct is not None:
        parts.append(f"eligible CGM TIR {kpis.tir_pct}%")

    kpi_line = "Current deterministic metrics: " + ", ".join(parts) + "." if parts else ""
    observation_line = ""
    if patterns:
        codes = ", ".join(pattern.code for pattern in patterns[:3])
        observation_line = (
            f"Evidence-qualified observation codes: {codes}. "
            "They are observations, not diagnoses or treatment instructions."
        )
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