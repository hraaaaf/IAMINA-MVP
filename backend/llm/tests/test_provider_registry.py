from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone

from core.ai_egress import ai_egress_scope
from core.ai_processor_policy import (
    PENDING,
    AIProcessorPolicyDenied,
    authorize_processor_policy,
    get_processor_policy,
)
from core.models import BasePatientProfile
from llm.factory import _enforce_text_payload_policy, _provider_policy_name
from llm.provider_registry import (
    build_openai_compatible_provider,
    get_openai_compatible_provider_spec,
    registered_openai_compatible_provider_specs,
)


def test_registry_contains_controlled_openai_compatible_candidates():
    specs = registered_openai_compatible_provider_specs()

    assert set(specs) == {"deepseek", "groq", "qwen"}
    assert specs["groq"].default_model == "openai/gpt-oss-120b"
    assert specs["groq"].default_endpoint == "https://api.groq.com/openai/v1"
    assert specs["groq"].processor_policy_key == "groq"
    assert "issue-430" in specs["groq"].pricing_evidence_reference
    assert "pending" in specs["groq"].locale_quality_status


def test_unknown_registered_candidate_fails_closed():
    with pytest.raises(RuntimeError, match="unknown OpenAI-compatible provider"):
        get_openai_compatible_provider_spec("not-registered")


@override_settings(
    GROQ_API_KEY="synthetic-test-key",
    GROQ_BASE_URL="",
    GROQ_MODEL="",
)
def test_groq_candidate_builds_from_registry_without_network_call():
    provider = build_openai_compatible_provider("groq")
    try:
        assert provider.model_name == "openai/gpt-oss-120b"
        assert provider.provider_policy_key == "groq"
        assert _provider_policy_name(provider) == "groq"
        assert provider.timeout_seconds == 15.0
    finally:
        provider.client.close()


@pytest.mark.django_db
@override_settings(
    GROQ_API_KEY="synthetic-test-key",
    GROQ_BASE_URL="",
    GROQ_MODEL="",
)
def test_groq_pending_processor_policy_denies_before_network():
    user = User.objects.create_user(username="groq-policy-patient")
    BasePatientProfile.objects.create(
        patient=user,
        ai_consent_given_at=timezone.now(),
    )
    provider = build_openai_compatible_provider("groq")
    network_call = MagicMock()
    provider.client.chat.completions.create = network_call
    guarded = _enforce_text_payload_policy(provider)

    try:
        with ai_egress_scope(user.id, "companion_chat", "text"):
            with pytest.raises(AIProcessorPolicyDenied, match="not approved"):
                guarded.complete("system", "hello")
    finally:
        provider.client.close()

    assert network_call.call_count == 0
    policy = get_processor_policy("groq")
    assert policy.status == PENDING
    assert policy.max_retention_days == 30
    assert policy.legal_basis == ""


def test_all_registered_network_candidates_remain_unapproved():
    for provider_id in ("deepseek", "qwen", "groq"):
        with pytest.raises(AIProcessorPolicyDenied, match="not approved"):
            authorize_processor_policy(provider_id, "companion_chat", "text")
