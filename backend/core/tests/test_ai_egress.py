"""P0 tests for the central patient AI egress authorization boundary."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.ai_egress import (
    AUDIO,
    DOCUMENT,
    IMAGE,
    TEXT,
    AIConsentRequired,
    AIEgressDenied,
    ai_egress_scope,
    assert_ai_egress_allowed,
    grant_media_consent,
    patient_ai_egress_scope,
    revoke_media_consent,
)
from core.models import BasePatientProfile


@pytest.fixture
def patient(db):
    user = User.objects.create_user(username="egress-patient")
    BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1990, 1, 1),
    )
    return user


def _grant_global_consent(patient):
    profile = patient.base_profile
    profile.ai_consent_given_at = timezone.now()
    profile.save(update_fields=["ai_consent_given_at"])


def test_no_scope_is_default_deny(db):
    with pytest.raises(AIEgressDenied, match="outside an authorized egress scope"):
        assert_ai_egress_allowed(TEXT)


def test_scope_is_lazy_and_does_not_block_deterministic_paths(patient):
    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        pass


def test_real_egress_requires_server_side_consent(patient):
    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        with pytest.raises(AIConsentRequired, match="Explicit patient AI consent"):
            assert_ai_egress_allowed(TEXT)


def test_text_egress_allowed_after_global_consent(patient):
    _grant_global_consent(patient)

    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        context = assert_ai_egress_allowed(TEXT)

    assert context.patient_id == patient.id
    assert context.purpose == "companion_chat"


@pytest.mark.parametrize(
    ("purpose", "modality"),
    [
        ("voice_transcription", AUDIO),
        ("meal_vision", IMAGE),
        ("document_ingest", DOCUMENT),
    ],
)
def test_raw_media_requires_additional_granular_consent(patient, purpose, modality):
    _grant_global_consent(patient)

    with ai_egress_scope(patient.id, purpose, modality):
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            assert_ai_egress_allowed(modality)


def test_exact_purpose_and_modality_grant_allows_media_egress(patient):
    _grant_global_consent(patient)
    grant = grant_media_consent(patient.id, "meal_vision", IMAGE)

    with ai_egress_scope(patient.id, "meal_vision", IMAGE):
        context = assert_ai_egress_allowed(IMAGE)

    assert grant.patient_id == patient.id
    assert grant.purpose == "meal_vision"
    assert grant.modality == IMAGE
    assert context.purpose == "meal_vision"


def test_grant_does_not_authorize_another_purpose(patient):
    _grant_global_consent(patient)
    grant_media_consent(patient.id, "meal_vision", IMAGE)

    with ai_egress_scope(patient.id, "glucometer_ocr", IMAGE):
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            assert_ai_egress_allowed(IMAGE)


def test_grant_does_not_authorize_another_modality(patient):
    _grant_global_consent(patient)
    grant_media_consent(patient.id, "document_ingest", DOCUMENT)

    with ai_egress_scope(patient.id, "document_ingest", IMAGE):
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            assert_ai_egress_allowed(IMAGE)


def test_revocation_takes_effect_before_next_egress(patient):
    _grant_global_consent(patient)
    grant_media_consent(patient.id, "voice_transcription", AUDIO)
    assert revoke_media_consent(patient.id, "voice_transcription", AUDIO) is True
    assert revoke_media_consent(patient.id, "voice_transcription", AUDIO) is False

    with ai_egress_scope(patient.id, "voice_transcription", AUDIO):
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            assert_ai_egress_allowed(AUDIO)


def test_invalid_grant_pair_is_denied(patient):
    with pytest.raises(AIEgressDenied, match="not authorized"):
        grant_media_consent(patient.id, "companion_chat", IMAGE)
    with pytest.raises(AIEgressDenied, match="not a raw-media"):
        grant_media_consent(patient.id, "companion_chat", TEXT)


def test_modality_cannot_escape_declared_purpose(patient):
    _grant_global_consent(patient)

    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        with pytest.raises(AIEgressDenied, match="not authorized"):
            assert_ai_egress_allowed(IMAGE)


def test_unknown_purpose_is_denied_before_runtime(patient):
    with pytest.raises(AIEgressDenied, match="Unknown AI egress purpose"):
        with ai_egress_scope(patient.id, "unregistered-purpose", TEXT):
            pass


def test_gateway_blocks_provider_call_without_authorized_scope(db):
    provider = MagicMock()
    with patch("core.llm_gateway.get_llm", return_value=provider):
        from core.llm_gateway import GatewayLLM

        gateway = GatewayLLM()
        with pytest.raises(AIEgressDenied):
            gateway.complete("system", "user")

    provider.complete.assert_not_called()


def test_endpoint_decorator_only_declares_scope_until_egress(patient):
    request = SimpleNamespace(user=patient, auth=patient)

    @patient_ai_egress_scope("voice_chat", AUDIO, TEXT)
    def endpoint(req):
        return req.user.id

    assert endpoint(request) == patient.id
