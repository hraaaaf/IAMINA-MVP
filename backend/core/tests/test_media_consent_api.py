"""Regression tests for patient-owned raw-media consent management."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from ninja.errors import HttpError

from core.models import AIMediaConsentGrant, BasePatientProfile
from diabetes.api.v1.profile import (
    grant_ai_media_consent,
    list_ai_media_consents,
    revoke_ai_media_consent,
)


@pytest.fixture
def patient(db):
    user = User.objects.create_user(username="media-consent-api-patient")
    BasePatientProfile.objects.create(patient=user)
    return user


def _request(user):
    return SimpleNamespace(user=user)


def _enable_global_ai_consent(user):
    profile = user.base_profile
    profile.ai_consent_given_at = timezone.now()
    profile.save(update_fields=["ai_consent_given_at"])


def test_list_returns_complete_supported_matrix_as_inactive(patient):
    states = list_ai_media_consents(_request(patient))

    assert [(state["purpose"], state["modality"]) for state in states] == [
        ("document_ingest", "document"),
        ("document_ingest", "image"),
        ("glucometer_ocr", "image"),
        ("meal_vision", "image"),
        ("voice_chat", "audio"),
        ("voice_transcription", "audio"),
    ]
    assert all(state["active"] is False for state in states)
    assert all(state["granted_at"] is None for state in states)


def test_grant_requires_global_ai_consent(patient):
    with pytest.raises(HttpError) as exc_info:
        grant_ai_media_consent(_request(patient), "meal_vision", "image")

    assert exc_info.value.status_code == 409
    assert AIMediaConsentGrant.objects.count() == 0


def test_grant_is_scoped_to_authenticated_patient_and_idempotent(patient):
    other = User.objects.create_user(username="media-consent-api-other")
    BasePatientProfile.objects.create(patient=other, ai_consent_given_at=timezone.now())
    _enable_global_ai_consent(patient)

    first = grant_ai_media_consent(_request(patient), "meal_vision", "image")
    second = grant_ai_media_consent(_request(patient), "meal_vision", "image")

    assert first["active"] is True
    assert second["active"] is True
    assert AIMediaConsentGrant.objects.filter(patient=patient).count() == 1
    assert AIMediaConsentGrant.objects.filter(patient=other).count() == 0


def test_invalid_purpose_modality_pair_is_rejected(patient):
    _enable_global_ai_consent(patient)

    with pytest.raises(HttpError) as exc_info:
        grant_ai_media_consent(_request(patient), "meal_vision", "audio")

    assert exc_info.value.status_code == 422
    assert AIMediaConsentGrant.objects.count() == 0


def test_revoke_is_immediate_and_idempotent(patient):
    _enable_global_ai_consent(patient)
    grant_ai_media_consent(_request(patient), "voice_transcription", "audio")

    first = revoke_ai_media_consent(
        _request(patient), "voice_transcription", "audio"
    )
    second = revoke_ai_media_consent(
        _request(patient), "voice_transcription", "audio"
    )

    grant = AIMediaConsentGrant.objects.get(patient=patient)
    assert first["active"] is False
    assert second["active"] is False
    assert grant.revoked_at is not None


def test_list_reflects_active_and_revoked_state(patient):
    _enable_global_ai_consent(patient)
    grant_ai_media_consent(_request(patient), "document_ingest", "document")
    grant_ai_media_consent(_request(patient), "glucometer_ocr", "image")
    revoke_ai_media_consent(_request(patient), "glucometer_ocr", "image")

    states = {
        (state["purpose"], state["modality"]): state
        for state in list_ai_media_consents(_request(patient))
    }

    assert states[("document_ingest", "document")]["active"] is True
    assert states[("document_ingest", "document")]["granted_at"] is not None
    assert states[("glucometer_ocr", "image")]["active"] is False
    assert states[("glucometer_ocr", "image")]["revoked_at"] is not None
