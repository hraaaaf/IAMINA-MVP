"""Condition-agnostic clinical narration policy.

This chassis policy is deliberately conservative. It authorizes only L0
conversation and L1 explanation/clinician-preparation. Condition modules may add
L2/L3 rule families later, but no model call may manufacture that authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.capabilities import Capability


class NarrationMode(StrEnum):
    PRACTICAL = "practical"
    EMOTIONAL = "emotional"
    CLINICIAN_PREP = "clinician_prep"
    RECAP = "recap"


@dataclass(frozen=True, slots=True)
class NarrationPolicyRequest:
    mode: NarrationMode
    language: str
    has_approved_context: bool
    has_sufficient_data: bool
    analysis_status: str = "complete"


_CLINICAL_ACTION_BARRIER = (
    "patient_facing_clinical_action",
    Capability.DIAGNOSE.value,
    Capability.PRESCRIBE.value,
    Capability.CALCULATE_DOSE.value,
    Capability.OPTIMIZE_TREATMENT.value,
    Capability.CHANGE_TREATMENT.value,
)


def authorize_narration(request: NarrationPolicyRequest) -> AdviceDecision:
    """Return the highest authority allowed before narration begins."""

    if request.analysis_status in {"partial", "unavailable"}:
        return AdviceDecision.fail_closed(language=request.language)

    if request.mode is NarrationMode.EMOTIONAL:
        return AdviceDecision(
            intent="conversation_emotional_support",
            authority_level=AdviceAuthorityLevel.L0_CONVERSATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="core.narration.emotional",
            rule_version="1",
            forbidden_actions=_CLINICAL_ACTION_BARRIER,
            limitations=("no_clinical_action",),
            language=request.language,
        )

    if request.mode is NarrationMode.CLINICIAN_PREP:
        return AdviceDecision(
            intent="clinician_preparation",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="core.narration.clinician_prep",
            rule_version="1",
            allowed_actions=(Capability.PREPARE_CLINICIAN_QUESTIONS.value,),
            forbidden_actions=_CLINICAL_ACTION_BARRIER,
            limitations=("questions_only", "no_treatment_selection"),
            language=request.language,
        )

    if (
        request.has_approved_context
        and request.has_sufficient_data
        and request.mode is NarrationMode.RECAP
    ):
        return AdviceDecision(
            intent="summarize_approved_clinical_context",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="core.narration.approved_summary",
            rule_version="1",
            allowed_actions=(
                Capability.SUMMARIZE_APPROVED_DATA.value,
                Capability.EXPLAIN_APPROVED_DATA.value,
            ),
            forbidden_actions=_CLINICAL_ACTION_BARRIER,
            limitations=("descriptive_only", "no_new_clinical_action"),
            language=request.language,
        )

    if request.has_approved_context and request.has_sufficient_data:
        return AdviceDecision(
            intent="explain_approved_clinical_context",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="core.narration.approved_context",
            rule_version="1",
            allowed_actions=(Capability.EXPLAIN_APPROVED_DATA.value,),
            forbidden_actions=_CLINICAL_ACTION_BARRIER,
            limitations=("descriptive_only", "no_new_clinical_action"),
            language=request.language,
        )

    return AdviceDecision(
        intent="conversation_without_clinical_authority",
        authority_level=AdviceAuthorityLevel.L0_CONVERSATION,
        decision=AdviceDisposition.CONSTRAIN,
        rule_id="core.narration.conversation",
        rule_version="1",
        forbidden_actions=_CLINICAL_ACTION_BARRIER,
        limitations=("no_clinical_context_authority",),
        language=request.language,
    )


def narration_authorized(decision: AdviceDecision) -> bool:
    return (
        decision.decision in {AdviceDisposition.ALLOW, AdviceDisposition.CONSTRAIN}
        and decision.authority_level
        not in {
            AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION,
            AdviceAuthorityLevel.L5_PROHIBITED,
        }
    )


def narration_policy_block(decision: AdviceDecision) -> str:
    """Compact PHI-free contract passed to the narrator as a constraint."""

    allowed = ",".join(decision.allowed_actions) or "none"
    forbidden = ",".join(decision.forbidden_actions) or "none"
    return (
        "[ADVICE_AUTHORITY]\n"
        f"level={decision.authority_level.value};"
        f"decision={decision.decision.value};"
        f"rule={decision.rule_id}@{decision.rule_version}\n"
        f"allowed_actions={allowed}\n"
        f"forbidden_actions={forbidden}\n"
        "Do not add any patient action that is absent from allowed_actions."
    )


__all__ = [
    "NarrationMode",
    "NarrationPolicyRequest",
    "authorize_narration",
    "narration_authorized",
    "narration_policy_block",
]
