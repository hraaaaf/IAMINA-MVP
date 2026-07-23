"""
ClinicalLogger — structured technical monitoring.

Writes to the Python file logger only. Zero DB writes.
No PHI allowed in any parameter.

Usage:
    from core.observability import ClinicalLogger
    ClinicalLogger.analysis("hyperglycemia", patient_id=42, pattern_count=3, duration_ms=12.5)
"""

import json
import logging

_clinical = logging.getLogger("amina.clinical")


class ClinicalLogger:
    """Structured technical monitoring — file logger only, zero DB writes."""

    @staticmethod
    def analysis(condition: str, patient_id: int, pattern_count: int, duration_ms: float) -> None:
        """Log a clinical analysis event."""
        _clinical.info(json.dumps({
            "event":         "clinical_analysis",
            "condition":     condition,
            "patient_id":    patient_id,
            "pattern_count": pattern_count,
            "duration_ms":   duration_ms,
        }))

    @staticmethod
    def emergency(condition: str, patient_id: int, kind: str, language: str) -> None:
        """Log a clinical emergency detection event."""
        _clinical.info(json.dumps({
            "event":      "clinical_emergency",
            "condition":  condition,
            "patient_id": patient_id,
            "kind":       kind,
            "language":   language,
        }))

    @staticmethod
    def llm_call(provider: str, tokens: int, duration_ms: float, from_cache: bool) -> None:
        """Log an LLM call event."""
        _clinical.info(json.dumps({
            "event":      "llm_call",
            "provider":   provider,
            "tokens":     tokens,
            "duration_ms": duration_ms,
            "from_cache": from_cache,
        }))

    @staticmethod
    def middleware_intercept(middleware: str, reason: str) -> None:
        """Log a middleware interception event."""
        _clinical.info(json.dumps({
            "event":      "middleware_intercept",
            "middleware": middleware,
            "reason":     reason,
        }))
