"""Deterministic server-side resolver for patient locale preferences."""

from __future__ import annotations

from dataclasses import dataclass

from core.models.locale import PatientLocalePreference
from core.models.patient import BasePatientProfile

USER_CONFIRMED = "user_confirmed"


@dataclass(frozen=True)
class ResolvedLocale:
    country_code: str | None
    ui_language: str
    response_language: str
    script_preference: str
    transliteration_preference: str
    dialect: str | None
    glucose_unit: str
    timezone: str | None
    country_confirmed: bool
    timezone_confirmed: bool


def _confirmed(value: str | None, provenance: str) -> str | None:
    return value if value and provenance == USER_CONFIRMED else None


def resolve_patient_locale(profile: BasePatientProfile) -> ResolvedLocale:
    """Resolve only confirmed settings; unconfirmed values cannot control behaviour."""
    try:
        preference = profile.locale_preference
    except PatientLocalePreference.DoesNotExist:
        preference = None

    if preference is None:
        return ResolvedLocale(
            country_code=None,
            ui_language="fr",
            response_language="fr",
            script_preference="latin",
            transliteration_preference="none",
            dialect=None,
            glucose_unit="mg/dL",
            timezone=None,
            country_confirmed=False,
            timezone_confirmed=False,
        )

    confirmed_ui = _confirmed(preference.ui_language, preference.ui_language_provenance)
    confirmed_response = _confirmed(
        preference.response_language,
        preference.response_language_provenance,
    )
    confirmed_script = _confirmed(preference.script_preference, preference.script_provenance)
    confirmed_transliteration = _confirmed(
        preference.transliteration_preference,
        preference.transliteration_provenance,
    )
    confirmed_dialect = _confirmed(preference.dialect, preference.dialect_provenance)
    confirmed_unit = _confirmed(preference.glucose_unit, preference.glucose_unit_provenance)
    confirmed_country = _confirmed(preference.country_code, preference.country_provenance)
    confirmed_timezone = _confirmed(preference.timezone, preference.timezone_provenance)

    if confirmed_response:
        response_language = confirmed_response
    elif confirmed_script == "arabic":
        response_language = "ar"
    elif confirmed_ui == "en":
        response_language = "en"
    else:
        response_language = "fr"

    return ResolvedLocale(
        country_code=confirmed_country,
        ui_language=confirmed_ui or "fr",
        response_language=response_language,
        script_preference=confirmed_script or "latin",
        transliteration_preference=confirmed_transliteration or "none",
        dialect=confirmed_dialect,
        glucose_unit=confirmed_unit or "mg/dL",
        timezone=confirmed_timezone,
        country_confirmed=confirmed_country is not None,
        timezone_confirmed=confirmed_timezone is not None,
    )
