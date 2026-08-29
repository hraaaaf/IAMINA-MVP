"""Central deterministic safety decision for text inputs."""

import re
from dataclasses import dataclass

from core.medical_safety import (
    is_insulin_prescription_request,
    is_treatment_prescription_request,
)
from core.triage_classification import TriageClass, classify
from core.vital_distress import detect_vital_distress


@dataclass(frozen=True)
class InputSafetyDecision:
    action: str
    reason: str | None = None


ALLOW = "ALLOW"
URGENT = "URGENT"
INSULIN_BLOCK = "INSULIN_BLOCK"
PRESCRIPTION_BLOCK = "PRESCRIPTION_BLOCK"

# Deterministic Arabic/dialect coverage for explicit insulin-dose requests.
# Keep educational insulin questions outside this boundary.
_ARABIC_INSULIN_DOSE_PATTERNS = (
    re.compile(
        r"(?:كم|شحال|جم)\s*(?:من\s+)?(?:وحدة|وحدات)?[^؟?\n]{0,40}"
        r"(?:ال)?[إأا]نسولين"
    ),
    re.compile(
        r"(?:ال)?[إأا]نسولين[^؟?\n]{0,40}(?:كم|شحال|جم)\s*(?:من\s+)?"
        r"(?:وحدة|وحدات)?"
    ),
    re.compile(r"(?:جرعة|الجرعة)[^؟?\n]{0,24}(?:ال)?[إأا]نسولين"),
)


def _is_arabic_insulin_dose_request(message: str | None) -> bool:
    if not message:
        return False
    return any(pattern.search(message) for pattern in _ARABIC_INSULIN_DOSE_PATTERNS)


def evaluate_input_safety(
    message: str | None,
    language: str | None = None,
) -> InputSafetyDecision:
    """Return the deterministic pre-LLM decision for a text message."""
    del language
    classification = classify(message or "")
    if classification is TriageClass.SUICIDAL_IDEATION:
        return InputSafetyDecision(URGENT, "suicidal_ideation")
    if classification is TriageClass.GLYCEMIC_EMERGENCY:
        return InputSafetyDecision(URGENT, "glycemic_emergency")
    if detect_vital_distress(message):
        return InputSafetyDecision(URGENT, "vital_distress")
    if is_insulin_prescription_request(message) or _is_arabic_insulin_dose_request(message):
        return InputSafetyDecision(INSULIN_BLOCK, "insulin_prescription")
    if is_treatment_prescription_request(message):
        return InputSafetyDecision(PRESCRIPTION_BLOCK, "treatment_prescription")
    return InputSafetyDecision(ALLOW)
