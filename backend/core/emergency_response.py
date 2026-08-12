"""Canonical deterministic emergency response authority.

P0.6 invariant: every patient-facing urgent path delegates response composition
here after ``core.input_safety.evaluate_input_safety`` has classified the input.
No generative model participates in classification or response composition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.emergency_operating_mode import PILOT_EMERGENCY_POLICY, append_emergency_disclosure
from core.emergency_resources import (
    ResolvedEmergencyResources,
    render_medical_emergency_contact,
    resolve_emergency_resources,
)
from core.input_safety import URGENT, InputSafetyDecision
from core.locale import ResolvedLocale, resolve_patient_locale
from core.triage_classification import crisis_support_response

_ARABIC_SCRIPT_MARKERS = (
    "ا",
    "أ",
    "إ",
    "ب",
    "ت",
    "ج",
    "ح",
    "د",
    "ر",
    "س",
    "ش",
    "ع",
    "ف",
    "ق",
    "ك",
    "ل",
    "م",
    "ن",
    "ه",
    "و",
    "ي",
)
_DARIJA_LATIN_MARKERS = frozenset(
    {"wach", "bghit", "sukkar", "3ndi", "3ndek", "daba", "bzaf", "mzyan"}
)


@dataclass(frozen=True, slots=True)
class EmergencyResponse:
    reply: str
    conversation_id: str
    is_emergency: bool
    reply_language: str
    reason: str
    response_class: str
    resources: ResolvedEmergencyResources
    emergency_operating_mode: str
    human_monitoring: bool

    def as_payload(self, *, timestamp: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "reply": self.reply,
            "conversation_id": self.conversation_id,
            "is_emergency": self.is_emergency,
            "reply_language": self.reply_language,
            "emergency_reason": self.reason,
            "emergency_response_class": self.response_class,
            "emergency_operating_mode": self.emergency_operating_mode,
            "human_monitoring": self.human_monitoring,
            "emergency_resources": [
                {"service": item.service, "number": item.number}
                for item in self.resources.contacts
            ],
            "emergency_resource_code": self.resources.safe_message_code,
        }
        if timestamp is not None:
            payload["timestamp"] = timestamp
        return payload

    def as_stream_event(self) -> dict[str, Any]:
        payload = self.as_payload()
        payload["token"] = payload.pop("reply")
        payload.pop("conversation_id", None)
        return payload


def normalize_emergency_language(language: str | None, message: str = "") -> str:
    """Resolve a supported response language without inferring jurisdiction."""
    candidate = (language or "").strip()
    lowered = candidate.lower()
    if lowered == "ar-ma":
        return "ar-MA"
    if lowered in {"fr", "en", "ar"}:
        return lowered

    normalized_message = message.lower()
    if any(marker in message for marker in _ARABIC_SCRIPT_MARKERS):
        return "ar-MA"
    tokens = set(normalized_message.replace("?", " ").replace("!", " ").split())
    if tokens & _DARIJA_LATIN_MARKERS:
        return "ar-MA"
    return "fr"


def fallback_emergency_locale(
    language: str | None = None,
    message: str = "",
) -> ResolvedLocale:
    """Build a jurisdiction-neutral locale when no confirmed patient locale exists."""
    response_language = normalize_emergency_language(language, message)
    return ResolvedLocale(
        country_code=None,
        ui_language=response_language if response_language != "ar-MA" else "ar",
        response_language=response_language,
        script_preference=(
            "arabic" if response_language in {"ar", "ar-MA"} else "latin"
        ),
        transliteration_preference="none",
        dialect="ar-MA" if response_language == "ar-MA" else None,
        glucose_unit="mg/dL",
        timezone=None,
        country_confirmed=False,
        timezone_confirmed=False,
    )


def resolve_emergency_locale(
    patient=None,
    *,
    language: str | None = None,
    message: str = "",
) -> ResolvedLocale:
    """Prefer confirmed patient locale; otherwise fail closed to generic jurisdiction."""
    if patient is not None:
        try:
            from core.models import BasePatientProfile

            profile = BasePatientProfile.objects.get(patient=patient)
            return resolve_patient_locale(profile)
        except Exception:
            pass
    return fallback_emergency_locale(language, message)


def _preferred_emergency_language(locale: ResolvedLocale, message: str) -> str:
    """Respect confirmed response language; Darija refines only an Arabic choice."""
    preferred = locale.response_language
    if preferred == "ar" and locale.dialect == "ar-MA":
        preferred = "ar-MA"
    return normalize_emergency_language(preferred, message)


def _response_class(reason: str | None) -> str:
    return "crisis" if reason == "suicidal_ideation" else "medical"


def _medical_reply(locale: ResolvedLocale, language: str) -> str:
    contact_line = render_medical_emergency_contact(locale, language=language)
    if language in {"ar-MA", "ar"}:
        return (
            "⚠️ تنبيه صحي عاجل — IAmina وقفات التحليل الآلي.\n\n"
            f"🚨 {contact_line}\n\n"
            "إلا كان الشخص واعي ويقدر يبلع، طبقو خطة نقص السكر اللي سبق شرحها الفريق الصحي. "
            "إلا كان فاقد الوعي، ما تعطيوه والو من الفم وبقاو معاه حتى توصل المساعدة.\n\n"
            "IAmina ما كتبدلش الرعاية الطبية المستعجلة."
        )
    if language == "en":
        return (
            "⚠️ URGENT HEALTH SITUATION DETECTED — IAmina has stopped AI analysis.\n\n"
            f"🚨 {contact_line}\n\n"
            "If the person is conscious and can swallow, follow the hypoglycemia plan "
            "already agreed with their care team. If they are unconscious, give nothing "
            "by mouth and stay with them until emergency help arrives.\n\n"
            "IAmina does not replace emergency medical care."
        )
    return (
        "⚠️ SITUATION D'URGENCE DÉTECTÉE — IAmina suspend l'analyse IA.\n\n"
        f"🚨 {contact_line}\n\n"
        "Si la personne est consciente et peut avaler, suivez le plan d'hypoglycémie "
        "déjà validé avec son équipe soignante. Si elle est inconsciente, ne donnez rien "
        "par la bouche et restez avec elle jusqu'à l'arrivée des secours.\n\n"
        "IAmina ne remplace pas les soins médicaux d'urgence."
    )


def _crisis_reply(locale: ResolvedLocale, language: str) -> tuple[str, str]:
    """Preserve the pre-P0.6 deterministic crisis copy; do not silently rewrite it."""
    region = (
        locale.country_code
        if locale.country_confirmed and locale.country_code in {"MA", "FR"}
        else "MA"
    )
    effective_language = language if language in {"fr", "ar", "ar-MA"} else "fr"
    return crisis_support_response(region=region, lang=effective_language), effective_language


def compose_emergency_response(
    decision: InputSafetyDecision,
    *,
    locale: ResolvedLocale,
    message: str = "",
) -> EmergencyResponse:
    """Compose the one canonical patient-facing urgent response."""
    if decision.action != URGENT:
        raise ValueError("Emergency response composition requires an URGENT decision")

    language = _preferred_emergency_language(locale, message)
    response_class = _response_class(decision.reason)
    resources = resolve_emergency_resources(locale)
    if response_class == "crisis":
        reply, language = _crisis_reply(locale, language)
    else:
        reply = _medical_reply(locale, language)
    reply = append_emergency_disclosure(reply, language)

    return EmergencyResponse(
        reply=reply,
        conversation_id="TRIAGE_CRISIS" if response_class == "crisis" else "TRIAGE_VITAL",
        is_emergency=True,
        reply_language=language,
        reason=decision.reason or "urgent",
        response_class=response_class,
        resources=resources,
        emergency_operating_mode=PILOT_EMERGENCY_POLICY.mode,
        human_monitoring=PILOT_EMERGENCY_POLICY.human_monitoring,
    )


def compose_emergency_for_patient(
    decision: InputSafetyDecision,
    *,
    patient=None,
    language: str | None = None,
    message: str = "",
) -> EmergencyResponse:
    """Resolve locale/resources and compose an urgent response at one authority boundary."""
    locale = resolve_emergency_locale(patient, language=language, message=message)
    return compose_emergency_response(decision, locale=locale, message=message)
