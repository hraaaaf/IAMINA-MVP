"""Central deterministic safety decision for text inputs."""

from dataclasses import dataclass

from core.medical_safety import (
    is_insulin_prescription_request,
    is_treatment_prescription_request,
)
from core.middleware.triage_vital import detect_vital_distress
from core.triage_classification import TriageClass, classify


@dataclass(frozen=True)
class InputSafetyDecision:
    action: str
    reason: str | None = None


ALLOW = "ALLOW"
URGENT = "URGENT"
INSULIN_BLOCK = "INSULIN_BLOCK"
PRESCRIPTION_BLOCK = "PRESCRIPTION_BLOCK"


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
    if detect_vital_distress(message or ""):
        return InputSafetyDecision(URGENT, "vital_distress")
    if is_insulin_prescription_request(message):
        return InputSafetyDecision(INSULIN_BLOCK, "insulin_prescription")
    if is_treatment_prescription_request(message):
        return InputSafetyDecision(PRESCRIPTION_BLOCK, "treatment_prescription")
    return InputSafetyDecision(ALLOW)
