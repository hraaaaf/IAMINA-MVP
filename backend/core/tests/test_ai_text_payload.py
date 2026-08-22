"""P0-MENA-1A/1B tests for text minimisation and semantic DLP."""

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
    user = User.objects.create_user(
        username="payload-patient",
        first_name="Amina",
        last_name="El Mansouri",
        email="amina@example.ma",
    )
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


@pytest.mark.parametrize(
    ("value", "finding"),
    [
        ("Contact: patient@example.com", "email"),
        ("Téléphone: +212 6 12 34 56 78", "phone"),
        ("CIN: AB123456", "moroccan_national_id"),
        ("UID: 123e4567-e89b-12d3-a456-426614174000", "uuid"),
        ("Firebase UID: aBcDeFgHiJkLmNoPqRsTuVwX", "firebase_uid"),
        ("Date de naissance: 14/07/1990", "date_of_birth"),
        ("Nom complet: Achraf Benmoussa", "explicit_identity_label"),
        ("الاسم: أشرف بنموسى", "explicit_identity_label"),
        ("العنوان: الرباط", "explicit_identity_label"),
    ],
)
def test_semantic_dlp_denies_identifiers(consenting_patient, value, finding):
    with ai_egress_scope(consenting_patient.id, "companion_chat", TEXT):
        with pytest.raises(AIPayloadDenied, match=finding):
            authorize_text_payload(
                {"system_prompt": "system", "user_prompt": value}
            )


@pytest.mark.parametrize(
    "value",
    [
        "Bonjour Amina, voici votre synthèse.",
        "El Mansouri présente une glycémie à 126 mg/dL.",
        "Compte payload-patient.",
        "Date 1990-01-01.",
    ],
)
def test_current_patient_identity_is_denied_without_identity_label(
    consenting_patient,
    value,
):
    with ai_egress_scope(consenting_patient.id, "companion_chat", TEXT):
        with pytest.raises(AIPayloadDenied, match="current_patient_identity"):
            authorize_text_payload(
                {"system_prompt": "system", "user_prompt": value}
            )


def test_unicode_normalisation_and_invisible_formatting_cannot_bypass_dlp(
    consenting_patient,
):
    full_width_email = "patient＠example．com"
    hidden_phone = "+212\u200b612345678"

    with ai_egress_scope(consenting_patient.id, "companion_chat", TEXT):
        with pytest.raises(AIPayloadDenied, match="email"):
            authorize_text_payload(
                {"system_prompt": "system", "user_prompt": full_width_email}
            )
        with pytest.raises(AIPayloadDenied, match="phone"):
            authorize_text_payload(
                {"system_prompt": "system", "user_prompt": hidden_phone}
            )


def test_documented_redaction_placeholders_are_allowed(consenting_patient):
    redacted = (
        "Patient [PATIENT_NAME], contact [EMAIL] / [PHONE], "
        "identifiant [PATIENT_ID], né(e) le [DATE_OF_BIRTH]."
    )

    with ai_egress_scope(consenting_patient.id, "doctor_brief", TEXT):
        payload = authorize_text_payload(
            {"system_prompt": "system", "user_prompt": redacted}
        )

    assert payload.user_prompt == redacted


def test_clinical_numbers_are_not_mistaken_for_identifiers(consenting_patient):
    clinical_text = (
        "Glycémie 126 mg/dL, HbA1c 7.2 %, poids 82 kg, "
        "insuline basale 18 unités à 22 h."
    )

    with ai_egress_scope(consenting_patient.id, "clinical_summary", TEXT):
        payload = authorize_text_payload(
            {"system_prompt": "system", "user_prompt": clinical_text}
        )

    assert payload.user_prompt == clinical_text


def test_provider_is_not_called_when_consent_is_missing(db):
    user = User.objects.create_user(username="no-payload-consent")
    BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1990, 1, 1),
    )
    provider = MagicMock()
    original_complete = MagicMock()
    provider.complete = original_complete
    provider.stream = MagicMock()
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(user.id, "companion_chat", TEXT):
        with pytest.raises(AIConsentRequired):
            guarded.complete("system", "user")

    original_complete.assert_not_called()


def test_provider_is_not_called_when_payload_is_oversized(consenting_patient):
    provider = MagicMock()
    original_complete = MagicMock()
    provider.complete = original_complete
    provider.stream = MagicMock()
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consenting_patient.id, "doctor_brief", TEXT):
        with pytest.raises(AIPayloadDenied):
            guarded.complete("system", "x" * 16_001)

    original_complete.assert_not_called()


def test_provider_complete_is_not_called_when_dlp_denies_payload(consenting_patient):
    provider = MagicMock()
    original_complete = MagicMock()
    provider.complete = original_complete
    provider.stream = MagicMock()
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consenting_patient.id, "companion_chat", TEXT):
        with pytest.raises(AIPayloadDenied, match="email"):
            guarded.complete("system", "patient@example.com")

    original_complete.assert_not_called()


def test_provider_complete_is_not_called_for_current_patient_name(consenting_patient):
    provider = MagicMock()
    original_complete = MagicMock()
    provider.complete = original_complete
    provider.stream = MagicMock()
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consenting_patient.id, "companion_chat", TEXT):
        with pytest.raises(AIPayloadDenied, match="current_patient_identity"):
            guarded.complete("system", "Amina a une glycémie à 126 mg/dL")

    original_complete.assert_not_called()


def test_provider_stream_is_not_called_when_dlp_denies_payload(consenting_patient):
    provider = MagicMock()
    provider.complete = MagicMock()
    original_stream = MagicMock(return_value=iter(["unsafe"]))
    provider.stream = original_stream
    provider.think = MagicMock()
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consenting_patient.id, "voice_chat", TEXT):
        with pytest.raises(AIPayloadDenied, match="phone"):
            list(guarded.stream("system", "+212 612345678"))

    original_stream.assert_not_called()


def test_provider_think_is_not_called_when_dlp_denies_payload(consenting_patient):
    provider = MagicMock()
    provider.complete = MagicMock()
    provider.stream = MagicMock()
    original_think = MagicMock()
    provider.think = original_think
    guarded = _enforce_text_payload_policy(provider)

    with ai_egress_scope(consenting_patient.id, "doctor_brief", TEXT):
        with pytest.raises(AIPayloadDenied, match="explicit_identity_label"):
            guarded.think("system", "Nom: Achraf")

    original_think.assert_not_called()


def test_valid_payload_reaches_provider_unchanged(consenting_patient, monkeypatch):
    monkeypatch.setattr("llm.factory._provider_policy_name", lambda _: "fallback")
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
