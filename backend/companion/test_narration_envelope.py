from __future__ import annotations

import pytest

from companion.narration_envelope import (
    NarrationVerificationError,
    build_shadow_envelope,
    locale_contract,
    shadow_validate_resolution,
    verify_and_reinject_narration,
)
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.capabilities import Capability
from core.contracts.narration_envelope import (
    FactEgressPolicy,
    NarrationFact,
    NarrationSpeechAct,
)


def _resolution() -> AdviceResolution:
    return AdviceResolution(
        decision=AdviceDecision(
            intent="explain_governed_observation",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.longitudinal.synthetic",
            rule_version="1",
            allowed_actions=(Capability.EXPLAIN_APPROVED_DATA.value,),
            forbidden_actions=(
                Capability.DIAGNOSE.value,
                Capability.PRESCRIBE.value,
                Capability.CALCULATE_DOSE.value,
            ),
            required_facts=("repeated_observation",),
            limitations=("descriptive_only",),
            language="ar-MA",
        ),
        reply="جواب حتمي وآمن.",
    )


def _fact() -> NarrationFact:
    return NarrationFact(
        key="FACT_GLUCOSE",
        semantic_type="glucose_value",
        rendered_value="187 mg/dL",
        egress_policy=FactEgressPolicy.LOCAL_ONLY,
        provenance_ref="log_entry:synthetic",
    )


def test_shadow_envelope_maps_existing_authority_without_expanding_it():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    assert envelope.speech_act is NarrationSpeechAct.EXPLAIN_APPROVED_DATA
    assert envelope.decision.authority_level is AdviceAuthorityLevel.L1_EDUCATION
    assert envelope.required_claims == ("repeated_observation",)
    assert Capability.DIAGNOSE.value in envelope.forbidden_claims
    assert envelope.fallback_reply == "جواب حتمي وآمن."


def test_provider_view_omits_local_fact_value_and_provenance():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    provider = envelope.provider_view()
    fact = provider["facts"][0]

    assert fact["token"] == "{{FACT_GLUCOSE}}"
    assert fact["provider_hint"] is None
    assert "187 mg/dL" not in repr(provider)
    assert "log_entry:synthetic" not in repr(provider)


def test_required_fact_token_is_reinjected_only_after_verification():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    result = verify_and_reinject_narration(
        "هاد القياس {{FACT_GLUCOSE}} باين فالملاحظة اللي عطاتها IAMINA.",
        envelope,
    )

    assert "{{FACT_GLUCOSE}}" not in result
    assert "187 mg/dL" in result


def test_unknown_or_missing_fact_tokens_fail_closed():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    with pytest.raises(NarrationVerificationError, match="unknown"):
        verify_and_reinject_narration(
            "هاد القياس {{FACT_UNKNOWN}}.",
            envelope,
        )

    with pytest.raises(NarrationVerificationError, match="omitted"):
        verify_and_reinject_narration(
            "هاد القياس باين فالملاحظة.",
            envelope,
        )


def test_candidate_cannot_expose_or_invent_untokenized_clinical_number():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    with pytest.raises(NarrationVerificationError, match="exact local"):
        verify_and_reinject_narration(
            "القياس 187 mg/dL و {{FACT_GLUCOSE}}.",
            envelope,
        )

    with pytest.raises(NarrationVerificationError, match="untokenized"):
        verify_and_reinject_narration(
            "القياس {{FACT_GLUCOSE}} وملاحظة ثانية 210 mg/dL.",
            envelope,
        )


def test_locale_contract_separates_darija_scripts_and_gulf_register():
    darija_latin = locale_contract("ar-MA", prefer_latin_script=True)
    darija_ar = locale_contract("ar-MA", prefer_latin_script=False)
    gulf = locale_contract("ar-AE")

    assert darija_latin.script == "latin"
    assert darija_latin.code_switching is True
    assert darija_ar.script == "arabic"
    assert gulf.script == "arabic"
    assert gulf.register == "daily-natural"


def test_shadow_validation_does_not_change_patient_visible_reply():
    resolution = _resolution()

    shadow = shadow_validate_resolution(
        resolution,
        language="ar-MA",
    )

    assert shadow.structurally_valid is True
    assert shadow.source_reply == resolution.reply
    assert shadow.envelope.fallback_reply == resolution.reply
