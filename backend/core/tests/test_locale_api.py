from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from ninja.errors import HttpError

from core.api.v1.locale import (
    LocalePatchSchema,
    confirm_locale_preferences,
    get_locale_preferences,
    revoke_locale_preference,
)
from core.models.locale import PatientLocalePreference
from core.models.patient import BasePatientProfile

GULF_DIALECTS = ("ar-SA", "ar-AE", "ar-KW", "ar-QA", "ar-OM")


@pytest.fixture
def patient(db):
    user = User.objects.create_user(username="locale-api-patient")
    BasePatientProfile.objects.create(patient=user)
    return user


def _request(user):
    return SimpleNamespace(user=user)


def test_get_is_scoped_to_authenticated_patient(patient):
    other = User.objects.create_user(username="locale-api-other")
    other_profile = BasePatientProfile.objects.create(patient=other)
    PatientLocalePreference.objects.create(
        profile=other_profile,
        ui_language="en",
        ui_language_provenance="user_confirmed",
    )

    state = get_locale_preferences(_request(patient))

    assert state["resolved"]["ui_language"] == "fr"
    assert state["stored"]["ui_language"]["confirmed"] is False


def test_confirmation_promotes_only_supplied_dimensions(patient):
    profile = patient.base_profile
    PatientLocalePreference.objects.create(
        profile=profile,
        country_code="MA",
        country_provenance="suggested",
        ui_language="ar",
        ui_language_provenance="suggested",
    )

    state = confirm_locale_preferences(
        _request(patient),
        LocalePatchSchema(country_code="ma"),
    )

    preference = profile.locale_preference
    preference.refresh_from_db()
    assert preference.country_code == "MA"
    assert preference.country_provenance == "user_confirmed"
    assert preference.ui_language == "ar"
    assert preference.ui_language_provenance == "suggested"
    assert state["resolved"]["country_code"] == "MA"
    assert state["resolved"]["ui_language"] == "fr"


def test_confirmed_dimensions_are_independent(patient):
    state = confirm_locale_preferences(
        _request(patient),
        LocalePatchSchema(
            country_code="MA",
            ui_language="fr",
            response_language="en",
            script_preference="latin",
            glucose_unit="mmol/L",
            timezone="Africa/Casablanca",
        ),
    )

    assert state["resolved"] == {
        "country_code": "MA",
        "ui_language": "fr",
        "response_language": "en",
        "script_preference": "latin",
        "transliteration_preference": "none",
        "dialect": None,
        "glucose_unit": "mmol/L",
        "timezone": "Africa/Casablanca",
        "country_confirmed": True,
        "timezone_confirmed": True,
    }


@pytest.mark.parametrize("dialect", GULF_DIALECTS)
def test_api_can_confirm_each_supported_gulf_dialect(patient, dialect):
    state = confirm_locale_preferences(
        _request(patient),
        LocalePatchSchema(
            response_language="ar",
            dialect=dialect,
        ),
    )

    assert state["resolved"]["response_language"] == "ar"
    assert state["resolved"]["dialect"] == dialect
    assert state["stored"]["dialect"] == {
        "value": dialect,
        "provenance": "user_confirmed",
        "confirmed": True,
    }


def test_revoke_one_dimension_restores_fallback_without_touching_others(patient):
    confirm_locale_preferences(
        _request(patient),
        LocalePatchSchema(
            ui_language="en",
            response_language="en",
            glucose_unit="mmol/L",
        ),
    )

    state = revoke_locale_preference(_request(patient), "response_language")

    assert state["resolved"]["response_language"] == "en"
    assert state["stored"]["response_language"]["confirmed"] is False
    assert state["resolved"]["glucose_unit"] == "mmol/L"


def test_explicit_null_is_rejected_and_requires_delete(patient):
    with pytest.raises(HttpError) as exc_info:
        confirm_locale_preferences(
            _request(patient),
            LocalePatchSchema(response_language=None),
        )

    assert exc_info.value.status_code == 422


def test_empty_patch_is_rejected(patient):
    with pytest.raises(HttpError) as exc_info:
        confirm_locale_preferences(_request(patient), LocalePatchSchema())

    assert exc_info.value.status_code == 422


def test_unknown_dimension_is_rejected(patient):
    with pytest.raises(HttpError) as exc_info:
        revoke_locale_preference(_request(patient), "preferred_language")

    assert exc_info.value.status_code == 404


def test_invalid_timezone_fails_validation(patient):
    with pytest.raises(Exception):
        confirm_locale_preferences(
            _request(patient),
            LocalePatchSchema(timezone="Not/AZone"),
        )
