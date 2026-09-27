from __future__ import annotations

import pytest

from companion.narration_envelope import (
    NarrationVerificationError,
    build_shadow_envelope,
    verify_and_reinject_protected_narration,
)
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.capabilities import Capability


def _resolution() -> AdviceResolution:
    return AdviceResolution(
        decision=AdviceDecision(
            intent="clinician_prep",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.clinician_prep.synthetic",
            rule_version="1",
            allowed_actions=(Capability.PREPARE_CLINICIAN_QUESTIONS.value,),
            forbidden_actions=(
                Capability.DIAGNOSE.value,
                Capability.PRESCRIBE.value,
                Capability.CALCULATE_DOSE.value,
            ),
            required_facts=("certified_consultation_brief",),
            limitations=("clinician_remains_medical_decision_authority",),
            language="fr",
        ),
        reply="Réponse clinique déterministe.",
    )


def test_provider_view_exposes_opaque_body_token_not_local_body():
    envelope = build_shadow_envelope(_resolution(), language="fr")
    provider = envelope.provider_view()

    token = provider["protected_body_token"]
    assert token == envelope.protected_body_token
    assert token.startswith("{{NVB_")
    assert token.endswith("}}")
    assert "Réponse clinique déterministe." not in repr(provider)


def test_protected_body_is_required_and_reinjected_locally():
    envelope = build_shadow_envelope(_resolution(), language="fr")
    token = envelope.protected_body_token

    result = verify_and_reinject_protected_narration(
        f"D'accord. {token}",
        envelope,
    )

    assert result == "D'accord. Réponse clinique déterministe."
    assert token not in result


def test_protected_body_omission_duplication_and_exposure_fail_closed():
    envelope = build_shadow_envelope(_resolution(), language="fr")
    token = envelope.protected_body_token

    with pytest.raises(NarrationVerificationError, match="omitted protected body"):
        verify_and_reinject_protected_narration("D'accord.", envelope)

    with pytest.raises(NarrationVerificationError, match="exactly one protected body"):
        verify_and_reinject_protected_narration(
            f"{token} puis {token}",
            envelope,
        )

    with pytest.raises(NarrationVerificationError, match="protected local body"):
        verify_and_reinject_protected_narration(
            f"Réponse clinique déterministe. {token}",
            envelope,
        )


def test_protected_body_token_is_envelope_scoped_and_replay_fails_closed():
    first = build_shadow_envelope(_resolution(), language="fr")
    second = build_shadow_envelope(_resolution(), language="fr")

    assert first.protected_body_token != second.protected_body_token

    with pytest.raises(
        NarrationVerificationError,
        match="replayed or unknown body token",
    ):
        verify_and_reinject_protected_narration(
            first.protected_body_token,
            second,
        )
