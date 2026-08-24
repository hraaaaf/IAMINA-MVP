"""Authenticated patient locale-preference API.

GET    /api/v1/profile/locale
PATCH  /api/v1/profile/locale
DELETE /api/v1/profile/locale/{dimension}
"""

from __future__ import annotations

from typing import Optional

from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, field_validator

from core.locale import resolve_patient_locale
from core.models.locale import PatientLocalePreference
from core.models.patient import BasePatientProfile

router = Router(tags=["locale"])

_LANGUAGE_VALUES = {"fr", "ar", "en"}
_SCRIPT_VALUES = {"latin", "arabic"}
_TRANSLITERATION_VALUES = {"none", "latin_arabic"}
_DIALECT_VALUES = {value for value, _label in PatientLocalePreference.DIALECT_CHOICES}
_GLUCOSE_UNIT_VALUES = {"mg/dL", "mmol/L"}

_DIMENSIONS = {
    "country_code": (None, "country_provenance"),
    "ui_language": ("fr", "ui_language_provenance"),
    "response_language": (None, "response_language_provenance"),
    "script_preference": (None, "script_provenance"),
    "transliteration_preference": ("none", "transliteration_provenance"),
    "dialect": (None, "dialect_provenance"),
    "glucose_unit": ("mg/dL", "glucose_unit_provenance"),
    "timezone": (None, "timezone_provenance"),
}


class LocalePatchSchema(BaseModel):
    """Supplied values are explicit authenticated-patient confirmations."""

    country_code: Optional[str] = None
    ui_language: Optional[str] = None
    response_language: Optional[str] = None
    script_preference: Optional[str] = None
    transliteration_preference: Optional[str] = None
    dialect: Optional[str] = None
    glucose_unit: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator("country_code")
    @classmethod
    def validate_country(cls, value):
        if value is None:
            return value
        normalized = value.upper()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError("country_code must be an ISO 3166-1 alpha-2 code")
        return normalized

    @field_validator("ui_language", "response_language")
    @classmethod
    def validate_language(cls, value):
        if value is not None and value not in _LANGUAGE_VALUES:
            raise ValueError(f"language must be one of {sorted(_LANGUAGE_VALUES)}")
        return value

    @field_validator("script_preference")
    @classmethod
    def validate_script(cls, value):
        if value is not None and value not in _SCRIPT_VALUES:
            raise ValueError(f"script_preference must be one of {sorted(_SCRIPT_VALUES)}")
        return value

    @field_validator("transliteration_preference")
    @classmethod
    def validate_transliteration(cls, value):
        if value is not None and value not in _TRANSLITERATION_VALUES:
            raise ValueError(
                "transliteration_preference must be one of "
                f"{sorted(_TRANSLITERATION_VALUES)}"
            )
        return value

    @field_validator("dialect")
    @classmethod
    def validate_dialect(cls, value):
        if value is not None and value not in _DIALECT_VALUES:
            raise ValueError(f"dialect must be one of {sorted(_DIALECT_VALUES)}")
        return value

    @field_validator("glucose_unit")
    @classmethod
    def validate_glucose_unit(cls, value):
        if value is not None and value not in _GLUCOSE_UNIT_VALUES:
            raise ValueError(f"glucose_unit must be one of {sorted(_GLUCOSE_UNIT_VALUES)}")
        return value


class LocaleStateSchema(BaseModel):
    stored: dict
    resolved: dict


def _profile_for(user) -> BasePatientProfile:
    try:
        return BasePatientProfile.objects.get(patient=user)
    except BasePatientProfile.DoesNotExist as exc:
        raise HttpError(404, "Profile not found") from exc


def _preference_for(profile: BasePatientProfile) -> PatientLocalePreference:
    preference, _ = PatientLocalePreference.objects.get_or_create(profile=profile)
    return preference


def _serialize(profile: BasePatientProfile, preference: PatientLocalePreference) -> dict:
    resolved = resolve_patient_locale(profile)
    stored = {
        dimension: {
            "value": getattr(preference, dimension),
            "provenance": getattr(preference, provenance_field),
            "confirmed": getattr(preference, provenance_field) == "user_confirmed",
        }
        for dimension, (_, provenance_field) in _DIMENSIONS.items()
    }
    return {
        "stored": stored,
        "resolved": {
            "country_code": resolved.country_code,
            "ui_language": resolved.ui_language,
            "response_language": resolved.response_language,
            "script_preference": resolved.script_preference,
            "transliteration_preference": resolved.transliteration_preference,
            "dialect": resolved.dialect,
            "glucose_unit": resolved.glucose_unit,
            "timezone": resolved.timezone,
            "country_confirmed": resolved.country_confirmed,
            "timezone_confirmed": resolved.timezone_confirmed,
        },
    }


@router.get("/profile/locale", response=LocaleStateSchema)
def get_locale_preferences(request):
    profile = _profile_for(request.user)
    return _serialize(profile, _preference_for(profile))


@router.patch("/profile/locale", response=LocaleStateSchema)
def confirm_locale_preferences(request, data: LocalePatchSchema):
    """Confirm only explicitly supplied dimensions for the authenticated patient."""
    profile = _profile_for(request.user)
    preference = _preference_for(profile)
    supplied = data.model_dump(exclude_unset=True)
    if not supplied:
        raise HttpError(422, "At least one locale dimension is required")
    if any(value is None for value in supplied.values()):
        raise HttpError(422, "Use the dimension DELETE endpoint to revoke a setting")

    update_fields: list[str] = []
    for dimension, value in supplied.items():
        _, provenance_field = _DIMENSIONS[dimension]
        setattr(preference, dimension, value)
        setattr(preference, provenance_field, "user_confirmed")
        update_fields.extend([dimension, provenance_field])

    preference.save(update_fields=[*update_fields, "updated_at"])
    return _serialize(profile, preference)


@router.delete("/profile/locale/{dimension}", response=LocaleStateSchema)
def revoke_locale_preference(request, dimension: str):
    """Revoke one dimension without changing any other patient preference."""
    if dimension not in _DIMENSIONS:
        raise HttpError(404, "Unknown locale dimension")

    profile = _profile_for(request.user)
    preference = _preference_for(profile)
    default_value, provenance_field = _DIMENSIONS[dimension]
    setattr(preference, dimension, default_value)
    setattr(preference, provenance_field, "defaulted")
    preference.save(update_fields=[dimension, provenance_field, "updated_at"])
    return _serialize(profile, preference)
