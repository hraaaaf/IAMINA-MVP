from datetime import date
from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.ai_egress import ai_egress_scope
from core.models import BasePatientProfile
from llm.base import BaseLLMProvider, LLMResponse
from llm.errors import (
    LLMProviderInternalFailure,
    LLMProviderTimeout,
    LLMProviderUnavailable,
)
from llm.factory import _enforce_text_payload_policy


class RaisingProvider(BaseLLMProvider):
    def __init__(self, exc: Exception):
        self.exc = exc
        self.calls = 0

    def complete(self, system: str, user: str) -> LLMResponse:
        self.calls += 1
        raise self.exc


@pytest.fixture
def consenting_patient(db):
    user = User.objects.create_user(username="provider-failure-patient")
    BasePatientProfile.objects.update_or_create(
        patient=user,
        defaults={
            "date_of_birth": date(1990, 1, 1),
            "ai_consent_given_at": timezone.now(),
        },
    )
    return user


def _approved_guard(provider, monkeypatch):
    monkeypatch.setattr("llm.factory._provider_policy_name", lambda _: "fallback")
    return _enforce_text_payload_policy(provider)


@pytest.mark.django_db
def test_timeout_is_normalized_without_raw_vendor_message(consenting_patient, monkeypatch):
    provider = RaisingProvider(TimeoutError("vendor request id secret-123 timed out"))
    guarded = _approved_guard(provider, monkeypatch)

    with ai_egress_scope(consenting_patient.id, "companion_chat", "text"):
        with pytest.raises(LLMProviderTimeout) as caught:
            guarded.complete("system", "bonjour")

    assert caught.value.code == "provider_timeout"
    assert caught.value.retryable is True
    assert "secret-123" not in str(caught.value)
    assert provider.calls == 1


@pytest.mark.django_db
def test_connection_failure_is_normalized(consenting_patient, monkeypatch):
    provider = RaisingProvider(ConnectionError("private endpoint detail"))
    guarded = _approved_guard(provider, monkeypatch)

    with ai_egress_scope(consenting_patient.id, "companion_chat", "text"):
        with pytest.raises(LLMProviderUnavailable) as caught:
            guarded.complete("system", "bonjour")

    assert caught.value.code == "provider_unavailable"
    assert caught.value.retryable is True
    assert "private endpoint" not in str(caught.value)


@pytest.mark.django_db
def test_unknown_provider_exception_becomes_non_retryable_internal_failure(
    consenting_patient,
    monkeypatch,
):
    provider = RaisingProvider(ValueError("raw provider payload"))
    guarded = _approved_guard(provider, monkeypatch)

    with ai_egress_scope(consenting_patient.id, "companion_chat", "text"):
        with pytest.raises(LLMProviderInternalFailure) as caught:
            guarded.complete("system", "bonjour")

    assert caught.value.code == "provider_internal_failure"
    assert caught.value.retryable is False
    assert "raw provider payload" not in str(caught.value)


@pytest.mark.django_db
def test_policy_denial_still_prevents_provider_invocation(consenting_patient, monkeypatch):
    monkeypatch.setattr("llm.factory._provider_policy_name", lambda _: "gemini")
    provider = MagicMock(spec=BaseLLMProvider)
    original_complete = MagicMock(
        return_value=LLMResponse(content="unsafe", provider="mock")
    )
    provider.complete = original_complete
    provider.stream = MagicMock()
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consenting_patient.id, "companion_chat", "text"):
        with pytest.raises(Exception) as caught:
            guarded.complete("system", "bonjour")

    assert type(caught.value).__name__ == "AIProcessorPolicyDenied"
    original_complete.assert_not_called()
