from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from companion.narration_envelope import build_shadow_envelope
from companion.protected_provider_shadow import (
    build_protected_provider_shadow_request,
    generate_protected_provider_shadow_candidate,
)
from core.ai_processor_policy import AIProcessorPolicyDenied
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution


def _resolution() -> AdviceResolution:
    return AdviceResolution(
        decision=AdviceDecision(
            intent="clinician_prep",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.clinician_prep.synthetic",
            rule_version="1",
            allowed_actions=("prepare_clinician_questions",),
            forbidden_actions=("diagnose",),
            required_facts=("certified_consultation_brief",),
            language="fr",
        ),
        reply="Réponse clinique déterministe 142 mg/dL.",
    )


def test_request_contains_only_locale_script_and_opaque_token():
    envelope = build_shadow_envelope(_resolution(), language="fr")
    request = build_protected_provider_shadow_request(envelope)
    prompt = request.user_prompt()

    assert request.locale == "fr"
    assert request.protected_body_token == envelope.protected_body_token
    assert "Réponse clinique déterministe" not in prompt
    assert "142" not in prompt
    assert "mg/dL" not in prompt
    assert "certified_consultation_brief" not in prompt
    assert "diabetes.clinician_prep" not in prompt


@override_settings(NARRATION_PROTECTED_PROVIDER_SHADOW=False)
def test_shadow_off_never_authorizes_or_builds_provider():
    envelope = build_shadow_envelope(_resolution(), language="fr")

    with patch(
        "companion.protected_provider_shadow.authorize_processor_policy"
    ) as authorize:
        with patch(
            "companion.protected_provider_shadow.build_openai_compatible_provider"
        ) as build:
            assert generate_protected_provider_shadow_candidate(envelope) is None

    authorize.assert_not_called()
    build.assert_not_called()


@override_settings(NARRATION_PROTECTED_PROVIDER_SHADOW=True)
def test_policy_denial_happens_before_provider_construction():
    envelope = build_shadow_envelope(_resolution(), language="fr")

    with patch(
        "companion.protected_provider_shadow.authorize_processor_policy",
        side_effect=AIProcessorPolicyDenied("blocked"),
    ) as authorize:
        with patch(
            "companion.protected_provider_shadow.build_openai_compatible_provider"
        ) as build:
            with pytest.raises(AIProcessorPolicyDenied):
                generate_protected_provider_shadow_candidate(envelope)

    authorize.assert_called_once_with("groq", "companion_chat", "text")
    build.assert_not_called()


@override_settings(NARRATION_PROTECTED_PROVIDER_SHADOW=True)
def test_authorized_shadow_returns_candidate_from_minimal_payload():
    envelope = build_shadow_envelope(_resolution(), language="fr")
    provider = MagicMock()
    provider.complete.return_value = MagicMock(
        content=f"D'accord. {envelope.protected_body_token}"
    )

    with patch(
        "companion.protected_provider_shadow.authorize_processor_policy"
    ) as authorize:
        with patch(
            "companion.protected_provider_shadow.build_openai_compatible_provider",
            return_value=provider,
        ):
            candidate = generate_protected_provider_shadow_candidate(envelope)

    authorize.assert_called_once_with("groq", "companion_chat", "text")
    assert candidate == f"D'accord. {envelope.protected_body_token}"
    system, user = provider.complete.call_args.args
    assert "Réponse clinique déterministe" not in system + user
    assert "142" not in system + user
    assert envelope.protected_body_token in user


@override_settings(NARRATION_PROTECTED_PROVIDER_SHADOW=True)
def test_non_internal_subject_never_reaches_processor_policy():
    envelope = build_shadow_envelope(_resolution(), language="fr")

    with patch(
        "companion.protected_provider_shadow.authorize_processor_policy"
    ) as authorize:
        with patch(
            "companion.protected_provider_shadow.build_openai_compatible_provider"
        ) as build:
            assert (
                generate_protected_provider_shadow_candidate(
                    envelope,
                    internal_authorized=False,
                )
                is None
            )

    authorize.assert_not_called()
    build.assert_not_called()


@override_settings(NARRATION_PROTECTED_PROVIDER_SHADOW=True)
def test_internal_subject_reaches_processor_policy_before_provider():
    envelope = build_shadow_envelope(_resolution(), language="fr")

    with patch(
        "companion.protected_provider_shadow.authorize_processor_policy",
        side_effect=AIProcessorPolicyDenied("blocked"),
    ) as authorize:
        with patch(
            "companion.protected_provider_shadow.build_openai_compatible_provider"
        ) as build:
            with pytest.raises(AIProcessorPolicyDenied):
                generate_protected_provider_shadow_candidate(
                    envelope,
                    internal_authorized=True,
                )

    authorize.assert_called_once_with("groq", "companion_chat", "text")
    build.assert_not_called()
