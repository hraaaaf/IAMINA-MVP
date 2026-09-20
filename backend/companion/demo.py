"""Stateless, zero-model conversation for public demo mode.

The demo endpoint deliberately shares IAMINA's deterministic safety authority
without creating a patient identity, reading clinical data, persisting turns, or
opening an external-model egress path.
"""

from __future__ import annotations

import re

from companion.demo_model import DemoModelUnavailable, DemoPayloadDenied, generate_demo_reply
from companion.output_guard import safe_fallback
from companion.zero_model_router import exact_chitchat_reply
from core.emergency_response import compose_emergency_for_patient
from core.input_safety import (
    INSULIN_BLOCK,
    PRESCRIPTION_BLOCK,
    URGENT,
    evaluate_input_safety,
)
from core.medical_safety import no_prescription_message

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
_ENGLISH_HINT_RE = re.compile(
    r"\b(?:hello|hi|thanks|thank you|doctor|clinician|help|what|how|why)\b",
    re.IGNORECASE,
)
_EMOTIONAL_RE = re.compile(
    r"(?:j['’]?en ai marre|j['’]?en peux plus|fatigu[ée]|[ée]puis[ée]|"
    r"i['’]?m done|exhausted|hopeless|3yit|3yayt|تعبت|عييت|خلاص)",
    re.IGNORECASE,
)
_CLINICIAN_RE = re.compile(
    r"\b(?:m[ée]decin|docteur|doctor|clinician|consultation|rendez-vous)\b|(?:طبيب|دكتور|موعد)",
    re.IGNORECASE,
)
_PERSONAL_DATA_RE = re.compile(
    r"\b(?:mes?\s+(?:donn[ée]es?|glyc[ée]mie|mesures?|r[ée]sultats?|tir|dossier)|"
    r"my\s+(?:data|glucose|readings?|results?|tir|record))\b|"
    r"(?:بياناتي|سكري|قياساتي|نتائجي|ملفي)",
    re.IGNORECASE,
)
_CAPABILITY_RE = re.compile(
    r"(?:que peux[- ]?tu faire|comment (?:tu|ça) fonctionne|qui es[- ]?tu|"
    r"what can you do|how do you work|who are you|"
    r"شنو كتقدر|ماذا يمكنك|من أنت)",
    re.IGNORECASE,
)

_DEMO_COPY = {
    "fr": {
        "capability": (
            "Je suis IAmina en mode démo. Je peux converser, montrer mes garde-fous "
            "et t’aider à organiser une question, sans accéder à un dossier patient."
        ),
        "personal": (
            "En mode démo, je n’ai accès à aucun dossier patient ni donnée personnelle. "
            "Je peux quand même t’aider à formuler ce que tu veux comprendre ou préparer."
        ),
        "general": (
            "Oui, on peut en parler ici. En mode démo je reste sans dossier patient : "
            "dis-moi ce que tu veux comprendre ou préparer, et je resterai dans ce cadre."
        ),
    },
    "en": {
        "capability": (
            "I’m IAmina in demo mode. I can converse, show my safety boundaries, "
            "and help organize a question without accessing a patient record."
        ),
        "personal": (
            "In demo mode I cannot access any patient record or personal health data. "
            "I can still help you frame what you want to understand or prepare."
        ),
        "general": (
            "Yes, we can talk about it here. Demo mode has no patient record, so tell me "
            "what you want to understand or prepare and I’ll stay within that boundary."
        ),
    },
    "ar": {
        "capability": (
            "أنا أمينة في وضع العرض. أستطيع المحادثة وإظهار حدود الأمان ومساعدتك "
            "في تنظيم سؤال، من دون الوصول إلى ملف مريض."
        ),
        "personal": (
            "في وضع العرض لا أستطيع الوصول إلى أي ملف مريض أو بيانات صحية شخصية. "
            "يمكنني مع ذلك مساعدتك في صياغة ما تريد فهمه أو تحضيره."
        ),
        "general": (
            "نعم، يمكننا التحدث هنا. وضع العرض لا يستخدم ملف مريض، فأخبرني بما تريد "
            "فهمه أو تحضيره وسأبقى ضمن هذا الإطار."
        ),
    },
    "ar-MA": {
        "capability": (
            "أنا أمينة فالوضع التجريبي. نقدر نهضر معاك ونوريك حدود الأمان ونعاونك "
            "ترتب سؤال، بلا ما نوصل لملف ديال شي مريض."
        ),
        "personal": (
            "فالوضع التجريبي ما عنديش الوصول لملف المريض ولا لمعطيات صحية شخصية. "
            "نقدر مع ذلك نعاونك تصيغ شنو بغيتي تفهم ولا توجد."
        ),
        "general": (
            "إيوا نقدروا نهضرو هنا. فالوضع التجريبي ما كنستعملش ملف مريض، قول ليا "
            "شنو بغيتي تفهم ولا توجد ونبقى فهاد الحدود."
        ),
    },
}


def resolve_demo_language(message: str, requested: str = "fr") -> str:
    """Resolve a bounded demo language without patient/profile lookup."""
    requested = (requested or "fr").strip()
    if _ARABIC_RE.search(message):
        return "ar-MA" if requested == "ar-MA" else "ar"
    if _ENGLISH_HINT_RE.search(message):
        return "en"
    if requested in _DEMO_COPY:
        return requested
    return "fr"


def reply_to_demo_message(message: str, language: str = "fr") -> dict:
    """Return one stateless governed demo turn.

    No patient object, ORM lookup, conversation persistence, or LLM/provider call
    is permitted in this function.
    """
    text = (message or "").strip()
    if not text:
        raise ValueError("demo message must not be empty")

    reply_language = resolve_demo_language(text, language)
    decision = evaluate_input_safety(text, reply_language)

    if decision.action == URGENT:
        emergency = compose_emergency_for_patient(
            decision,
            patient=None,
            language=reply_language,
            message=text,
        )
        return {
            "reply": emergency.reply,
            "conversation_id": emergency.conversation_id,
            "is_emergency": True,
            "reply_language": emergency.reply_language,
        }

    deterministic_language = "ar" if reply_language == "ar-MA" else reply_language
    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        return {
            "reply": no_prescription_message(deterministic_language),
            "conversation_id": "demo-governed",
            "is_emergency": False,
            "reply_language": reply_language,
        }

    exact = exact_chitchat_reply(text, reply_language)
    if exact is not None:
        return {
            "reply": exact,
            "conversation_id": "demo-governed",
            "is_emergency": False,
            "reply_language": reply_language,
        }

    if _PERSONAL_DATA_RE.search(text):
        reply = _DEMO_COPY[reply_language]["personal"]
    elif _CAPABILITY_RE.search(text):
        reply = _DEMO_COPY[reply_language]["capability"]
    else:
        try:
            reply = generate_demo_reply(text, reply_language)
        except DemoPayloadDenied:
            reply = _DEMO_COPY[reply_language]["personal"]
        except DemoModelUnavailable:
            if _EMOTIONAL_RE.search(text):
                reply = safe_fallback(
                    reply_language,
                    mode="emotional",
                    prefer_latin_script=False,
                )
            elif _CLINICIAN_RE.search(text):
                reply = safe_fallback(
                    reply_language,
                    mode="clinician_prep",
                    prefer_latin_script=False,
                )
            else:
                reply = _DEMO_COPY[reply_language]["general"]

    return {
        "reply": reply,
        "conversation_id": "demo-governed",
        "is_emergency": False,
        "reply_language": reply_language,
    }
