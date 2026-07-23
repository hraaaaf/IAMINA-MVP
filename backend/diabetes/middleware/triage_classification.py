"""Backward-compatible import surface for deterministic triage classification.

The authoritative classifier now lives in ``core.triage_classification`` so the
shared pre-LLM safety gate does not depend on the diabetes module.
"""

from core.triage_classification import (
    CRISIS_RESOURCES,
    TriageClass,
    classify,
    crisis_support_response,
    select_triage_response,
)

__all__ = [
    "CRISIS_RESOURCES",
    "TriageClass",
    "classify",
    "crisis_support_response",
    "select_triage_response",
]
