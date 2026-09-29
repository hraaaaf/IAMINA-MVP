from types import SimpleNamespace
from unittest.mock import patch

import pytest

from companion import conversation
from companion.narration_envelope import build_shadow_envelope
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


def _protected(resolution):
    envelope = build_shadow_envelope(resolution, language="fr")
    return SimpleNamespace(
        structurally_valid=True,
        reinjected_reply=resolution.reply,
        envelope=envelope,
    )


@pytest.mark.parametrize("candidate_kind", [
    "missing",
    "duplicate",
    "replayed",
    "body_exposed",
    "clinical_number",
])
def test_adversarial_provider_candidates_never_change_patient_reply(candidate_kind):
    patient = SimpleNamespace(id=42, first_name="")
    resolution = _resolution()
    protected = _protected(resolution)
    token = protected.envelope.protected_body_token
    other_token = build_shadow_envelope(resolution, language="fr").protected_body_token

    candidates = {
        "missing": "D'accord.",
        "duplicate": f"{token} {token}",
        "replayed": other_token,
        "body_exposed": f"{resolution.reply} {token}",
        "clinical_number": f"142 mg/dL {token}",
    }
    telemetry = []

    def verify_protected(_patient_id, _resolution, candidate):
        # The local seam is exact-copy; a provider candidate reaches this only
        # after structural reinjection.
        return candidate

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=resolution,
        ),
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
            return_value=candidates[candidate_kind],
        ),
        patch(
            "companion.conversation.verify_advice_reply",
            side_effect=lambda _pid, _res, candidate: candidate,
        ),
        patch(
            "companion.conversation.verify_protected_advice_reply",
            side_effect=verify_protected,
        ),
        patch(
            "companion.conversation.record_protected_narration_shadow",
            side_effect=lambda **kwargs: telemetry.append(kwargs["status"]),
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

    assert reply == resolution.reply
    assert telemetry == ["rejected"]


def test_clinical_wrapper_rejected_by_module_verifier_without_changing_patient_reply():
    patient = SimpleNamespace(id=42, first_name="")
    resolution = _resolution()
    protected = _protected(resolution)
    token = protected.envelope.protected_body_token
    telemetry = []
    calls = {"protected": 0}

    def verify_protected(_patient_id, _resolution, candidate):
        calls["protected"] += 1
        if calls["protected"] == 1:
            return candidate
        raise PermissionError("wrapper_contains_clinical_content")

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
            return_value=f"Ton glucose semble stable. {token}",
        ),
        patch(
            "companion.conversation.verify_advice_reply",
            side_effect=lambda _pid, _res, candidate: candidate,
        ),
        patch(
            "companion.conversation.verify_protected_advice_reply",
            side_effect=verify_protected,
        ),
        patch(
            "companion.conversation.record_protected_narration_shadow",
            side_effect=lambda **kwargs: telemetry.append(kwargs["status"]),
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

    assert reply == resolution.reply
    assert telemetry == ["rejected"]
    assert calls["protected"] == 2
