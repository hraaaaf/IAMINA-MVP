"""Execution-integrity wrapper for the active evidence-gated diabetes analysis.

Clinical detector failures are deliberately fail-soft for availability, but they
must never be indistinguishable from a complete analysis. This module preserves
the deterministic clinical engine behavior while returning stable, PHI-free
technical degradation codes to the public authority boundary.
"""
from __future__ import annotations

import logging

from . import engine
from .sql_analytics import AnalyticalKPIs

logger = logging.getLogger(__name__)


def _detector_code(detector) -> str:
    name = getattr(detector, "__name__", "unknown")
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    return f"detector_failed_{safe or 'unknown'}"


def run_clinical_analysis_with_integrity(
    entries,
    kpis: AnalyticalKPIs,
    language: str = "fr",
) -> tuple[engine.ClinicalReport, list[str]]:
    """Run active deterministic detectors and expose any partial-execution state.

    Degradation codes are technical only. They contain neither patient data nor
    exception text. A failed detector is skipped, preserving the existing
    fail-soft behavior, while the caller can mark the overall analysis partial.
    """
    entries = list(entries)
    patterns = []
    degradations: list[str] = []

    try:
        cgm_variability = engine._high_variability_from_kpis(kpis)
        if cgm_variability is not None:
            patterns.append(cgm_variability)
    except Exception:
        logger.exception("ClinicalEngine: KPI-backed variability detector failed")
        degradations.append("detector_failed_cgm_variability")

    for detector in engine._ACTIVE_ENTRY_DETECTORS:
        try:
            result = detector(entries)
            if result is not None:
                patterns.append(result)
        except Exception:
            detector_name = getattr(detector, "__name__", repr(detector))
            logger.exception("ClinicalEngine: detector %s failed", detector_name)
            degradations.append(_detector_code(detector))

    patterns.sort(key=lambda p: (p.priority, p.code))
    insights = engine._format_with_llm(patterns, language) if patterns else []
    report = engine.ClinicalReport(kpis=kpis, patterns=patterns, insights=insights)
    return report, sorted(set(degradations))
