from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from companion import conversation
from companion.narration_envelope import build_shadow_envelope
from companion.protected_provider_shadow import generate_protected_provider_shadow_candidate
from companion.protected_shadow_campaign import (
    ProtectedShadowCampaignProtocol,
    summarize_protected_shadow_campaign,
)
from core.ai_processor_policy import AIProcessorPolicyDenied
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.domain_context import DomainContext


def _resolution() -> AdviceResolution:
    return AdviceResolution(
        decision=AdviceDecision(
            intent="clinician_prep",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.clinician_prep.synthetic",
            rule_version="1",
            allowed_actions=("prepare_clinician_questions",),
            forbidden_actions=("diagnose", "change_treatment"),
            required_facts=("certified_consultation_brief",),
            language="fr",
        ),
        reply="Réponse CLINICIAN_PREP déterministe.",
    )


def _event(status: str) -> dict[str, str]:
    return {
        "event": "protected_narration_shadow",
        "status": status,
        "provider": "groq",
        "family": "clinician_prep",
    }


@override_settings(NARRATION_PROTECTED_PROVIDER_SHADOW=True)
def test_bounded_campaign_policy_blocked_path_never_constructs_provider():
    envelope = build_shadow_envelope(_resolution(), language="fr")
    telemetry = []

    with (
        patch(
            "companion.protected_provider_shadow.authorize_processor_policy",
            side_effect=AIProcessorPolicyDenied("blocked"),
        ),
        patch(
            "companion.protected_provider_shadow.build_openai_compatible_provider"
        ) as build,
        patch(
            "companion.protected_provider_shadow.record_protected_narration_shadow",
            side_effect=lambda **kwargs: telemetry.append(_event(kwargs["status"])),
        ),
    ):
        with pytest.raises(AIProcessorPolicyDenied):
            generate_protected_provider_shadow_candidate(
                envelope,
                internal_authorized=True,
            )

    summary = summarize_protected_shadow_campaign(
        ProtectedShadowCampaignProtocol(
            campaign_id="dry-run-policy-blocked",
            max_turns=1,
            locales=("fr",),
        ),
        telemetry,
    )
    assert summary.blocked == 1
    assert summary.provider_attempted_turns == 0
    build.assert_not_called()


@pytest.mark.parametrize(
    ("provider_candidate", "expected_status"),
    [
        ("D'accord. {token}", "accepted"),
        ("142 mg/dL {token}", "rejected"),
        ("D'accord.", "rejected"),
    ],
)
def test_bounded_campaign_synthetic_candidates_keep_patient_reply_deterministic(
    provider_candidate,
    expected_status,
):
    patient = SimpleNamespace(id=42, first_name="", is_active=True, is_staff=True)
    resolution = _resolution()
    envelope = build_shadow_envelope(resolution, language="fr")
    protected = SimpleNamespace(
        structurally_valid=True,
        reinjected_reply=resolution.reply,
        envelope=envelope,
    )
    telemetry = []
    candidate = provider_candidate.format(token=envelope.protected_body_token)

    def verify_protected(_patient_id, _resolution, reinjected):
        if "142 mg/dL" in reinjected:
            raise PermissionError("clinical wrapper")
        return reinjected

    with (
        patch("companion.conversation.get_advice_resolution", return_value=resolution),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch(
            "companion.conversation.shadow_validate_protected_resolution",
            return_value=protected,
        ),
        patch(
            "companion.conversation.generate_protected_provider_shadow_candidate",
            return_value=candidate,
        ),
        patch(
            "companion.conversation.verify_advice_reply",
            side_effect=lambda _pid, _res, reply: reply,
        ),
        patch(
            "companion.conversation.verify_protected_advice_reply",
            side_effect=verify_protected,
        ),
        patch(
            "companion.conversation.record_protected_narration_shadow",
            side_effect=lambda **kwargs: telemetry.append(_event(kwargs["status"])),
        ),
        patch("companion.conversation._append_turn"),
        patch("companion.conversation.record_companion_route"),
    ):
        reply = conversation.chat(
            "Aide-moi à préparer les questions pour mon médecin.",
            memory=None,
            deep=object(),
            llm=object(),
            language="fr",
            patient=patient,
        )

    summary = summarize_protected_shadow_campaign(
        ProtectedShadowCampaignProtocol(
            campaign_id="dry-run-synthetic",
            max_turns=1,
            locales=("fr",),
        ),
        telemetry,
    )
    assert reply == resolution.reply
    assert getattr(summary, expected_status) == 1


@override_settings(NARRATION_PROTECTED_PROVIDER_SHADOW=True)
def test_bounded_campaign_provider_error_is_content_free_and_fail_closed():
    envelope = build_shadow_envelope(_resolution(), language="fr")
    provider = MagicMock()
    provider.complete_text.side_effect = RuntimeError("secret provider detail 142 mg/dL")
    telemetry = []

    with (
        patch("companion.protected_provider_shadow.authorize_processor_policy"),
        patch(
            "companion.protected_provider_shadow.build_openai_compatible_provider",
            return_value=provider,
        ),
        patch(
            "companion.protected_provider_shadow.record_protected_narration_shadow",
            side_effect=lambda **kwargs: telemetry.append(_event(kwargs["status"])),
        ),
    ):
        with pytest.raises(RuntimeError):
            generate_protected_provider_shadow_candidate(
                envelope,
                internal_authorized=True,
            )

    summary = summarize_protected_shadow_campaign(
        ProtectedShadowCampaignProtocol(
            campaign_id="dry-run-error",
            max_turns=1,
            locales=("fr",),
        ),
        telemetry,
    )
    assert summary.error == 1
    assert telemetry == [_event("error")]
    provider.client.close.assert_called_once()
