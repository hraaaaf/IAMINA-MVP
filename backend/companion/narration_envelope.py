"""Shadow-mode narration envelope helpers.

Shadow mode is deliberately non-authoritative: it builds and validates the
future narrator contract without changing the patient-visible reply or calling
an LLM.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from core.contracts.advice_decision import AdviceDecision
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.capabilities import Capability
from core.contracts.narration_envelope import (
    LocaleContract,
    NarrationEnvelope,
    NarrationEnvelopeError,
    NarrationFact,
    NarrationSpeechAct,
)

_FACT_TOKEN_RE = re.compile(r"\{\{(FACT_[A-Z0-9_]+)\}\}")
_CLINICAL_NUMBER_RE = re.compile(
    r"(?<!\w)\d{1,4}(?:[.,]\d+)?\s*(?:"
    r"mg\s*/\s*d[lL]|mmol\s*/\s*[lL]|mm\s*Hg|bpm|%|"
    r"(?:IU|UI|U)\b|ملغ\s*/\s*دل|مليمول\s*/\s*ل|وحد(?:ة|ات))",
    re.IGNORECASE,
)


class NarrationVerificationError(PermissionError):
    """Raised when model-formulated text violates its narration envelope."""


@dataclass(frozen=True, slots=True)
class ShadowNarrationResult:
    envelope: NarrationEnvelope
    source_reply: str
    structurally_valid: bool


def _speech_act(decision: AdviceDecision) -> NarrationSpeechAct:
    actions = set(decision.allowed_actions)
    if Capability.PREPARE_CLINICIAN_QUESTIONS.value in actions:
        return NarrationSpeechAct.PREPARE_CLINICIAN_QUESTIONS
    if Capability.SUMMARIZE_APPROVED_DATA.value in actions:
        return NarrationSpeechAct.SUMMARIZE_APPROVED_DATA
    if Capability.EXPLAIN_APPROVED_DATA.value in actions:
        return NarrationSpeechAct.EXPLAIN_APPROVED_DATA
    return NarrationSpeechAct.RESTATE_GOVERNED_ADVICE


def locale_contract(
    language: str,
    *,
    prefer_latin_script: bool = False,
) -> LocaleContract:
    if language == "ar-MA":
        return LocaleContract(
            locale=language,
            script="latin" if prefer_latin_script else "arabic",
            register="casual-native",
            code_switching=prefer_latin_script,
        )
    if language.startswith("ar-"):
        return LocaleContract(
            locale=language,
            script="arabic",
            register="daily-natural",
            code_switching=False,
        )
    return LocaleContract(
        locale=language,
        script="default",
        register="natural",
        code_switching=False,
    )


def build_shadow_envelope(
    resolution: AdviceResolution,
    *,
    language: str,
    prefer_latin_script: bool = False,
    facts: tuple[NarrationFact, ...] = (),
) -> NarrationEnvelope:
    """Build a local envelope without exposing the deterministic reply to a model."""
    if not isinstance(resolution, AdviceResolution):
        raise NarrationEnvelopeError("resolution must be an AdviceResolution")

    decision = resolution.decision
    return NarrationEnvelope(
        decision=decision,
        speech_act=_speech_act(decision),
        locale=locale_contract(
            language,
            prefer_latin_script=prefer_latin_script,
        ),
        facts=facts,
        allowed_claims=tuple(decision.required_facts),
        required_claims=tuple(decision.required_facts),
        forbidden_claims=tuple(decision.forbidden_actions),
        relationship_context={},
        style_contract={
            "goal": "formulation_only",
            "clinical_reasoning": "forbidden",
            "authority_change": "forbidden",
        },
        fallback_reply=resolution.reply,
        verifier_id="structural-shadow.v1",
    )


def verify_and_reinject_narration(
    candidate: str,
    envelope: NarrationEnvelope,
) -> str:
    """Validate token integrity then locally restore protected fact values.

    This structural verifier intentionally does not claim semantic equivalence.
    Family-specific semantic verifiers remain authoritative for clinical meaning.
    """
    if not isinstance(candidate, str) or not candidate.strip():
        raise NarrationVerificationError("candidate must be non-empty")

    known = {fact.key: fact for fact in envelope.facts}
    observed = set(_FACT_TOKEN_RE.findall(candidate))
    unknown = observed - set(known)
    if unknown:
        raise NarrationVerificationError("candidate contains unknown fact tokens")

    for fact in envelope.facts:
        if fact.required and fact.key not in observed:
            raise NarrationVerificationError(
                f"candidate omitted required fact token {fact.key}"
            )
        if fact.egress_policy.value == "local_only" and fact.rendered_value in candidate:
            raise NarrationVerificationError(
                f"candidate exposed local-only fact value {fact.key}"
            )

    scrubbed = _FACT_TOKEN_RE.sub("", candidate)
    if _CLINICAL_NUMBER_RE.search(scrubbed):
        raise NarrationVerificationError(
            "candidate introduced an untokenized clinical number"
        )

    result = candidate
    for fact in envelope.facts:
        result = result.replace(fact.token, fact.rendered_value)

    if _FACT_TOKEN_RE.search(result):
        raise NarrationVerificationError("unresolved fact token remains")
    return result.strip()


def shadow_validate_resolution(
    resolution: AdviceResolution,
    *,
    language: str,
    prefer_latin_script: bool = False,
) -> ShadowNarrationResult:
    """Exercise the envelope contract without changing runtime output."""
    envelope = build_shadow_envelope(
        resolution,
        language=language,
        prefer_latin_script=prefer_latin_script,
    )
    return ShadowNarrationResult(
        envelope=envelope,
        source_reply=resolution.reply,
        structurally_valid=True,
    )


__all__ = [
    "NarrationVerificationError",
    "ShadowNarrationResult",
    "build_shadow_envelope",
    "locale_contract",
    "shadow_validate_resolution",
    "verify_and_reinject_narration",
]
