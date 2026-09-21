from dataclasses import replace

import pytest
from django.contrib.auth.models import User

from core.ai_egress import ai_egress_scope
from core.ai_processor_policy import (
    APPROVED,
    PENDING,
    AIProcessorPolicy,
    AIProcessorPolicyDenied,
    authorize_processor_policy,
    get_processor_policy,
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


@pytest.fixture
def consented_user(db):
    user = User.objects.create_user(username="processor-policy-patient")
    grant_current_ai_consent(user)
    return user


def test_unknown_provider_is_denied():
    with pytest.raises(AIProcessorPolicyDenied, match="Unknown"):
        get_processor_policy("not-registered")


def test_pending_network_provider_is_denied():
    with pytest.raises(AIProcessorPolicyDenied, match="not approved"):
        authorize_processor_policy("gemini", "companion_chat", "text")



def test_groq_patient_egress_stays_pending_until_governance_evidence_exists():
    policy = get_processor_policy("groq")

    assert policy.status == PENDING
    assert policy.processing_regions == ("United States",)
    assert policy.max_retention_days == 30
    assert "Zero Data Retention" in policy.retention_policy
    assert "cndp_health_processing_authorization_reference" in policy.approval_conditions
    assert "cndp_cross_border_transfer_basis_or_authorization_reference" in policy.approval_conditions
    assert "groq_dpa_accepted_for_iamina_data_controller" in policy.approval_conditions
    assert "groq_zero_data_retention_verified_for_production_org" in policy.approval_conditions
    assert "patient_consent_notice_identifies_groq_and_us_transfer" in policy.approval_conditions

    with pytest.raises(AIProcessorPolicyDenied, match="not approved"):
        authorize_processor_policy("groq", "companion_chat", "text")


def test_groq_status_flip_alone_cannot_open_patient_egress():
    policy = replace(get_processor_policy("groq"), status=APPROVED)

    with pytest.raises(AIProcessorPolicyDenied, match="outstanding approval conditions"):
        policy.validate()


def test_local_fallback_is_approved_for_registered_text_purpose():
    policy = authorize_processor_policy("fallback", "companion_chat", "text")
    assert policy.status == APPROVED
    assert policy.external_egress is False
    assert policy.data_residency == "local-only"
    assert policy.training_use == "none"


def test_local_fallback_rejects_wrong_modality():
    with pytest.raises(AIProcessorPolicyDenied, match="modality"):
        authorize_processor_policy("fallback", "companion_chat", "image")


def test_incomplete_external_policy_fails_validation():
    policy = AIProcessorPolicy(
        provider="incomplete",
        processor="External Processor",
        subprocessors=(),
        processing_regions=(),
        data_residency="",
        retention_policy="",
        max_retention_days=0,
        training_use="",
        legal_basis="",
        allowed_modalities=frozenset({"text"}),
        allowed_purposes=frozenset({"companion_chat"}),
        status=PENDING,
    )
    with pytest.raises(AIProcessorPolicyDenied, match="governance metadata"):
        policy.validate()


@pytest.mark.django_db
def test_processor_denial_prevents_provider_invocation(consented_user, monkeypatch):
    monkeypatch.setattr("llm.factory._provider_policy_name", lambda _: "gemini")
    provider = RecordingProvider()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consented_user.id, "companion_chat", "text"):
        with pytest.raises(AIProcessorPolicyDenied):
            guarded.complete("system", "hello")

    assert provider.calls == 0


@pytest.mark.django_db
def test_approved_local_provider_can_execute(consented_user, monkeypatch):
    monkeypatch.setattr("llm.factory._provider_policy_name", lambda _: "fallback")
    provider = RecordingProvider()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consented_user.id, "companion_chat", "text"):
        result = guarded.complete("system", "hello")

    assert result.content == "ok"
    assert provider.calls == 1
