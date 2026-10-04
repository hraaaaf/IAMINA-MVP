from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from companion import conversation
from companion.intent_envelope import RouteKind
from companion.intent_runtime import analyze_runtime_turn
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution


class StrictIntentProvider:
    processor_policy_key = "fallback"

    def __init__(self, payload: str):
        self.payload = payload
        self.calls = 0

    def complete_json_schema(self, *_args, **_kwargs):
        self.calls += 1
        return SimpleNamespace(content=self.payload)


class ExplodingProvider:
    processor_policy_key = "fallback"

    def complete_json_schema(self, *_args, **_kwargs):
        raise AssertionError("intent provider must not be called")


class UnauthorizedProvider:
    processor_policy_key = "groq"

    def __init__(self):
        self.calls = 0

    def complete_json_schema(self, *_args, **_kwargs):
        self.calls += 1
        raise AssertionError("pending processor must be denied before network use")


class ExplodingNarrator:
    def complete(self, *_args, **_kwargs):
        raise AssertionError("narrator must not be called")


def _payload(intent: str, target: str, confidence: float = 0.99, ambiguity: str = "none") -> str:
    return (
        '{"schema_version":"1","intent":"'
        + intent
        + '","target":"'
        + target
        + '","confidence":'
        + str(confidence)
        + ',"ambiguity":"'
        + ambiguity
        + '"}'
    )


def _resolution() -> AdviceResolution:
    return AdviceResolution(
        decision=AdviceDecision(
            intent="cgm_latest_reading",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.context.cgm_latest_reading",
            rule_version="1",
            allowed_actions=("read_patient_owned_data", "describe_persisted_facts"),
            forbidden_actions=("change_treatment",),
            evidence_refs=("product.patient-owned-persisted-data.v1",),
            limitations=("read_only_patient_owned_data",),
            language="fr",
        ),
        reply="Dernière lecture CGM enregistrée : 146 mg/dL.",
    )


def test_runtime_gate_is_default_off(monkeypatch):
    monkeypatch.delenv("IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED", raising=False)

    assert (
        analyze_runtime_turn(
            "Présente-toi autrement.",
            "fr",
            provider=ExplodingProvider(),
        )
        is None
    )


def test_enabled_runtime_without_provider_fails_closed_to_clarify(monkeypatch):
    monkeypatch.setenv("IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED", "true")

    outcome = analyze_runtime_turn(
        "Question nouvelle et non résolue.",
        "fr",
        provider=None,
    )

    assert outcome is not None
    assert outcome.decision.route is RouteKind.CLARIFY
    assert outcome.source == "local_fail_closed"


def test_pending_external_processor_is_denied_before_classifier_call(monkeypatch):
    monkeypatch.setenv("IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED", "true")
    provider = UnauthorizedProvider()

    outcome = analyze_runtime_turn(
        "Présente-toi autrement.",
        "fr",
        provider=provider,
    )

    assert outcome is not None
    assert outcome.decision.route is RouteKind.CLARIFY
    assert provider.calls == 0


def test_classified_meta_identity_stays_local_and_never_calls_narrator(monkeypatch):
    monkeypatch.setenv("IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED", "true")
    provider = StrictIntentProvider(_payload("meta_identity", "none"))

    with patch("companion.conversation.record_companion_route"):
        reply = conversation.chat(
            "Présente-toi avec tes propres mots.",
            memory=None,
            deep=object(),
            llm=ExplodingNarrator(),
            language="fr",
            patient=None,
            intent_provider=provider,
        )

    assert provider.calls == 1
    assert "IAmina" in reply


def test_safety_runs_before_intent_classifier(monkeypatch):
    monkeypatch.setenv("IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED", "true")

    with patch("companion.conversation.record_companion_route"):
        reply = conversation.chat(
            "Je veux mourir.",
            memory=None,
            deep=object(),
            llm=ExplodingNarrator(),
            language="fr",
            patient=None,
            intent_provider=ExplodingProvider(),
        )

    assert reply


def test_patient_target_route_uses_module_target_port_and_verifier(monkeypatch):
    monkeypatch.setenv("IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED", "true")
    provider = StrictIntentProvider(_payload("patient_data_read", "cgm"))
    patient = SimpleNamespace(id=77, first_name="")
    resolution = _resolution()

    with (
        patch(
            "companion.conversation.get_intent_target_resolution",
            return_value=resolution,
        ) as resolve,
        patch(
            "companion.conversation.verify_advice_reply",
            return_value=resolution.reply,
        ) as verify,
        patch("companion.conversation.record_clinical_decision_audit") as audit,
        patch("companion.conversation.record_companion_route"),
        patch("companion.conversation._append_turn"),
    ):
        reply = conversation.chat(
            "Montre-moi la valeur de mon capteur la plus récente.",
            memory=None,
            deep=object(),
            llm=ExplodingNarrator(),
            language="fr",
            patient=patient,
            intent_provider=provider,
        )

    assert reply == resolution.reply
    resolve.assert_called_once_with(
        77,
        "cgm",
        "Montre-moi la valeur de mon capteur la plus récente.",
        language="fr",
    )
    verify.assert_called_once_with(77, resolution, resolution.reply)
    audit.assert_called_once()


def test_patient_target_stream_has_same_deterministic_route(monkeypatch):
    monkeypatch.setenv("IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED", "true")
    provider = StrictIntentProvider(_payload("patient_data_read", "cgm"))
    patient = SimpleNamespace(id=77, first_name="")
    resolution = _resolution()

    with (
        patch(
            "companion.conversation.get_intent_target_resolution",
            return_value=resolution,
        ),
        patch(
            "companion.conversation.verify_advice_reply",
            return_value=resolution.reply,
        ),
        patch("companion.conversation.record_clinical_decision_audit"),
        patch("companion.conversation.record_companion_route"),
        patch("companion.conversation._append_turn"),
    ):
        chunks = list(
            conversation.stream_chat(
                "Montre-moi la valeur de mon capteur la plus récente.",
                memory=None,
                deep=object(),
                llm=ExplodingNarrator(),
                language="fr",
                patient=patient,
                intent_provider=provider,
            )
        )

    assert chunks == [resolution.reply]


def test_conversational_intent_cannot_load_patient_context(monkeypatch):
    monkeypatch.setenv("IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED", "true")
    patient = SimpleNamespace(id=77, first_name="")

    with (
        patch(
            "companion.conversation._get_context",
            side_effect=AssertionError("patient context must stay closed"),
        ),
        patch(
            "companion.conversation.get_advice_resolution",
            side_effect=AssertionError("module patient resolver must stay closed"),
        ),
    ):
        _language, ctx, decision, resolution = conversation._authorize_runtime_narration(
            "Je veux juste discuter un peu.",
            patient,
            "fr",
            14,
            patient_context_allowed=False,
        )

    assert resolution is None
    assert not ctx.pivot_text
    assert decision.authority_level.value == "L0"
