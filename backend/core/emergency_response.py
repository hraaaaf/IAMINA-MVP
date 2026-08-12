"""Canonical deterministic emergency response authority.

P0.6 invariant: every patient-facing urgent path delegates response composition
here after ``core.input_safety.evaluate_input_safety`` has classified the input.
No generative model participates in classification or response composition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.emergency_operating_mode import PILOT_EMERGENCY_POLICY, append_emergency_disclosure
from core.emergency_resources import ResolvedEmergencyResources, resolve_emergency_resources
from core.input_safety import URGENT, InputSafetyDecision
from core.locale import ResolvedLocale, resolve_patient_locale

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

_MESSAGES: dict[str, dict[str, str]] = {
    "medical": {
        "fr": (
            "Une situation médicale urgente peut être présente. Arrête le chat et "
            "contacte immédiatement les services d’urgence ou une personne de confiance "
            "près de toi."
        ),
        "en": (
            "An urgent medical situation may be present. Stop the chat and contact "
            "emergency services or a trusted person near you now."
        ),
        "ar": (
            "قد تكون هناك حالة طبية طارئة. أوقف المحادثة وتواصل الآن مع خدمات الطوارئ "
            "أو مع شخص موثوق قريب منك."
        ),
        "ar-MA": (
            "يمكن تكون حالة طبية مستعجلة. وقف الشات وتاصل دابا بالمستعجلات ولا بشي "
            "واحد كتثق فيه وقريب ليك."
        ),
    },
    "crisis": {
        "fr": (
            "Ton message indique que tu peux avoir besoin d’une aide humaine immédiate. "
            "Ne reste pas seul·e avec ça : contacte maintenant les services d’urgence "
            "ou une personne de confiance près de toi."
        ),
        "en": (
            "Your message suggests you may need immediate human support. Do not handle "
            "this alone: contact emergency services or a trusted person near you now."
        ),
        "ar": (
            "تشير رسالتك إلى أنك قد تحتاج إلى دعم بشري فوري. لا تبق وحدك مع هذا الأمر: "
            "تواصل الآن مع خدمات الطوارئ أو مع شخص موثوق قريب منك."
        ),
        "ar-MA": (
            "الرسالة ديالك كاتبين باللي يمكن تحتاج دعم من شي إنسان دابا. ما تبقاش "
            "بوحدك مع هاد الشي: تاصل بالمستعجلات ولا بشي واحد كتثق فيه وقريب ليك."
        ),
    },
}

_RESOURCE_PREFIX = {
    "fr": "Contacts d’urgence confirmés",
    "en": "Confirmed emergency contacts",
    "ar": "جهات اتصال الطوارئ المؤكدة",
    "ar-MA": "أرقام المستعجلات المؤكدة",
}


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
    """Prefer the patient's confirmed locale contract, otherwise fail closed generically."""
    if patient is not None:
        try:
            from core.models import BasePatientProfile

            profile = BasePatientProfile.objects.get(patient=patient)
            return resolve_patient_locale(profile)
        except Exception:
            pass
    return fallback_emergency_locale(language, message)


def _response_class(reason: str | None) -> str:
    return "crisis" if reason == "suicidal_ideation" else "medical"


def _render_resources(resources: ResolvedEmergencyResources, language: str) -> str:
    if not resources.country_specific or not resources.contacts:
        return ""
    contacts = " · ".join(f"{item.service}: {item.number}" for item in resources.contacts)
    return f"\n\n{_RESOURCE_PREFIX[language]}: {contacts}."


def compose_emergency_response(
    decision: InputSafetyDecision,
    *,
    locale: ResolvedLocale,
    message: str = "",
) -> EmergencyResponse:
    """Compose the one canonical patient-facing urgent response.

    Classification is deliberately not performed here. Callers must first use
    ``evaluate_input_safety`` and pass the resulting URGENT decision.
    """
    if decision.action != URGENT:
        raise ValueError("Emergency response composition requires an URGENT decision")

    language = normalize_emergency_language(
        locale.dialect or locale.response_language,
        message,
    )
    response_class = _response_class(decision.reason)
    resources = resolve_emergency_resources(locale)
    reply = _MESSAGES[response_class][language] + _render_resources(resources, language)
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
