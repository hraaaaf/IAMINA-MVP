"""
IAmina — deterministic vital-triage middleware.

This layer runs before generative AI on registered triage paths. Emergency
classification remains deterministic. P0.6 makes ``core.emergency_response``
the sole patient-facing response composer; this middleware owns interception,
request extraction and audit logging only.
"""
from __future__ import annotations

import json
import logging
import re

from django.http import JsonResponse
from django.utils import timezone

from core.emergency_response import compose_emergency_response
from core.input_safety import URGENT, InputSafetyDecision, evaluate_input_safety
from core.locale import ResolvedLocale, resolve_patient_locale

logger = logging.getLogger(__name__)


_FR_CRITICAL = frozenset(
    [
        "inconscient",
        "inconsciente",
        "perd connaissance",
        "perdu connaissance",
        "perte de connaissance",
        "coma",
        "comateux",
        "convulsion",
        "convulsions",
        "épilepsie",
        "crise d'épilepsie",
        "arrêt cardiaque",
        "infarctus",
        "crise cardiaque",
        "hypoglycémie sévère",
        "très bas",
        "glycémie très basse",
        "j'appelle le samu",
        "je tombe dans les pommes",
        "ne répond plus",
        "ne bouge plus",
        "j'ai du mal à respirer",
        "difficulté à respirer",
        "essoufflement grave",
        "AVC",
        "accident vasculaire",
        "vomissements incontrôlables",
        "vomissement continu",
        "déshydratation grave",
        "déshydraté",
    ]
)

_DARIJA_CRITICAL = frozenset(
    [
        "ma3endouch l7al",
        "tayb3ed 3lik",
        "ghrib",
        "mchi mezyan",
        "khrj mn raso",
        "m3ih",
        "tay7 fl7al",
        "fqad l3ql",
        "mabghach y3aweb",
        "sukkar bhal zero",
        "sukkar bayna",
        "waqt l7al",
        "3yyan bzaf",
        "safi",
        "wqe3",
    ]
)

_ARABIC_CRITICAL = frozenset(
    [
        "فقدان الوعي",
        "فقد الوعي",
        "غيبوبة",
        "تشنج",
        "تشنجات",
        "نوبة قلبية",
        "سكتة قلبية",
        "أزمة قلبية",
        "صعوبة التنفس",
        "لا يتنفس",
        "هبوط حاد",
        "انهيار",
        "مغشي عليه",
        "سكتة دماغية",
        "جلطة",
        "سكريتي وطا",
        "السكر وطا",
        "سكر واطي",
        "كنزووم",
        "كانزووم",
        "ساقط",
        "طايح",
        "ما كنشعرش",
        "ما كنقدرش",
        "كيدوخني",
    ]
)

_NUMERIC_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"(glycémie|glucose|sukkar|sucre\s+de\s+sang|taux\s+de\s+sucre|سكر|سكري|السكر)"
        r".{0,20}\b[1-4]\d\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b[1-4]\d\b.{0,20}(glycémie|glucose|mg.?dl|sukkar|سكر|سكري|السكر)",
        re.IGNORECASE,
    ),
]

_ALL_KEYWORDS = _FR_CRITICAL | _DARIJA_CRITICAL | _ARABIC_CRITICAL

_DARIJA_INDICATORS = frozenset(
    [
        "wach",
        "bghit",
        "nta",
        "nti",
        "hna",
        "huwa",
        "3ndek",
        "3ndi",
        "bhal",
        "dyal",
        "wqila",
        "sukkar",
        "3yyan",
        "bzaf",
        "ma3endouch",
        "kan",
        "lmrid",
        "سكريتي",
        "سكري",
        "كانزووم",
        "كنزووم",
        "عندي",
        "واش",
        "بغيت",
    ]
)


def _generic_locale() -> ResolvedLocale:
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


def _message_language(message: str) -> str:
    lowered = message.lower()
    for token in _DARIJA_INDICATORS:
        if re.search(r"\b" + re.escape(token) + r"\b", lowered):
            return "ar-MA"
    return "fr"


def _pick_emergency_response(
    message: str,
    *,
    locale: ResolvedLocale | None = None,
    language: str | None = None,
) -> dict:
    """Compatibility helper delegated to the canonical emergency composer."""
    resolved_locale = locale or _generic_locale()
    reply_language = language or _message_language(message)
    if reply_language != resolved_locale.response_language:
        resolved_locale = ResolvedLocale(
            country_code=resolved_locale.country_code,
            ui_language=resolved_locale.ui_language,
            response_language=reply_language,
            script_preference=resolved_locale.script_preference,
            transliteration_preference=resolved_locale.transliteration_preference,
            dialect="ar-MA" if reply_language == "ar-MA" else resolved_locale.dialect,
            glucose_unit=resolved_locale.glucose_unit,
            timezone=resolved_locale.timezone,
            country_confirmed=resolved_locale.country_confirmed,
            timezone_confirmed=resolved_locale.timezone_confirmed,
        )
    response = compose_emergency_response(
        InputSafetyDecision(URGENT, "glycemic_emergency"),
        locale=resolved_locale,
        message=message,
    )
    return response.as_payload()


def detect_vital_distress(text: str) -> bool:
    lowered = text.lower()
    for keyword in _ALL_KEYWORDS:
        if keyword in lowered:
            return True
    for pattern in _NUMERIC_PATTERNS:
        if pattern.search(lowered):
            return True
    return False


class TriageVitalMiddleware:
    """Intercept registered emergency-capable routes before any LLM call."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        if self._is_chat_endpoint(request):
            user_message = self._read_message(request)
            decision = evaluate_input_safety(user_message)
            if decision.action == URGENT:
                self._log_emergency(request, user_message, kind=decision.reason or "urgent")
                locale = self._patient_locale(request)
                language = self._patient_lang(request, user_message)
                if language != (locale.dialect or locale.response_language):
                    locale = ResolvedLocale(
                        country_code=locale.country_code,
                        ui_language=locale.ui_language,
                        response_language=language,
                        script_preference=locale.script_preference,
                        transliteration_preference=locale.transliteration_preference,
                        dialect="ar-MA" if language == "ar-MA" else locale.dialect,
                        glucose_unit=locale.glucose_unit,
                        timezone=locale.timezone,
                        country_confirmed=locale.country_confirmed,
                        timezone_confirmed=locale.timezone_confirmed,
                    )
                response = compose_emergency_response(
                    decision,
                    locale=locale,
                    message=user_message,
                )
                return JsonResponse(
                    response.as_payload(timestamp=timezone.now().isoformat()),
                    status=200,
                )

        return self.get_response(request)

    def _is_chat_endpoint(self, request) -> bool:
        from core.safety_registry import TRIAGE_REGISTRY

        return request.method == "POST" and any(
            request.path.startswith(path) for path in TRIAGE_REGISTRY._paths
        )

    def _inspect_body(self, request) -> tuple[bool, str]:
        message = self._read_message(request)
        return detect_vital_distress(message), message

    def _read_message(self, request) -> str:
        try:
            payload = json.loads(request.body or b"{}")
            return str(payload.get("message", ""))
        except Exception:
            return ""

    def _patient_locale(self, request) -> ResolvedLocale:
        """Resolve country only through explicit locale-preference provenance."""
        try:
            from core.models import BasePatientProfile

            profile = BasePatientProfile.objects.get(patient=request.user)
            return resolve_patient_locale(profile)
        except Exception:
            return _generic_locale()

    def _patient_region(self, request) -> str:
        """Legacy compatibility helper; canonical response does not consume it."""
        try:
            from core.models import BasePatientProfile

            base = BasePatientProfile.objects.get(patient=request.user)
            region = (getattr(base, "region", "") or "").upper()
            if region in ("MA", "FR"):
                return region
        except Exception:
            pass
        return "MA"

    def _patient_lang(self, request, message: str) -> str:
        """Use confirmed locale language, then legacy preference, then message heuristic."""
        try:
            from core.models import BasePatientProfile

            base = BasePatientProfile.objects.get(patient=request.user)
            try:
                preference = base.locale_preference
            except Exception:
                preference = None

            if (
                preference is not None
                and preference.response_language_provenance == "user_confirmed"
                and preference.response_language in ("fr", "ar", "en")
            ):
                if (
                    preference.response_language == "ar"
                    and preference.dialect_provenance == "user_confirmed"
                    and preference.dialect == "ar-MA"
                ):
                    return "ar-MA"
                return preference.response_language

            pref = (getattr(base, "preferred_language", "") or "").lower()
            if pref == "ar-ma":
                return "ar-MA"
            if pref in ("fr", "ar", "en"):
                return pref
        except Exception:
            pass
        return _message_language(message)

    def _log_emergency(self, request, message: str, kind: str = "legacy") -> None:
        user_id = getattr(request.user, "id", "anonymous")
        logger.critical(
            "TriageVital: EMERGENCY DETECTED — kind=%s | user_id=%s | path=%s | snippet='%s'",
            kind,
            user_id,
            request.path,
            message[:120],
        )
