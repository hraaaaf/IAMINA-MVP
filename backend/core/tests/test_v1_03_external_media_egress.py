"""V1-03 synthetic proofs for the actual media provider last hop."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User

from core.ai_egress import (
    AUDIO,
    DOCUMENT,
    IMAGE,
    AIConsentRequired,
    ai_egress_scope,
    grant_media_consent,
    revoke_media_consent,
)
from core.ai_processor_policy import AIProcessorPolicyDenied
from core.tests.consent_helpers import grant_current_ai_consent
from llm.runtime import execute_external_provider_call


@pytest.fixture
def consenting_patient(db):
    user = User.objects.create_user(username="v1-03-media-synthetic")
    grant_current_ai_consent(user)
    return user


@pytest.mark.parametrize(
    ("purpose", "modality"),
    [
        ("meal_vision", IMAGE),
        ("glucometer_ocr", IMAGE),
        ("voice_chat", AUDIO),
        ("voice_transcription", AUDIO),
        ("document_ingest", DOCUMENT),
        ("document_ingest", IMAGE),
    ],
)
def test_media_last_hop_deny_even_if_consent_and_processor_approved(
    consenting_patient, monkeypatch, purpose, modality
):
    grant_media_consent(consenting_patient.id, purpose, modality)
    approved_calls = []
    vendor_calls = []

    def processor_approved(provider, allowed_purpose, allowed_modality):
        approved_calls.append((provider, allowed_purpose, allowed_modality))
        return SimpleNamespace(external_egress=True, status="approved")

    monkeypatch.setattr(
        "llm.runtime.authorize_processor_policy", processor_approved
    )

    with (
        ai_egress_scope(consenting_patient.id, purpose, modality),
        pytest.raises(AIProcessorPolicyDenied, match="raw patient media is disabled"),
    ):
        execute_external_provider_call(
            "gemini",
            modality,
            purpose,
            lambda: vendor_calls.append("unexpected network call"),
        )

    assert approved_calls == [("gemini", purpose, modality)]
    assert vendor_calls == []


def test_media_without_granular_consent_never_reaches_processor(
    consenting_patient, monkeypatch
):
    processor_calls = []
    monkeypatch.setattr(
        "llm.runtime.authorize_processor_policy",
        lambda *args: processor_calls.append(args),
    )
    with (
        ai_egress_scope(consenting_patient.id, "voice_transcription", AUDIO),
        pytest.raises(AIConsentRequired, match="Explicit media consent"),
    ):
        execute_external_provider_call(
            "gemini", AUDIO, "transcribe", lambda: pytest.fail("network was called")
        )
    assert processor_calls == []


def test_media_revocation_fails_before_processor_or_network(
    consenting_patient, monkeypatch
):
    grant_media_consent(consenting_patient.id, "meal_vision", IMAGE)
    assert revoke_media_consent(consenting_patient.id, "meal_vision", IMAGE)
    processor_calls = []
    monkeypatch.setattr(
        "llm.runtime.authorize_processor_policy",
        lambda *args: processor_calls.append(args),
    )
    with (
        ai_egress_scope(consenting_patient.id, "meal_vision", IMAGE),
        pytest.raises(AIConsentRequired, match="Explicit media consent"),
    ):
        execute_external_provider_call(
            "gemini", IMAGE, "generate", lambda: pytest.fail("network was called")
        )
    assert processor_calls == []
