from __future__ import annotations

import pytest
from django.contrib.auth.models import User

from core.ai_egress import ai_egress_scope
from core.ai_processor_policy import AIProcessorPolicyDenied
from core.anonymization_gateway import (
    AnonymizationResult,
    AnonymizationRiskDenied,
    minimize_external_text,
    minimize_external_text_payload,
)
from core.tests.consent_helpers import grant_current_ai_consent
from llm.base import BaseLLMProvider, LLMResponse
from llm.factory import _enforce_text_payload_policy


class RecordingProvider(BaseLLMProvider):
    def __init__(self):
        self.calls = 0

    def complete(self, system: str, user: str) -> LLMResponse:
        self.calls += 1
        return LLMResponse(content="ok", provider="recording")


def test_minimizer_coarsens_known_reidentification_signals_without_mapping():
    raw = (
        "Âgé de 29 ans. Date 21/09/2026 à 22:41. "
        "Glycémie 248 mg/dL, insuline 6 U, HbA1c 7.2%.\n"
        "Ville: Rabat\n"
        "Email: patient@example.com\n"
        "Téléphone: +212 6 12 34 56 78\n"
        "CIN: AB123456\n"
        "token ABCDEFGHIJKLMNOPQRSTUVWX123456"
    )

    minimized, transformations = minimize_external_text(raw)

    assert "29 ans" not in minimized
    assert "21/09/2026" not in minimized
    assert "22:41" not in minimized
    assert "248 mg/dL" not in minimized
    assert "6 U" not in minimized
    assert "7.2%" not in minimized
    assert "Rabat" not in minimized
    assert "patient@example.com" not in minimized
    assert "+212 6 12 34 56 78" not in minimized
    assert "AB123456" not in minimized
    assert "ABCDEFGHIJKLMNOPQRSTUVWX123456" not in minimized

    assert "[age band: adult]" in minimized
    assert "[date coarsened]" in minimized
    assert "[time coarsened]" in minimized
    assert "[clinical value withheld]" in minimized
    assert "[location withheld]" in minimized
    assert "[identifier withheld]" in minimized
    assert "exact_age" in transformations
    assert "precise_date" in transformations
    assert "precise_time" in transformations
    assert "exact_clinical_value" in transformations


def test_minimizer_removes_international_phone_and_disposable_patient_token():
    raw = "Contact +33 6 12 34 56 78. Ref PATIENT_deadbeef."

    minimized, transformations = minimize_external_text(raw)

    assert "+33 6 12 34 56 78" not in minimized
    assert "PATIENT_deadbeef" not in minimized
    assert "[identifier withheld]" in minimized
    assert "[patient reference withheld]" in minimized
    assert "direct_identifier" in transformations
    assert "patient_reference_token" in transformations


def test_minimizer_covers_arabic_digits_age_location_and_clinical_units():
    raw = (
        "عمري ٢٩ سنة. أسكن في الرباط. "
        "القياس ٢٤٨ ملغ/دل الساعة ٢٢:٤١ يوم ٢١/٠٩/٢٠٢٦."
    )

    minimized, transformations = minimize_external_text(raw)

    assert "٢٩" not in minimized
    assert "الرباط" not in minimized
    assert "٢٤٨ ملغ/دل" not in minimized
    assert "٢٢:٤١" not in minimized
    assert "٢١/٠٩/٢٠٢٦" not in minimized
    assert "[age band: adult]" in minimized
    assert "[location withheld]" in minimized
    assert "[clinical value withheld]" in minimized
    assert "[time coarsened]" in minimized
    assert "[date coarsened]" in minimized
    assert "exact_age" in transformations
    assert "location_phrase" in transformations
    assert "exact_clinical_value" in transformations


def test_payload_result_is_deterministic_immutable_and_never_claims_certified_anonymity():
    payload = {
        "system_prompt": "Review anchor 2026-09-20 at 22:41.",
        "user_prompt": "I am 35 years old and measured 210 mg/dL.",
    }

    first = minimize_external_text_payload(payload)
    second = minimize_external_text_payload(payload)

    assert dict(first.fields) == dict(second.fields)
    assert first.transformations == second.transformations
    assert first.residual_findings == frozenset()
    assert first.certified_anonymous is False

    with pytest.raises(TypeError):
        first.fields["system_prompt"] = "mutated"  # type: ignore[index]


def test_legal_anonymity_flag_cannot_be_opted_in():
    with pytest.raises(TypeError):
        AnonymizationResult(
            fields={},
            transformations=(),
            residual_findings=frozenset(),
            certified_anonymous=True,  # type: ignore[call-arg]
        )


def test_payload_shape_is_fail_closed():
    with pytest.raises(AnonymizationRiskDenied, match="exactly"):
        minimize_external_text_payload({"user_prompt": "hello"})


def test_residual_risk_is_fail_closed(monkeypatch):
    monkeypatch.setattr(
        "core.anonymization_gateway._known_residual_findings",
        lambda _text: frozenset({"synthetic_residual"}),
    )

    with pytest.raises(AnonymizationRiskDenied, match="re-identification"):
        minimize_external_text_payload(
            {"system_prompt": "safe", "user_prompt": "safe"}
        )


@pytest.mark.django_db
def test_external_provider_path_runs_anonymization_before_processor_policy(monkeypatch):
    user = User.objects.create_user(username="anon-gateway-patient")
    grant_current_ai_consent(user)

    observed = {}
    from core import anonymization_gateway
    from llm import factory

    real_minimize = anonymization_gateway.minimize_external_text_payload

    def recording_minimize(payload):
        result = real_minimize(payload)
        observed["result"] = result
        return result

    monkeypatch.setattr(factory, "minimize_external_text_payload", recording_minimize)
    monkeypatch.setattr(factory, "_provider_policy_name", lambda _provider: "groq")

    provider = _enforce_text_payload_policy(RecordingProvider())

    with ai_egress_scope(user.id, "companion_chat", "text"):
        with pytest.raises(AIProcessorPolicyDenied, match="not approved"):
            provider.complete(
                "Review anchor 2026-09-20 at 22:41.",
                "I am 35 years old and measured 210 mg/dL.",
            )

    minimized = observed["result"]
    assert "2026-09-20" not in minimized.fields["system_prompt"]
    assert "22:41" not in minimized.fields["system_prompt"]
    assert "35 years old" not in minimized.fields["user_prompt"]
    assert "210 mg/dL" not in minimized.fields["user_prompt"]
    assert provider.calls == 0


@pytest.mark.django_db
def test_local_fallback_path_does_not_mutate_prompt(monkeypatch):
    user = User.objects.create_user(username="anon-gateway-local")
    grant_current_ai_consent(user)

    provider = RecordingProvider()
    monkeypatch.setattr("llm.factory._provider_policy_name", lambda _provider: "fallback")

    def unexpected_minimize(_payload):
        raise AssertionError("local provider must not use external anonymization gateway")

    monkeypatch.setattr(
        "llm.factory.minimize_external_text_payload",
        unexpected_minimize,
    )

    guarded = _enforce_text_payload_policy(provider)
    with ai_egress_scope(user.id, "companion_chat", "text"):
        response = guarded.complete("system", "hello")

    assert response.content == "ok"
    assert provider.calls == 1
