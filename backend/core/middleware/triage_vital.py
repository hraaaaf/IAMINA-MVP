"""
IAmina — deterministic vital-triage middleware.

This layer runs before generative AI on registered triage paths. Glycemic
emergency classification remains deterministic. Patient-visible emergency
numbers are never hard-coded here: they are selected by the versioned
``core.emergency_resources`` registry only when the patient's country is
explicitly confirmed and the resource policy is current.
"""
from __future__ import annotations

import json
import logging
import re

from django.http import JsonResponse
from django.utils import timezone

from core.emergency_resources import render_medical_emergency_contact
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
    """Number-free locale used when no confirmed profile can be resolved."""
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
    """Build deterministic glycemic emergency copy with jurisdiction-safe contact."""
    resolved_locale = locale or _generic_locale()
    reply_language = language or _message_language(message)
    contact_line = render_medical_emergency_contact(
        resolved_locale,
        language=reply_language,
    )

    if reply_language in ("ar-MA", "ar"):
        reply = (
            "⚠️ تنبيه صحي عاجل — IAmina وقفات التحليل الآلي.\n\n"
            f"🚨 {contact_line}\n\n"
            "إلا كان الشخص واعي ويقدر يبلع، طبقو خطة نقص السكر اللي سبق شرحها الفريق الصحي. "
            "إلا كان فاقد الوعي، ما تعطيوه والو من الفم وبقاو معاه حتى توصل المساعدة.\n\n"
            "IAmina ما كتبدلش الرعاية الطبية المستعجلة."
        )
    else:
        reply = (
            "⚠️ SITUATION D'URGENCE DÉTECTÉE — IAmina suspend l'analyse IA.\n\n"
            f"🚨 {contact_line}\n\n"
            "Si la personne est consciente et peut avaler, suivez le plan d'hypoglycémie "
            "déjà validé avec son équipe soignante. Si elle est inconsciente, ne donnez rien "
            "par la bouche et restez avec elle jusqu'à l'arrivée des secours.\n\n"
            "IAmina ne remplace pas les soins médicaux d'urgence."
        )

    return {
        "reply": reply,
        "conversation_id": "TRIAGE_VITAL",
        "is_emergency": True,
    }


def detect_vital_distress(text: str) -> bool:
    """Return True when the legacy deterministic distress corpus matches."""
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

            from core.input_safety import URGENT, evaluate_input_safety
            from diabetes.middleware.triage_classification import crisis_support_response

            decision = evaluate_input_safety(user_message)

            if decision.action == URGENT and decision.reason == "suicidal_ideation":
                self._log_emergency(request, user_message, kind="ideation")
                region = self._patient_region(request)
                lang = self._patient_lang(request, user_message)
                response_payload = {
                    "reply": crisis_support_response(region=region, lang=lang),
                    "conversation_id": "TRIAGE_CRISIS",
                    "is_emergency": True,
                    "timestamp": timezone.now().isoformat(),
                }
                return JsonResponse(response_payload, status=200)

            if decision.action == URGENT and decision.reason == "glycemic_emergency":
                self._log_emergency(request, user_message, kind="glycemic_classified")
                locale = self._patient_locale(request)
                lang = self._patient_lang(request, user_message, locale=locale)
                response_payload = {
                    **_pick_emergency_response(
                        user_message,
                        locale=locale,
                        language=lang,
                    ),
                    "timestamp": timezone.now().isoformat(),
                }
                return JsonResponse(response_payload, status=200)

            if decision.action == URGENT:
                self._log_emergency(request, user_message, kind="legacy_keyword")
                locale = self._patient_locale(request)
                lang = self._patient_lang(request, user_message, locale=locale)
                response_payload = {
                    **_pick_emergency_response(
                        user_message,
                        locale=locale,
                        language=lang,
                    ),
                    "timestamp": timezone.now().isoformat(),
                }
                return JsonResponse(response_payload, status=200)

        return self.get_response(request)

    def _is_chat_endpoint(self, request) -> bool:
        from core.safety_registry import TRIAGE_REGISTRY

        return request.method == "POST" and any(
            request.path.startswith(path) for path in TRIAGE_REGISTRY._paths
        )

    def _inspect_body(self, request) -> tuple[bool, str]:
        """Return legacy `(distress_detected, message)` compatibility shape."""
        message = self._read_message(request)
        return detect_vital_distress(message), message

    def _read_message(self, request) -> str:
        try:
            payload = json.loads(request.body or b"{}")
            return str(payload.get("message", ""))
        except Exception:
            return ""

    def _patient_locale(self, request) -> ResolvedLocale:
        """Resolve country only from the explicit locale-preference provenance contract."""
        try:
            from core.models import BasePatientProfile

            profile = BasePatientProfile.objects.get(patient=request.user)
            return resolve_patient_locale(profile)
        except Exception:
            return _generic_locale()

    def _patient_region(self, request) -> str:
        """Legacy non-glycemic crisis-resource region helper; unchanged in this LOT."""
        try:
            from core.models import BasePatientProfile

            base = BasePatientProfile.objects.get(patient=request.user)
            region = (getattr(base, "region", "") or "").upper()
            if region in ("MA", "FR"):
                return region
        except Exception:
            pass
        return "MA"

    def _patient_lang(
        self,
        request,
        message: str,
        *,
        locale: ResolvedLocale | None = None,
    ) -> str:
        """Prefer confirmed response locale, then legacy profile preference, then message."""
        if locale is not None and locale.response_language in ("fr", "ar", "en"):
            if locale.response_language == "ar" and locale.dialect == "ar-MA":
                return "ar-MA"
            return locale.response_language
        try:
            from core.models import BasePatientProfile

            base = BasePatientProfile.objects.get(patient=request.user)
            pref = (getattr(base, "preferred_language", "") or "").lower()
            if pref in ("fr", "ar", "ar-ma"):
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
