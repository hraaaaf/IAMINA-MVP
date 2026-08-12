"""Shared patient-visible medical emergency response rendering.

This module owns no clinical detection and no treatment instructions. Callers
arrive here only after deterministic safety logic has classified the input as
urgent. Jurisdiction-specific contact numbers come exclusively from the
versioned emergency-resource registry and therefore require confirmed locale
provenance.
"""
from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from core.emergency_resources import render_medical_emergency_contact
from core.locale import ResolvedLocale, resolve_patient_locale


def _unconfirmed_locale(language: str) -> ResolvedLocale:
    response_language = language if language in {"fr", "ar", "ar-MA", "en"} else "fr"
    return ResolvedLocale(
        country_code=None,
        ui_language="fr",
        response_language=response_language,
        script_preference="arabic" if response_language in {"ar", "ar-MA"} else "latin",
        transliteration_preference="none",
        dialect="ar-MA" if response_language == "ar-MA" else None,
        glucose_unit="mg/dL",
        timezone=None,
        country_confirmed=False,
        timezone_confirmed=False,
    )


def render_patient_medical_emergency_response(patient, *, language: str = "fr") -> str:
    """Render the deterministic urgent response for a patient or anonymous caller.

    A missing patient/profile/locale fails closed to a number-free response.
    The caller-selected language controls wording only; it never establishes a
    country or authorizes a jurisdictional emergency number.
    """
    locale = _unconfirmed_locale(language)
    if patient is not None:
        try:
            profile = patient.base_profile
        except (AttributeError, ObjectDoesNotExist):
            profile = None
        if profile is not None:
            locale = resolve_patient_locale(profile)

    contact = render_medical_emergency_contact(locale, language=language)
    if language == "ar-MA":
        return f"⚠️ هادي حالة مستعجلة. IAmina ماشي خدمة ديال الطوارئ. {contact}"
    if language == "ar":
        return f"⚠️ هذه حالة طارئة. IAmina ليست خدمة طوارئ. {contact}"
    if language == "en":
        return f"⚠️ This may be an emergency. IAmina is not an emergency service. {contact}"
    return f"⚠️ Cela peut être une urgence. IAmina n'est pas un service d'urgence. {contact}"
