import pytest
from django.contrib.auth.models import User

from ai.api.v1.ai import _get_patient_language
from ai.api.v1.voice import _get_language
from core.models.locale import PatientLocalePreference
from core.models.patient import BasePatientProfile

GULF_DIALECTS = ("ar-SA", "ar-AE", "ar-KW", "ar-QA", "ar-OM")


@pytest.fixture
def patient(db):
    user = User.objects.create_user(username="locale-runtime-patient")
    BasePatientProfile.objects.create(patient=user)
    return user


def test_text_and_voice_default_to_french_without_confirmation(patient):
    assert _get_patient_language(patient) == "fr"
    assert _get_language(patient) == "fr"


def test_suggested_darija_does_not_control_text_or_voice(patient):
    PatientLocalePreference.objects.create(
        profile=patient.base_profile,
        response_language="ar",
        response_language_provenance="suggested",
        dialect="ar-MA",
        dialect_provenance="suggested",
    )

    assert _get_patient_language(patient) == "fr"
    assert _get_language(patient) == "fr"


def test_confirmed_response_language_controls_text_and_voice(patient):
    PatientLocalePreference.objects.create(
        profile=patient.base_profile,
        response_language="en",
        response_language_provenance="user_confirmed",
    )

    assert _get_patient_language(patient) == "en"
    assert _get_language(patient) == "en"


def test_confirmed_dialect_is_used_only_after_confirmation(patient):
    PatientLocalePreference.objects.create(
        profile=patient.base_profile,
        response_language="ar",
        response_language_provenance="user_confirmed",
        dialect="ar-MA",
        dialect_provenance="user_confirmed",
    )

    assert _get_patient_language(patient) == "ar-MA"
    assert _get_language(patient) == "ar-MA"


@pytest.mark.parametrize("dialect", GULF_DIALECTS)
def test_confirmed_gulf_dialect_controls_text_and_voice(patient, dialect):
    PatientLocalePreference.objects.create(
        profile=patient.base_profile,
        response_language="ar",
        response_language_provenance="user_confirmed",
        dialect=dialect,
        dialect_provenance="user_confirmed",
    )

    assert _get_patient_language(patient) == dialect
    assert _get_language(patient) == dialect


@pytest.mark.parametrize("dialect", GULF_DIALECTS)
def test_suggested_gulf_dialect_cannot_control_runtime(patient, dialect):
    PatientLocalePreference.objects.create(
        profile=patient.base_profile,
        response_language="ar",
        response_language_provenance="user_confirmed",
        dialect=dialect,
        dialect_provenance="suggested",
    )

    assert _get_patient_language(patient) == "ar"
    assert _get_language(patient) == "ar"
