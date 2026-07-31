import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from core.locale import resolve_patient_locale
from core.models.locale import PatientLocalePreference
from core.models.patient import BasePatientProfile


@pytest.fixture
def profile(db):
    user = User.objects.create_user(username="locale-patient")
    return BasePatientProfile.objects.create(patient=user)


def test_missing_record_uses_safe_deterministic_defaults(profile):
    resolved = resolve_patient_locale(profile)
    assert resolved.country_code is None
    assert resolved.ui_language == "fr"
    assert resolved.response_language == "fr"
    assert resolved.dialect is None
    assert resolved.glucose_unit == "mg/dL"
    assert resolved.timezone is None


def test_suggestions_cannot_control_runtime(profile):
    PatientLocalePreference.objects.create(
        profile=profile,
        country_code="MA",
        country_provenance="suggested",
        ui_language="ar",
        ui_language_provenance="suggested",
        response_language="ar",
        response_language_provenance="suggested",
        script_preference="arabic",
        script_provenance="suggested",
        dialect="ar-MA",
        dialect_provenance="suggested",
        glucose_unit="mmol/L",
        glucose_unit_provenance="suggested",
        timezone="Africa/Casablanca",
        timezone_provenance="suggested",
    )
    resolved = resolve_patient_locale(profile)
    assert resolved.country_code is None
    assert resolved.ui_language == "fr"
    assert resolved.response_language == "fr"
    assert resolved.script_preference == "latin"
    assert resolved.dialect is None
    assert resolved.glucose_unit == "mg/dL"
    assert resolved.timezone is None


def test_confirmed_dimensions_remain_independent(profile):
    PatientLocalePreference.objects.create(
        profile=profile,
        country_code="MA",
        country_provenance="user_confirmed",
        ui_language="fr",
        ui_language_provenance="user_confirmed",
        response_language="en",
        response_language_provenance="user_confirmed",
        script_preference="latin",
        script_provenance="user_confirmed",
        glucose_unit="mmol/L",
        glucose_unit_provenance="user_confirmed",
        timezone="Africa/Casablanca",
        timezone_provenance="user_confirmed",
    )
    resolved = resolve_patient_locale(profile)
    assert resolved.country_code == "MA"
    assert resolved.ui_language == "fr"
    assert resolved.response_language == "en"
    assert resolved.glucose_unit == "mmol/L"
    assert resolved.timezone == "Africa/Casablanca"


def test_confirmed_arabic_script_uses_msa_fallback(profile):
    PatientLocalePreference.objects.create(
        profile=profile,
        script_preference="arabic",
        script_provenance="user_confirmed",
    )
    assert resolve_patient_locale(profile).response_language == "ar"


def test_country_is_normalized_and_timezone_is_validated(profile):
    preference = PatientLocalePreference(profile=profile, country_code="ma", timezone="Not/AZone")
    with pytest.raises(ValidationError):
        preference.save()
    preference.timezone = "Africa/Casablanca"
    preference.save()
    assert preference.country_code == "MA"
