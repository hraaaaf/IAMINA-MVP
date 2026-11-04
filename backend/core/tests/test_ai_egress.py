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
from core.consent_notice import expected_notice_claim
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
    claim = expected_notice_claim("fr")
    profile.ai_consent_given_at = timezone.now()
    profile.ai_consent_notice_version = claim.version
    profile.ai_consent_notice_hash = claim.notice_hash
    profile.ai_consent_notice_locale = claim.locale
    profile.save(
        update_fields=[
            "ai_consent_given_at",
            "ai_consent_notice_version",
            "ai_consent_notice_hash",
            "ai_consent_notice_locale",
        ]
    )


def test_no_scope_is_default_deny(db):
    with pytest.raises(AIEgressDenied, match="outside an authorized egress scope"):
        assert_ai_egress_allowed(TEXT)


def test_scope_is_lazy_and_does_not_block_deterministic_paths(patient):
    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        pass


def test_real_egress_requires_server_side_consent(patient):
    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        with pytest.raises(AIConsentRequired, match="AI consent"):
            assert_ai_egress_allowed(TEXT)


def test_legacy_timestamp_without_notice_evidence_is_denied(patient):
    profile = patient.base_profile
    profile.ai_consent_given_at = timezone.now()
    profile.save(update_fields=["ai_consent_given_at"])

    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        with pytest.raises(AIConsentRequired, match="current patient AI consent"):
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


def test_d24_global_off_denies_existing_scopes_and_provider_calls(patient):
    """An already-open request scope never freezes a consent grant."""
    _grant_global_consent(patient)
    grant_media_consent(patient.id, "meal_vision", IMAGE)

    from core.api.v1.account import withdraw_consent
    from core.llm_gateway import GatewayLLM

    provider = MagicMock()
    with patch("core.llm_gateway.get_llm", return_value=provider):
        gateway = GatewayLLM()
        with ai_egress_scope(patient.id, "companion_chat", TEXT):
            assert_ai_egress_allowed(TEXT)
            status = withdraw_consent(SimpleNamespace(user=patient, META={}))
            assert status["ai_consent_given"] is False
            with pytest.raises(AIConsentRequired, match="AI consent"):
                gateway.complete("Safe system", "Safe user")

    with ai_egress_scope(patient.id, "meal_vision", IMAGE):
        with pytest.raises(AIConsentRequired, match="AI consent"):
            assert_ai_egress_allowed(IMAGE)

    provider.complete.assert_not_called()


def test_d24_reconsent_never_resurrects_revoked_media_grant(patient):
    """A fresh global consent cannot reuse a prior photo permission."""
    _grant_global_consent(patient)
    grant_media_consent(patient.id, "meal_vision", IMAGE)
    from core.api.v1.account import withdraw_consent
    withdraw_consent(SimpleNamespace(user=patient, META={}))
    _grant_global_consent(patient)

    with ai_egress_scope(patient.id, "meal_vision", IMAGE):
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            assert_ai_egress_allowed(IMAGE)


def test_invalid_grant_pair_is_denied(patient):
    with pytest.raises(AIEgressDenied, match="not authorized"):
        grant_media_consent(patient.id, "companion_chat", IMAGE)
    with pytest.raises(AIEgressDenied, match="not a raw-media"):
        grant_media_consent(patient.id, "companion_chat", TEXT)


def test_media_grant_requires_current_global_consent(patient):
    with pytest.raises(AIConsentRequired, match="AI consent"):
        grant_media_consent(patient.id, "meal_vision", IMAGE)


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


def test_d24_photo_provider_cannot_start_without_granular_grant(patient):
    """A global AI notice is not permission to send a photograph."""
    from llm.runtime import execute_external_provider_call

    _grant_global_consent(patient)
    operation = MagicMock(return_value="should never execute")

    with ai_egress_scope(patient.id, "meal_vision", IMAGE):
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            execute_external_provider_call(
                "gemini", IMAGE, "meal_vision", operation
            )

    operation.assert_not_called()


def test_d24_open_photo_scope_checks_revocation_before_provider_start(patient):
    """Revocation is checked on every dispatch, not on scope creation."""
    from llm.runtime import execute_external_provider_call

    _grant_global_consent(patient)
    grant_media_consent(patient.id, "meal_vision", IMAGE)
    operation = MagicMock(return_value="should never execute")

    with ai_egress_scope(patient.id, "meal_vision", IMAGE):
        assert_ai_egress_allowed(IMAGE)
        assert revoke_media_consent(patient.id, "meal_vision", IMAGE) is True
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            execute_external_provider_call(
                "gemini", IMAGE, "meal_vision", operation
            )

    operation.assert_not_called()


def test_d24_photo_grants_are_patient_scoped_and_do_not_cross_a_b_a(patient):
    """A's image grant cannot unlock B, and A's revocation cannot lock B."""
    other = User.objects.create_user(username="egress-other-patient")
    BasePatientProfile.objects.create(
        patient=other, date_of_birth=date(1992, 2, 2)
    )
    _grant_global_consent(patient)
    _grant_global_consent(other)
    grant_media_consent(patient.id, "meal_vision", IMAGE)

    with ai_egress_scope(other.id, "meal_vision", IMAGE):
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            assert_ai_egress_allowed(IMAGE)

    grant_media_consent(other.id, "meal_vision", IMAGE)
    assert revoke_media_consent(patient.id, "meal_vision", IMAGE)

    with ai_egress_scope(other.id, "meal_vision", IMAGE):
        assert assert_ai_egress_allowed(IMAGE).patient_id == other.id

    with ai_egress_scope(patient.id, "meal_vision", IMAGE):
        with pytest.raises(AIConsentRequired, match="Explicit media consent"):
            assert_ai_egress_allowed(IMAGE)


def test_d24_media_grant_does_not_override_pending_processor_approval(patient):
    """Even consented synthetic image data never leaves via an unapproved vendor."""
    from core.ai_processor_policy import AIProcessorPolicyDenied
    from llm.runtime import execute_external_provider_call

    _grant_global_consent(patient)
    grant_media_consent(patient.id, "meal_vision", IMAGE)
    send_external = MagicMock(return_value="forbidden")

    with ai_egress_scope(patient.id, "meal_vision", IMAGE):
        assert_ai_egress_allowed(IMAGE)  # Two-level patient consent is present.
        with pytest.raises(AIProcessorPolicyDenied, match="not approved"):
            execute_external_provider_call(
                "gemini", IMAGE, "meal_vision", send_external
            )

    send_external.assert_not_called()
