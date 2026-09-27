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
    NarrationEnvelopeError,
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


def _with_body(envelope, text: str) -> str:
    return f"{text} {envelope.protected_body_token}"


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

    assert fact["token"].startswith("{{NVF_")
    assert fact["token"].endswith("}}")
    assert "FACT_GLUCOSE" not in fact["token"]
    assert fact["provider_hint"] is None
    assert provider["protected_body_token"].startswith("{{NVB_")
    assert provider["protected_body_token"].endswith("}}")
    assert "جواب حتمي وآمن." not in repr(provider)
    assert "187 mg/dL" not in repr(provider)
    assert "log_entry:synthetic" not in repr(provider)


def test_required_fact_token_is_reinjected_only_after_verification():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    token = envelope.fact_token("FACT_GLUCOSE")
    result = verify_and_reinject_narration(
        _with_body(
            envelope,
            f"هاد القياس {token} باين فالملاحظة اللي عطاتها IAMINA.",
        ),
        envelope,
    )

    assert token not in result
    assert "187 mg/dL" in result


def test_unknown_or_missing_fact_tokens_fail_closed():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    with pytest.raises(NarrationVerificationError, match="unknown"):
        verify_and_reinject_narration(
            _with_body(
                envelope,
                "هاد القياس {{NVF_00000000000000000000000000000000}}.",
            ),
            envelope,
        )

    with pytest.raises(NarrationVerificationError, match="omitted"):
        verify_and_reinject_narration(
            _with_body(envelope, "هاد القياس باين فالملاحظة."),
            envelope,
        )


def test_candidate_cannot_expose_or_invent_untokenized_clinical_number():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    token = envelope.fact_token("FACT_GLUCOSE")

    with pytest.raises(NarrationVerificationError, match="exact local"):
        verify_and_reinject_narration(
            _with_body(envelope, f"القياس 187 mg/dL و {token}."),
            envelope,
        )

    with pytest.raises(NarrationVerificationError, match="untokenized"):
        verify_and_reinject_narration(
            _with_body(
                envelope,
                f"القياس {token} وملاحظة ثانية 210 mg/dL.",
            ),
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


def test_coarsened_provider_hint_cannot_expose_exact_or_replacement_measurement():
    unsafe_hints = (
        "around 187 mg/dL",
        "around 180 mg/dL",
        "تقريباً ١٨٧ mg/dL",
        "187",
    )
    for hint in unsafe_hints:
        with pytest.raises(NarrationEnvelopeError, match="genuinely coarsened"):
            NarrationFact(
                key="FACT_GLUCOSE",
                semantic_type="glucose_value",
                rendered_value="187 mg/dL",
                egress_policy=FactEgressPolicy.COARSENED_ONLY,
                provider_hint=hint,
            )

    safe = NarrationFact(
        key="FACT_GLUCOSE",
        semantic_type="glucose_value",
        rendered_value="187 mg/dL",
        egress_policy=FactEgressPolicy.COARSENED_ONLY,
        provider_hint="elevated range",
    )
    assert safe.provider_hint == "elevated range"


def test_provider_view_exposes_only_safe_coarsened_hint_not_exact_value():
    fact = NarrationFact(
        key="FACT_GLUCOSE",
        semantic_type="glucose_value",
        rendered_value="187 mg/dL",
        egress_policy=FactEgressPolicy.COARSENED_ONLY,
        provider_hint="elevated range",
    )
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(fact,),
    )

    provider = envelope.provider_view()
    assert provider["facts"][0]["provider_hint"] == "elevated range"
    assert "187 mg/dL" not in repr(provider)


def test_fact_tokens_are_opaque_unique_and_envelope_scoped():
    first = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )
    second = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(),),
    )

    first_token = first.fact_token("FACT_GLUCOSE")
    second_token = second.fact_token("FACT_GLUCOSE")

    assert first_token != second_token
    assert "FACT_GLUCOSE" not in first_token
    assert "FACT_GLUCOSE" not in second_token

    assert "187 mg/dL" in verify_and_reinject_narration(
        _with_body(first, f"القياس {first_token}."),
        first,
    )
    with pytest.raises(NarrationVerificationError, match="unknown"):
        verify_and_reinject_narration(
            _with_body(second, f"القياس {first_token}."),
            second,
        )


def test_multiple_facts_receive_distinct_tokens_without_semantic_keys():
    second_fact = NarrationFact(
        key="FACT_SECOND",
        semantic_type="second_observation",
        rendered_value="stable",
        egress_policy=FactEgressPolicy.LOCAL_ONLY,
    )
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
        facts=(_fact(), second_fact),
    )

    tokens = {
        envelope.fact_token("FACT_GLUCOSE"),
        envelope.fact_token("FACT_SECOND"),
    }
    assert len(tokens) == 2
    assert all(token.startswith("{{NVF_") and token.endswith("}}") for token in tokens)
    assert all("FACT_" not in token for token in tokens)


def test_protected_body_is_required_reinjected_locally_and_not_provider_visible():
    envelope = build_shadow_envelope(
        _resolution(),
        language="ar-MA",
    )

    provider = envelope.provider_view()
    body_token = provider["protected_body_token"]

    assert body_token == envelope.protected_body_token
    assert "جواب حتمي وآمن." not in repr(provider)

    result = verify_and_reinject_narration(
        f"مفهوم. {body_token}",
        envelope,
    )
    assert body_token not in result
    assert result == "مفهوم. جواب حتمي وآمن."

    with pytest.raises(NarrationVerificationError, match="omitted protected body"):
        verify_and_reinject_narration("مفهوم.", envelope)

    with pytest.raises(NarrationVerificationError, match="protected local body"):
        verify_and_reinject_narration(
            f"جواب حتمي وآمن. {body_token}",
            envelope,
        )


def test_protected_body_token_is_envelope_scoped_and_replay_fails_closed():
    first = build_shadow_envelope(_resolution(), language="ar-MA")
    second = build_shadow_envelope(_resolution(), language="ar-MA")

    assert first.protected_body_token != second.protected_body_token

    with pytest.raises(
        NarrationVerificationError,
        match="replayed or unknown body token",
    ):
        verify_and_reinject_narration(
            first.protected_body_token,
            second,
        )


def test_duplicate_protected_body_token_is_rejected():
    envelope = build_shadow_envelope(_resolution(), language="ar-MA")
    token = envelope.protected_body_token

    with pytest.raises(
        NarrationVerificationError,
        match="exactly one protected body token",
    ):
        verify_and_reinject_narration(
            f"{token} puis {token}",
            envelope,
        )
