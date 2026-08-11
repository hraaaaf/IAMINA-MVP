"""Executable capability/authority contract for IAmina.

The policy distinguishes *what the product may do* from *which authority may
make that decision*. Generative models remain narration/orchestration tools;
they are not medical decision authorities.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Authority(str, Enum):
    USER = "user"
    DETERMINISTIC_ENGINE = "deterministic_engine"
    GENERATIVE_MODEL = "generative_model"
    SYSTEM = "system"


class Capability(str, Enum):
    EXPLAIN_APPROVED_DATA = "explain_approved_data"
    SUMMARIZE_APPROVED_DATA = "summarize_approved_data"
    SURFACE_DETERMINISTIC_PATTERN = "surface_deterministic_pattern"
    PREPARE_CLINICIAN_QUESTIONS = "prepare_clinician_questions"
    RECORD_USER_CLAIM = "record_user_claim"
    UPDATE_USER_PREFERENCE = "update_user_preference"
    CLASSIFY_EMERGENCY = "classify_emergency"
    DIAGNOSE = "diagnose"
    PRESCRIBE = "prescribe"
    CALCULATE_DOSE = "calculate_dose"
    OPTIMIZE_TREATMENT = "optimize_treatment"
    CHANGE_TREATMENT = "change_treatment"
    PROMOTE_MODEL_INFERENCE_TO_FACT = "promote_model_inference_to_fact"
    AUTONOMOUS_CLINICAL_RECORD_WRITE = "autonomous_clinical_record_write"


@dataclass(frozen=True)
class CapabilityRule:
    allowed_authorities: frozenset[Authority]
    requires_user_confirmation: bool = False


_RULES: dict[Capability, CapabilityRule] = {
    Capability.EXPLAIN_APPROVED_DATA: CapabilityRule(
        frozenset({Authority.GENERATIVE_MODEL, Authority.DETERMINISTIC_ENGINE})
    ),
    Capability.SUMMARIZE_APPROVED_DATA: CapabilityRule(
        frozenset({Authority.GENERATIVE_MODEL, Authority.DETERMINISTIC_ENGINE})
    ),
    Capability.SURFACE_DETERMINISTIC_PATTERN: CapabilityRule(
        frozenset({Authority.DETERMINISTIC_ENGINE, Authority.GENERATIVE_MODEL})
    ),
    Capability.PREPARE_CLINICIAN_QUESTIONS: CapabilityRule(
        frozenset({Authority.GENERATIVE_MODEL, Authority.DETERMINISTIC_ENGINE})
    ),
    Capability.RECORD_USER_CLAIM: CapabilityRule(
        frozenset({Authority.USER, Authority.SYSTEM}),
        requires_user_confirmation=True,
    ),
    Capability.UPDATE_USER_PREFERENCE: CapabilityRule(
        frozenset({Authority.USER, Authority.SYSTEM}),
        requires_user_confirmation=True,
    ),
    Capability.CLASSIFY_EMERGENCY: CapabilityRule(
        frozenset({Authority.DETERMINISTIC_ENGINE})
    ),
    Capability.DIAGNOSE: CapabilityRule(frozenset()),
    Capability.PRESCRIBE: CapabilityRule(frozenset()),
    Capability.CALCULATE_DOSE: CapabilityRule(frozenset()),
    Capability.OPTIMIZE_TREATMENT: CapabilityRule(frozenset()),
    Capability.CHANGE_TREATMENT: CapabilityRule(frozenset()),
    Capability.PROMOTE_MODEL_INFERENCE_TO_FACT: CapabilityRule(frozenset()),
    Capability.AUTONOMOUS_CLINICAL_RECORD_WRITE: CapabilityRule(frozenset()),
}


def rule_for(capability: Capability) -> CapabilityRule:
    return _RULES[capability]


def capability_allowed(capability: Capability, authority: Authority) -> bool:
    return authority in rule_for(capability).allowed_authorities


def assert_capability_allowed(capability: Capability, authority: Authority) -> None:
    if not capability_allowed(capability, authority):
        raise PermissionError(
            f"{authority.value} is not allowed to perform capability {capability.value}"
        )
