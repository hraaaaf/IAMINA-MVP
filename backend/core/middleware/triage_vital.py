"""
IAmina — Triage Vital Middleware (Phase 6 Clinical Shield — P0 Safety)
========================================================================
Medical emergency detection layer that sits BEFORE the LLM pipeline.

If the patient's message contains distress keywords (loss of consciousness,
severe hypoglycemia symptoms, cardiac events, etc.), the system:

1. Bypasses the LLM entirely (zero AI latency in emergencies).
2. Returns a fixed, pre-validated emergency response with national emergency numbers.
3. Logs the event with severity=CRITICAL for clinical audit.

This is a P0 safety feature. Any regression here must block deployment.

Coverage: French, Darija transliterations, and common medical terms.

Paths where triage applies are registered via TRIAGE_REGISTRY (core.safety_registry)
during AppConfig.ready() — no hardcoded path tuples in this file.
"""
from __future__ import annotations

import json
import logging
import re

from django.http import JsonResponse
from django.utils import timezone

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# 1. KEYWORD TAXONOMY (multi-lingual)
# ──────────────────────────────────────────────────────────────

# French medical distress terms
_FR_CRITICAL = frozenset([
    "inconscient", "inconsciente", "perd connaissance", "perdu connaissance",
    "perte de connaissance", "coma", "comateux",
    "convulsion", "convulsions", "épilepsie", "crise d'épilepsie",
    "arrêt cardiaque", "infarctus", "crise cardiaque",
    "hypoglycémie sévère", "très bas", "glycémie très basse",
    "j'appelle le samu", "je tombe dans les pommes",
    "ne répond plus", "ne bouge plus", "j'ai du mal à respirer",
    "difficulté à respirer", "essoufflement grave",
    "AVC", "accident vasculaire",
    "vomissements incontrôlables", "vomissement continu",
    "déshydratation grave", "déshydraté",
])

# Darija transliterations (common phonetic spellings — Latin script).
# Death idioms ("kan nmout", "ghad nmout", "imkan mort", "bghit nmout") REMOVED
# from this set on 2026-05-29 — they're now handled by triage_classification with
# hyperbole-aware logic. Keeping them here re-introduced the original bug:
# "kan nmout 3la l7loua" (= I love this cake) firing as glycemic emergency.
_DARIJA_CRITICAL = frozenset([
    "ma3endouch l7al", "tayb3ed 3lik", "ghrib",
    "mchi mezyan", "khrj mn raso", "m3ih",
    "tay7 fl7al", "fqad l3ql", "mabghach y3aweb",
    "sukkar bhal zero", "sukkar bayna", "waqt l7al",
    "3yyan bzaf", "safi", "wqe3",
])

# Arabic script Darija/MSA emergency keywords
# Patients who type in actual Arabic Unicode (not Latin transliteration) must be covered.
_ARABIC_CRITICAL = frozenset([
    "فقدان الوعي", "فقد الوعي", "غيبوبة",
    "تشنج", "تشنجات", "نوبة قلبية", "سكتة قلبية",
    "أزمة قلبية", "صعوبة التنفس", "لا يتنفس",
    "هبوط حاد", "انهيار", "مغشي عليه",
    "سكتة دماغية", "جلطة",
    # Darija Arabic: glycemic distress phrases
    "سكريتي وطا", "السكر وطا", "سكر واطي",
    "كنزووم", "كانزووم",
    "ساقط", "طايح",
    "ما كنشعرش", "ما كنقدرش", "كيدوخني",
    # NOTE: "غادي نموت" and "بغيت نموت" REMOVED (2026-05-29) — now handled by
    # triage_classification (Class 2: suicidal ideation) with hyperbole-aware logic.
])

# Numeric thresholds detected in natural language (regex patterns)
# Requires a glucose-related keyword to be CLOSE to the number (within 20 chars)
# to reduce false positives on non-medical contexts ("40g de sucre glace", "14h").
# Covers Latin-script and Arabic-script glucose terms.
_NUMERIC_PATTERNS: list[re.Pattern] = [
    re.compile(r"(glycémie|glucose|sukkar|sucre\s+de\s+sang|taux\s+de\s+sucre|سكر|سكري|السكر).{0,20}\b[1-4]\d\b", re.IGNORECASE),
    re.compile(r"\b[1-4]\d\b.{0,20}(glycémie|glucose|mg.?dl|sukkar|سكر|سكري|السكر)", re.IGNORECASE),
]

_ALL_KEYWORDS = _FR_CRITICAL | _DARIJA_CRITICAL | _ARABIC_CRITICAL


# ──────────────────────────────────────────────────────────────
# 2. EMERGENCY RESPONSE (fixed, validated by medical advisor)
# ──────────────────────────────────────────────────────────────

_EMERGENCY_RESPONSE_FR = {
    "reply": (
        "⚠️ SITUATION D'URGENCE DÉTECTÉE — Je suspends mon analyse IA.\n\n"
        "🚨 APPELEZ IMMÉDIATEMENT :\n"
        "• 🇫🇷 France : SAMU → 15 | Urgences → 112\n"
        "• 🇲🇦 Maroc : SAMU → 141 | Urgences → 15\n\n"
        "Si le patient est inconscient ou en hypoglycémie sévère :\n"
        "1. Allongez la personne sur le côté (position latérale de sécurité).\n"
        "2. Si consciente et peut avaler : donnez 15g de sucre rapide "
        "(3 sucres, 150mL de jus de fruit).\n"
        "3. Ne donnez RIEN par la bouche si perte de conscience.\n"
        "4. Restez avec le patient jusqu'à l'arrivée des secours.\n\n"
        "IAmina ne peut pas remplacer les soins médicaux d'urgence."
    ),
    "conversation_id": "TRIAGE_VITAL",
    "is_emergency": True,
}

_EMERGENCY_RESPONSE_DARIJA = {
    "reply": (
        "⚠️ KHATR — IAmina waqfat l-analyse dyal AI.\n\n"
        "🚨 ATTISSEL DABA:\n"
        "• 🇲🇦 Maroc : SAMU → 141 | Tawari → 15\n"
        "• 🇫🇷 France : SAMU → 15 | Urgences → 112\n\n"
        "Ila kan lmrid ma3endouch l7al (fqad l3ql aw sukkar wata):\n"
        "1. Dir-o f-janbo (position latérale de sécurité).\n"
        "2. Ila kan sahran w yqder yebla3: 3tih 15g dyal l7elwa "
        "(3 morceaux de sucre aw 150mL dyal 3sir).\n"
        "3. Ma3tih walo mn l-fomm ila kan faqed l7al.\n"
        "4. Bqa m3ah hta ywsel l-mssaada.\n\n"
        "IAmina ma tqderch tbdel l-t3la wriya dyal lwaqt."
    ),
    "conversation_id": "TRIAGE_VITAL",
    "is_emergency": True,
}

# Simple Darija indicator tokens — enough to recognise the language.
# Covers both Latin transliteration and Arabic Unicode script.
# Low-threshold: if any one token matches, reply in Darija (patient's native language).
_DARIJA_INDICATORS = frozenset([
    "wach", "bghit", "nta", "nti", "hna", "huwa",
    "3ndek", "3ndi", "bhal", "dyal", "wqila",
    "sukkar", "3yyan", "bzaf", "ma3endouch", "kan", "lmrid",
    # Arabic-script tokens — single words that unmistakably signal Arabic input
    "سكريتي", "سكري", "كانزووم", "كنزووم", "عندي", "واش", "بغيت",
])


# ──────────────────────────────────────────────────────────────
# 3. LANGUAGE SELECTION
# ──────────────────────────────────────────────────────────────

def _pick_emergency_response(message: str) -> dict:
    """
    Returns the Darija emergency response if the message appears to be in Darija,
    otherwise returns the French response.

    Detection: if any _DARIJA_INDICATORS token appears as a whole word → Darija.
    Intentionally low threshold: in an emergency we prefer the patient's native
    language when there is any signal for it.
    """
    lowered = message.lower()
    for token in _DARIJA_INDICATORS:
        if re.search(r"\b" + re.escape(token) + r"\b", lowered):
            return _EMERGENCY_RESPONSE_DARIJA
    return _EMERGENCY_RESPONSE_FR


# ──────────────────────────────────────────────────────────────
# 4. DETECTION LOGIC
# ──────────────────────────────────────────────────────────────

def detect_vital_distress(text: str) -> bool:
    """
    Returns True if the text contains any critical distress signal.
    Performs case-insensitive, accent-tolerant keyword matching.
    """
    lowered = text.lower()

    # Keyword match
    for keyword in _ALL_KEYWORDS:
        if keyword in lowered:
            return True

    # Numeric pattern match — patterns already require a glucose keyword nearby
    for pattern in _NUMERIC_PATTERNS:
        if pattern.search(lowered):
            return True

    return False


# ──────────────────────────────────────────────────────────────
# 5. DJANGO MIDDLEWARE
# ──────────────────────────────────────────────────────────────

class TriageVitalMiddleware:
    """
    Intercepts POST requests to registered triage paths.
    If vital distress is detected, returns the emergency response immediately,
    bypassing the view and any LLM call.

    Paths are registered via TRIAGE_REGISTRY (core.safety_registry) in each
    module's AppConfig.ready(). No hardcoded path tuples in this file.

    Activation: add 'core.middleware.triage_vital.TriageVitalMiddleware'
    to MIDDLEWARE in settings.py BEFORE the view dispatch (after auth middleware).
    Order matters: UnitGuard → TriageVital → Views.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        if self._is_chat_endpoint(request):
            user_message = self._read_message(request)

            # ── 2-class classifier (NEW) — runs BEFORE legacy keyword match.
            # SUICIDAL_IDEATION → crisis support template (NEVER glycemic instructions).
            # GLYCEMIC_EMERGENCY → glycemic template (same as legacy path).
            # NONE → fall through to legacy keyword match for backward compatibility.
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
                response_payload = {
                    **_pick_emergency_response(user_message),
                    "timestamp": timezone.now().isoformat(),
                }
                return JsonResponse(response_payload, status=200)

            # ── Legacy keyword match (kept for backward compat with existing tests
            #    and frozensets that may catch cases the new classifier doesn't yet).
            if decision.action == URGENT:
                self._log_emergency(request, user_message, kind="legacy_keyword")
                response_payload = {
                    **_pick_emergency_response(user_message),
                    "timestamp": timezone.now().isoformat(),
                }
                return JsonResponse(response_payload, status=200)

        return self.get_response(request)

    # ── private ──

    def _is_chat_endpoint(self, request) -> bool:
        from core.safety_registry import TRIAGE_REGISTRY
        return (
            request.method == "POST"
            and any(request.path.startswith(p) for p in TRIAGE_REGISTRY._paths)
        )

    def _inspect_body(self, request) -> tuple[bool, str]:
        """Returns (distress_detected, user_message_text). Kept for backward compat."""
        message = self._read_message(request)
        return detect_vital_distress(message), message

    def _read_message(self, request) -> str:
        """Parse the request body once; safe on malformed JSON."""
        try:
            payload = json.loads(request.body or b"{}")
            return str(payload.get("message", ""))
        except Exception:
            return ""

    def _patient_region(self, request) -> str:
        """
        Best-effort region detection from patient profile. Defaults to MA
        (target market). Crisis resources differ by region — getting this
        wrong sends a French 3114 number to a Moroccan patient.
        """
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
        """
        Pick reply language: profile preference first, else simple heuristic
        on the message (Arabic indicators → ar-MA, otherwise fr).
        """
        try:
            from core.models import BasePatientProfile
            base = BasePatientProfile.objects.get(patient=request.user)
            pref = (getattr(base, "preferred_language", "") or "").lower()
            if pref in ("fr", "ar", "ar-ma"):
                return pref
        except Exception:
            pass
        # Light fallback: any Darija indicator → ar-MA
        lowered = message.lower()
        for tok in _DARIJA_INDICATORS:
            if re.search(r"\b" + re.escape(tok) + r"\b", lowered):
                return "ar-MA"
        return "fr"

    def _log_emergency(self, request, message: str, kind: str = "legacy") -> None:
        """Logs the distress event. Critical severity for clinical audit trail."""
        user_id = getattr(request.user, "id", "anonymous")
        logger.critical(
            "TriageVital: EMERGENCY DETECTED — kind=%s | user_id=%s | path=%s | snippet='%s'",
            kind,
            user_id,
            request.path,
            message[:120],  # truncate PII risk
        )
