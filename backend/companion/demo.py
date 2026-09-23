"""Stateless governed conversation for public demo mode.

The demo endpoint shares IAMINA's deterministic safety authority without creating
a patient identity, reading clinical data or persisting turns. Ordinary free-form
demo turns may use the dedicated bounded external narrator when explicitly enabled.
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
from diabetes.services.clinical.clinical_validation import enforce_clinical_validation
from diabetes.services.clinical.food_decision import resolve_reported_food_context

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
_FOOD_PERMISSION_RE = re.compile(
    r"(?:"
    r"\b(?:est[- ]?ce que\s+)?(?:je|j['’])\s+peux\s+manger\b"
    r"|\bcan\s+i\s+(?:eat|have)\b"
    r"|\b(?:wach\s+)?n9dar\s+nakol\b"
    r"|(?:هل\s+)?(?:أقدر|اقدر|ممكن)\s+آكل"
    r")",
    re.IGNORECASE,
)
_LATIN_DARIJA_FOOD_RE = re.compile(
    r"\b(?:wach\s+)?n9dar\s+nakol\b",
    re.IGNORECASE,
)
_FOOD_REPORT_PROMPT_RE = re.compile(
    r"(?:"
    r"qu['’]est[- ]?ce que tu as mang[ée]|qu['’]as[- ]?tu mang[ée]|tu as mang[ée] quoi"
    r"|what did you eat|what have you eaten"
    r"|chno kliti|ach kliti"
    r"|شنو كليتي|شنو كلّيتي|ماذا أكلت|شو أكلت"
    r")",
    re.IGNORECASE,
)


def _history_invites_food_report(history: list[dict[str, str]]) -> bool:
    """True only when the latest assistant turn explicitly asks what was eaten."""
    for turn in reversed(history):
        role = str(turn.get("role", "")).strip()
        content = str(turn.get("content", "")).strip()
        if role == "assistant":
            return bool(_FOOD_REPORT_PROMPT_RE.search(content))
        if role == "user":
            continue
        break
    return False


def _food_permission_reply(text: str, reply_language: str) -> str:
    if (
        (_LATIN_DARIJA_FOOD_RE.search(text) or _LATIN_DARIJA_RE.search(text))
        and not _ARABIC_RE.search(text)
    ):
        return (
            "Ma n9drch ngolik yes/no b tari9a chakhssiya 3la chi makla. "
            "N9dro nchofo lportion w lcarbs, w ila bghiti n3awnk tqra l'étiquette "
            "wla twjjed sou2al ltbib."
        )
    if reply_language == "en":
        return (
            "I can’t give a personalized yes/no approval for a food. "
            "For a dessert or meal, the useful things to look at are the portion "
            "and carbohydrate content. If you want, I can help you read the label "
            "or prepare a question for your care team."
        )
    if reply_language == "ar":
        return (
            "ما أقدر أعطيك موافقة شخصية بنعم أو لا على طعام معيّن. "
            "الأفضل ننظر إلى الكمية ومحتوى الكربوهيدرات، وإذا تحب أساعدك "
            "تقرأ الملصق الغذائي أو تجهّز سؤالًا لفريقك الصحي."
        )
    if reply_language == "ar-MA":
        return (
            "ما نقدرش نعطيك جواب شخصي بنعم ولا لا على شي ماكلة. "
            "نقدرو غير نشوفو الكمية والكربوهيدرات، وإذا بغيتي نعاونك "
            "تقرا لابيتيكيت ولا توجد سؤال للطبيب."
        )
    return (
        "Je ne peux pas te donner un feu vert/rouge personnalisé pour un aliment. "
        "Pour un dessert ou un repas, le plus utile est de regarder la portion et "
        "la teneur en glucides. Si tu veux, je peux t’aider à lire l’étiquette ou "
        "à préparer une question pour ton soignant."
    )
_CASUAL_CHAT_RE = re.compile(
    r"(?:just keep me company|just talk|keep it casual|don't turn it into advice|"
    r"pas besoin d['’]un plan|juste discuter|parle-moi normalement|"
    r"ghir (?:nhder|hdar|n9ssr)|ma bghit ta chi 7al|ma bghitch conseils|"
    r"ما أبي حلول|ما أبغى نصائح|بدون حلول|بدون نصائح|بلا نصائح|"
    r"بغيت غير نهضر|بس ودي أسولف|بس أسولف|بس كلمني)",
    re.IGNORECASE,
)
_LATIN_DARIJA_RE = re.compile(
    r"(?:salam|lyouma|bghit|bghitch|ghir|nhder|hdar|n9ssr|m3ak|chwia|hakka|khlli)",
    re.IGNORECASE,
)
_GULF_RE = re.compile(r"(?:هلا|أبغى|أبي|ودي|الحين|أسولف|سوالف|خلك|شوي)")


def _history_is_casual(history: list[dict[str, str]]) -> bool:
    return any(
        turn.get("role") == "user"
        and _CASUAL_CHAT_RE.search(str(turn.get("content", "")))
        for turn in history
    )


def _casual_fallback(
    text: str,
    reply_language: str,
    history: list[dict[str, str]],
) -> str:
    continuation = bool(history)
    if reply_language == "en":
        return (
            "Sure — we can just keep it light. What’s on your mind now?"
            if continuation
            else "Sure — no fixing, no advice. We can just chat for a bit."
        )
    if reply_language == "ar":
        if _GULF_RE.search(text):
            return (
                "أكيد، نخليها سوالف خفيفة وبس. وش على بالك الحين؟"
                if continuation
                else "تمام، نخليها سوالف خفيفة وبس. وش ودك تسولف عنه؟"
            )
        return (
            "أكيد، نخليها دردشة خفيفة فقط. ما الذي يدور في بالك الآن؟"
            if continuation
            else "تمام، نتحدث ببساطة ومن دون نصائح."
        )
    if reply_language == "ar-MA":
        return (
            "واخا، نخليوها غير هدرة خفيفة. شنو جا فبالك دابا؟"
            if continuation
            else "واخا، غير نهضرو بشوية وعلى راحتك."
        )
    if _LATIN_DARIJA_RE.search(text) and not _ARABIC_RE.search(text):
        return (
            "Wakha, nkhelliwha ghir hdra khfifa. Chno jay f balk daba?"
            if continuation
            else "Wakha, ghir nhdro chwia b rahatk."
        )
    return (
        "D’accord, on reste léger et on discute tranquillement. Qu’est-ce qui te passe par la tête ?"
        if continuation
        else "D’accord, pas de plan ni de conseils. On peut juste discuter tranquillement."
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


def reply_to_demo_message(
    message: str,
    language: str = "fr",
    history: list[dict[str, str]] | None = None,
) -> dict:
    """Return one stateless governed demo turn.

    No patient object, ORM lookup or durable conversation persistence is permitted.
    Optional history is request-scoped and bounded by the demo model gate.
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

    if _FOOD_PERMISSION_RE.search(text):
        return {
            "reply": _food_permission_reply(text, reply_language),
            "conversation_id": "demo-governed",
            "is_emergency": False,
            "reply_language": reply_language,
        }

    if _history_invites_food_report(history or []):
        resolution = resolve_reported_food_context(
            text,
            language=reply_language,
        )
        resolution = enforce_clinical_validation(resolution)
        return {
            "reply": resolution.reply,
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
            reply = generate_demo_reply(
                text,
                reply_language,
                history=history or [],
            )
        except DemoPayloadDenied:
            reply = _DEMO_COPY[reply_language]["personal"]
        except DemoModelUnavailable:
            bounded_history = history or []
            if _CASUAL_CHAT_RE.search(text) or _history_is_casual(bounded_history):
                reply = _casual_fallback(text, reply_language, bounded_history)
            elif _EMOTIONAL_RE.search(text):
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
