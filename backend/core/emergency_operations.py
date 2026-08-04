"""Fail-closed emergency operating policy for the pilot.

IAMINA currently operates in SELF_CARE_ONLY mode. Audit logging is not clinical
monitoring, and no response may imply that a person or service was notified.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from core.emergency_resources import ResolvedEmergencyResources, resolve_emergency_resources
from core.locale import ResolvedLocale, resolve_patient_locale
from core.models.patient import BasePatientProfile

SELF_CARE_ONLY = "SELF_CARE_ONLY"
HUMAN_MONITORED = "HUMAN_MONITORED"


@dataclass(frozen=True)
class EmergencyOperatingPolicy:
    mode: str
    version: str
    effective_on: date
    owner: str
    human_monitoring_enabled: bool
    alert_dispatch_enabled: bool


ACTIVE_EMERGENCY_POLICY = EmergencyOperatingPolicy(
    mode=SELF_CARE_ONLY,
    version="2026-08-04.1",
    effective_on=date(2026, 8, 4),
    owner="IAmina Safety & Compliance",
    human_monitoring_enabled=False,
    alert_dispatch_enabled=False,
)

# Exact positive claims that are prohibited while no monitored service exists.
# Negated disclosures such as "this alert is not monitored" are intentionally safe.
_PROHIBITED_MONITORING_CLAIMS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"a clinician has been notified",
        r"a doctor has been notified",
        r"our team is monitoring this alert",
        r"an operator will call you",
        r"emergency services have been contacted",
        r"un m[ée]decin a [ée]t[ée] (?:averti|pr[ée]venu|notifi[ée])",
        r"notre [ée]quipe surveille cette alerte",
        r"un op[ée]rateur va vous rappeler",
        r"les secours ont [ée]t[ée] contact[ée]s",
        r"تم إبلاغ الطبيب",
        r"تم الاتصال بخدمات الطوارئ",
    )
)


def _unconfirmed_locale(language: str = "fr") -> ResolvedLocale:
    return ResolvedLocale(
        country_code=None,
        ui_language="fr",
        response_language=language,
        script_preference="latin",
        transliteration_preference="none",
        dialect=None,
        glucose_unit="mg/dL",
        timezone=None,
        country_confirmed=False,
        timezone_confirmed=False,
    )


def resolve_user_emergency_locale(user) -> ResolvedLocale:
    """Resolve emergency country only from an authenticated confirmed profile."""
    if user is None or not bool(getattr(user, "is_authenticated", False)):
        return _unconfirmed_locale()
    try:
        profile = BasePatientProfile.objects.get(patient=user)
    except (BasePatientProfile.DoesNotExist, TypeError, ValueError):
        return _unconfirmed_locale()
    return resolve_patient_locale(profile)


def assert_no_unproven_monitoring_claim(text: str) -> None:
    """Reject positive monitoring/dispatch claims in SELF_CARE_ONLY mode."""
    if ACTIVE_EMERGENCY_POLICY.mode != SELF_CARE_ONLY:
        return
    for pattern in _PROHIBITED_MONITORING_CLAIMS:
        if pattern.search(text):
            raise ValueError("Unproven human-monitoring claim in emergency response")


def _language_code(language: str | None, locale: ResolvedLocale) -> str:
    selected = (language or locale.response_language or "fr").lower()
    if selected in {"ar-ma", "darija"}:
        return "ar-ma"
    if selected.startswith("ar"):
        return "ar"
    if selected.startswith("en"):
        return "en"
    return "fr"


def _contacts_line(resources: ResolvedEmergencyResources, language: str) -> str:
    if not resources.country_specific:
        return ""
    contacts = " · ".join(f"{item.service}: {item.number}" for item in resources.contacts)
    if language == "en":
        return f"Verified public emergency contacts for {resources.country_code}: {contacts}. "
    if language in {"ar", "ar-ma"}:
        return f"أرقام الطوارئ العمومية المتحقق منها في {resources.country_code}: {contacts}. "
    return f"Contacts publics d’urgence vérifiés pour {resources.country_code} : {contacts}. "


def _emergency_text(resources: ResolvedEmergencyResources, language: str) -> str:
    contacts = _contacts_line(resources, language)
    if language == "en":
        text = (
            "This may be an emergency. Stop using the chat and contact local emergency "
            f"services now. {contacts}IAMINA has not notified anyone, this alert is not "
            "monitored, and the app does not dispatch emergency services."
        )
    elif language == "ar":
        text = (
            "قد تكون هذه حالة طارئة. أوقف استخدام الدردشة واتصل بخدمات الطوارئ المحلية "
            f"فوراً. {contacts}لم تُبلّغ IAMINA أي شخص، ولا تتم مراقبة هذا التنبيه، "
            "ولا يرسل التطبيق خدمات الطوارئ."
        )
    elif language == "ar-ma":
        text = (
            "هاد الحالة تقدر تكون طارئة. وقف الشات واتاصل دابا بخدمات الطوارئ المحلية. "
            f"{contacts}IAMINA ما خبرات حتى واحد، هاد التنبيه ما كيراقبوش شي ناس، "
            "والتطبيق ما كيرسلش خدمات الطوارئ."
        )
    else:
        text = (
            "Cette situation peut être urgente. Arrêtez le chat et contactez immédiatement "
            f"les services d’urgence locaux. {contacts}IAMINA n’a averti personne, cette "
            "alerte n’est pas surveillée et l’application ne déclenche aucun secours."
        )
    assert_no_unproven_monitoring_claim(text)
    return text


def build_emergency_payload(
    user,
    *,
    reason: str,
    language: str | None = None,
    today: date | None = None,
) -> dict:
    """Build one deterministic emergency payload for text, SSE and voice paths."""
    locale = resolve_user_emergency_locale(user)
    resources = resolve_emergency_resources(locale, today=today)
    selected_language = _language_code(language, locale)
    return {
        "reply": _emergency_text(resources, selected_language),
        "conversation_id": "TRIAGE_CRISIS" if reason == "suicidal_ideation" else "TRIAGE_VITAL",
        "is_emergency": True,
        "reply_language": selected_language,
        "operating_mode": ACTIVE_EMERGENCY_POLICY.mode,
        "policy_version": ACTIVE_EMERGENCY_POLICY.version,
        "human_monitoring": ACTIVE_EMERGENCY_POLICY.human_monitoring_enabled,
        "alert_dispatched": ACTIVE_EMERGENCY_POLICY.alert_dispatch_enabled,
        "resource_status": resources.safe_message_code,
        "country_code": resources.country_code,
        "resource_verified_on": resources.verified_on.isoformat() if resources.verified_on else None,
    }


def emergency_audit_fields(*, reason: str, payload: dict) -> dict:
    """Return non-sensitive structured fields for emergency audit logging."""
    return {
        "reason": reason,
        "operating_mode": payload["operating_mode"],
        "policy_version": payload["policy_version"],
        "human_monitoring": payload["human_monitoring"],
        "alert_dispatched": payload["alert_dispatched"],
        "resource_status": payload["resource_status"],
        "country_code": payload["country_code"],
    }
