"""
IAmina — Semantic Compressor (Phase 6)
========================================
Transforms structured SQL KPIs + clinical patterns into a compact English
technical summary. This summary is the ONLY input sent to the LLM, replacing
raw number lists.

English Pivot rationale:
- LLMs benchmark 15-20% higher on clinical reasoning tasks in English.
- Token density is higher in English → lower API costs.
- PHIPseudonymizer has already stripped PII before this layer is called.

See docs/adr/0007-analytical-sql-over-llm.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..clinical.engine import ClinicalPattern
from .sql_analytics import AnalyticalKPIs

# ──────────────────────────────────────────────────────────────
# 1. OUTPUT STRUCTURE
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CompressedContext:
    """
    The minimal, LLM-ready English summary produced by the compressor.
    No raw number arrays are passed further — only this object.
    """
    kpi_summary: str            # One paragraph: KPI narrative
    pattern_summary: str        # Bullet-list: detected clinical patterns
    full_pivot_text: str        # Combined text sent to LLM


# ──────────────────────────────────────────────────────────────
# 2. KPI NARRATIVE BUILDER
# ──────────────────────────────────────────────────────────────

def _build_kpi_narrative(kpis: AnalyticalKPIs) -> str:
    """
    Converts AnalyticalKPIs into a dense, medically precise English sentence block.
    Units are always explicit to prevent Unit Guard bypass at the LLM layer.
    """
    if not kpis.has_sufficient_data:
        return (
            f"Insufficient data: only {kpis.log_count} glucose readings recorded "
            f"over {kpis.days_with_data} day(s). Clinical analysis requires ≥5 entries. "
            "Encourage the patient to log more frequently before generating a full report."
        )

    lines: list[str] = [
        f"ANALYSIS WINDOW: {kpis.days_with_data} days | {kpis.log_count} readings (all values in mg/dL).",
        "",
        "GLYCEMIC CONTROL METRICS:",
    ]

    # Average glucose
    if kpis.avg_glucose is not None:
        gmi_note = (
            f" → Estimated HbA1c (GMI): {kpis.gmi}%"
            if kpis.gmi is not None else ""
        )
        lines.append(f"  • Mean glucose: {kpis.avg_glucose} mg/dL.{gmi_note}")

    # Variability
    if kpis.std_dev is not None and kpis.cv_pct is not None:
        stability = "STABLE" if kpis.is_stable else "UNSTABLE (above ADA threshold)"
        lines.append(
            f"  • Glycemic variability: SD={kpis.std_dev} mg/dL, CV={kpis.cv_pct}% "
            f"[ADA target ≤36%] → {stability}."
        )

    # TIR / TAR / TBR
    if kpis.tir_pct is not None:
        tir_status = "MEETS TARGET" if kpis.tir_pct >= 70 else "BELOW TARGET (needs improvement)"
        lines.append(
            f"  • Time In Range (70-180 mg/dL): {kpis.tir_pct}% "
            f"[ADA target ≥70%] → {tir_status}."
        )
    if kpis.tar_pct is not None:
        lines.append(f"  • Time Above Range (>180 mg/dL): {kpis.tar_pct}%.")
    if kpis.tbr_pct is not None:
        hypoglycemia_flag = " ⚠ HYPOGLYCEMIA RISK" if (kpis.tbr_pct or 0) > 4 else ""
        lines.append(f"  • Time Below Range (<70 mg/dL): {kpis.tbr_pct}%.{hypoglycemia_flag}")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# 3. PATTERN SUMMARY BUILDER
# ──────────────────────────────────────────────────────────────

_PRIORITY_LABEL = {1: "CRITICAL", 2: "IMPORTANT", 3: "INFORMATIONAL"}


def _build_pattern_summary(patterns: list[ClinicalPattern]) -> str:
    """
    Converts detected clinical patterns into a structured English bullet list.
    Only evidence strings (already in EN or bilingual) are used — no French UI text.
    """
    if not patterns:
        return "DETECTED PATTERNS: None. All clinical indicators are within normal range."

    lines = ["DETECTED CLINICAL PATTERNS (in order of priority):"]
    for i, p in enumerate(patterns, 1):
        priority_str = _PRIORITY_LABEL.get(p.priority, f"P{p.priority}")
        lines.append(
            f"  {i}. [{priority_str}] {p.code}: {p.evidence}"
        )
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# 4. CHAT CONTEXT BUILDER (for conversational endpoint)
# ──────────────────────────────────────────────────────────────

def build_chat_context(kpis: AnalyticalKPIs, patterns: list[ClinicalPattern]) -> str:
    """
    Minimal context injected into chat prompts.
    Intentionally shorter than the summary context to reduce token cost per turn.
    """
    if not kpis.has_sufficient_data:
        return f"Patient has only {kpis.log_count} glucose log(s). Encourage more frequent logging."

    parts: list[str] = []

    if kpis.avg_glucose:
        parts.append(f"avg glucose {kpis.avg_glucose} mg/dL")
    if kpis.tir_pct is not None:
        parts.append(f"TIR {kpis.tir_pct}%")
    if kpis.gmi:
        parts.append(f"GMI {kpis.gmi}%")
    if kpis.cv_pct is not None:
        stability = "stable" if kpis.is_stable else f"unstable (CV {kpis.cv_pct}%)"
        parts.append(f"variability {stability}")

    kpi_line = "Current KPIs: " + ", ".join(parts) + "." if parts else ""

    pattern_line = ""
    if patterns:
        codes = ", ".join(p.code for p in patterns[:3])  # max 3 to keep context tight
        pattern_line = f"Active clinical alerts: {codes}."

    return " ".join(filter(None, [kpi_line, pattern_line]))


# ──────────────────────────────────────────────────────────────
# 5. MAIN COMPRESSOR
# ──────────────────────────────────────────────────────────────

def compress(
    kpis: AnalyticalKPIs,
    patterns: list[ClinicalPattern],
    patient_language: str = "fr",
) -> CompressedContext:
    """
    Main compressor entry point.

    Args:
        kpis: Pre-computed SQL KPIs.
        patterns: Detected clinical patterns from the rules engine.
        patient_language: Patient's preferred language (fr | ar-MA).
                          Used only for the LLM output instruction, not the input.

    Returns:
        CompressedContext with the full English pivot text ready for LLM injection.
    """
    kpi_summary = _build_kpi_narrative(kpis)
    pattern_summary = _build_pattern_summary(patterns)

    # Language instruction appended so the LLM knows which language to respond in
    language_map = {"fr": "French", "ar-MA": "Moroccan Darija (Arabic dialect)"}
    output_lang = language_map.get(patient_language, "French")
    output_instruction = (
        f"\nOUTPUT LANGUAGE: Respond in {output_lang}. "
        "Use empathetic, medically precise language. Never prescribe; recommend consulting the physician."
    )

    full_pivot_text = "\n\n".join([kpi_summary, pattern_summary, output_instruction])

    return CompressedContext(
        kpi_summary=kpi_summary,
        pattern_summary=pattern_summary,
        full_pivot_text=full_pivot_text,
    )
