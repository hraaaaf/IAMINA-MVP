"""P0-MENA-1A tests for enforceable text payload minimisation."""

from datetime import date
from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.ai_egress import (
    TEXT,
    AIConsentRequired,
    AIPayloadDenied,
    ai_egress_scope,
    authorize_text_payload,
)
from core.models import BasePatientProfile
from llm.factory import _enforce_text_payload_policy


@pytest.fixture
def consenting_patient(db):
    user = User.objects.create_user(username="payload-patient")
    BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1990, 1, 1),
        ai_consent_given_at=timezone.now(),
    )
    return user


def test_text_payload_is_frozen_after_allowlist_validation(consenting_patient):
    with ai_egress_scope(consenting_patient.id, "companion_chat", TEXT):
        payload = authorize_text_payload(
            {"system_prompt": "system", "user_prompt": "bonjour"}
        )

    assert payload.purpose == "companion_chat"
    assert payload.system_prompt == "system"
    assert payload.user_prompt == "bonjour"
    with pytest.raises(TypeError):
        payload.fields["user_prompt"] = "mutated"


def test_unknown_payload_field_is_denied(consenting_patient):
    with ai_egress_scope(consenting_patient.id, "companion_chat", TEXT):
        with pytest.raises(AIPayloadDenied, match="Unknown text payload fields"):
            authorize_text_payload(
                {
                    "system_prompt": "system",
                    "user_prompt": "bonjour",
                    "patient_name": "must never be accepted",
                }
            )


def test_missing_payload_field_is_denied(consenting_patient):
    with ai_egress_scope(consenting_patient.id, "doctor_brief", TEXT):
        with pytest.raises(AIPayloadDenied, match="Missing text payload fields"):
            authorize_text_payload({"system_prompt": "system"})


def test_non_string_and_nul_payloads_are_denied(consenting_patient):
    with ai_egress_scope(consenting_patient.id, "clinical_summary", TEXT):
        with pytest.raises(AIPayloadDenied, match="must be a string"):
            authorize_text_payload(
                {"system_prompt": "system", "user_prompt": {"raw": "clinical"}}
            )
        with pytest.raises(AIPayloadDenied, match="NUL byte"):
            authorize_text_payload(
                {"system_prompt": "system", "user_prompt": "unsafe\x00payload"}
            )


def test_purpose_specific_size_limit_is_enforced(consenting_patient):
    with ai_egress_scope(consenting_patient.id, "doctor_brief", TEXT):
        with pytest.raises(AIPayloadDenied, match="16000 character limit"):
            authorize_text_payload(
                {"system_prompt": "system", "user_prompt": "x" * 16_001}
            )


def test_provider_is_not_called_when_consent_is_missing(db):
    user = User.objects.create_user(username="no-payload-consent")
    BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1990, 1, 1),
    )
    provider = MagicMock()
    provider.complete = MagicMock()
    provider.stream = MagicMock()
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(user.id, "companion_chat", TEXT):
        with pytest.raises(AIConsentRequired):
            guarded.complete("system", "user")

    provider.complete.assert_not_called()


def test_provider_is_not_called_when_payload_is_oversized(consenting_patient):
    provider = MagicMock()
    provider.complete = MagicMock()
    provider.stream = MagicMock()
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consenting_patient.id, "doctor_brief", TEXT):
        with pytest.raises(AIPayloadDenied):
            guarded.complete("system", "x" * 16_001)

    provider.complete.assert_not_called()


def test_valid_payload_reaches_provider_unchanged(consenting_patient):
    provider = MagicMock()
    original_complete = MagicMock(return_value="ok")
    provider.complete = original_complete
    provider.stream = MagicMock()
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consenting_patient.id, "companion_chat", TEXT):
        result = guarded.complete("system", "bonjour")

    assert result == "ok"
    original_complete.assert_called_once_with("system", "bonjour")
