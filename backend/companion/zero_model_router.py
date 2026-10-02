"""Fail-closed zero-model routing for bounded companion turns.

Exact chitchat plus a tiny allow-list of abstract organization requests can
bypass the LLM. Safety still runs before this router in ``conversation.py``;
anything ambiguous stays on the governed LLM path.
"""

import re

from companion.output_guard import safe_fallback

_TRAILING_PUNCTUATION = re.compile(r"[\s.!?…،؛:]+$")
_INTERNAL_SPACE = re.compile(r"\s+")

_GREETING = {
    "salut",
    "hello",
    "hi",
    "hi ca va",
    "hi ça va",
    "ca va",
    "ça va",
    "comment ça va",
    "comment ca va",
    "how are you",
    "salam",
    "salam ca va",
    "salam ça va",
    "salam cava",
    "salam labas",
    "سلام",
    "السلام عليكم",
}
_IDENTITY = {
    "qui es-tu",
    "qui es tu",
    "tu es qui",
    "t'es qui",
    "who are you",
    "chkoun nta",
    "chkon nta",
    "chkoune nta",
    "شكون نتا",
}
_CAPABILITIES = {
    "tu sais faire quoi",
    "tu peux faire quoi",
    "qu'est-ce que tu sais faire",
    "qu'est ce que tu sais faire",
    "what can you do",
    "chno kat9der dir",
    "ach kat9der dir",
    "شنو كتقدر دير",
}
_HISTORY_ACCESS = {
    "t'as accès a mon historique",
    "t'as accès à mon historique",
    "tu as accès a mon historique",
    "tu as accès à mon historique",
    "as-tu accès a mon historique",
    "as-tu accès à mon historique",
    "do you have access to my history",
    "wach 3ndk acces lhistorique dyali",
    "wach 3ndk accès lhistorique dyali",
    "واش عندك الولوج للتاريخ ديالي",
}
_CONFUSION = {
    "malek chkouen sweltek",
    "malek chkoun swlk",
    "malek chkon swlk",
    "malk chkouen sweltek",
    "malk chkoun swlk",
    "qui t'a demandé ça",
    "qui t'a demande ca",
    "je t'ai pas demandé ça",
    "je t ai pas demandé ça",
}
_THANKS = {
    "merci",
    "merci beaucoup",
    "thanks",
    "thank you",
    "chokran",
    "شكرا",
    "شكراً",
}
_FAREWELLS = {
    "au revoir",
    "goodbye",
    "bslama",
    "مع السلامة",
}

_REPLIES = {
    "fr": {
        "greeting": "Bonjour 👋 Je suis là. Que puis-je faire pour toi ?",
        "thanks": "Avec plaisir 🙏",
        "farewell": "À bientôt 👋",
        "identity": (
            "Je suis IAmina, ton compagnon de suivi. "
            "Je réponds à partir des données enregistrées dans IAMINA sans inventer ce qui manque."
        ),
        "capabilities": (
            "Je peux retrouver tes données enregistrées dans IAMINA — glycémie, repas, sommeil, "
            "stress, traitement enregistré, CGM et documents/labs — puis les résumer ou répondre "
            "à une question précise. Je ne modifie pas ton traitement et je n'invente pas les données manquantes."
        ),
        "history": (
            "Oui pour l'historique récent de cette conversation. Pour les données IAMINA, "
            "je n'utilise que celles qui sont effectivement enregistrées et accessibles dans l'app."
        ),
        "confusion": (
            "Tu as raison, ma réponse précédente était hors sujet. "
            "Dis-moi simplement ce que tu veux savoir."
        ),
    },
    "en": {
        "greeting": "Hello 👋 I'm here. What would you like to know?",
        "thanks": "You're welcome 🙏",
        "farewell": "See you soon 👋",
        "identity": (
            "I'm IAmina, your tracking companion. "
            "I answer from data recorded in IAmina and do not invent missing information."
        ),
        "capabilities": (
            "I can retrieve data recorded in IAmina — glucose, meals, sleep, stress, recorded treatment, "
            "CGM and documents/labs — then summarize it or answer a specific question. "
            "I do not change treatment or invent missing data."
        ),
        "history": (
            "Yes for the recent history of this conversation. For IAmina data, "
            "I only use information that is actually recorded and available in the app."
        ),
        "confusion": "You're right, my previous reply was off-topic. Tell me what you want to know.",
    },
    "ar": {
        "greeting": "مرحباً 👋 أنا هنا. ماذا تريد أن تعرف؟",
        "thanks": "بكل سرور 🙏",
        "farewell": "إلى اللقاء 👋",
        "identity": "أنا IAmina، رفيق متابعة يعتمد على البيانات المسجلة في IAmina ولا يختلق معلومات غير موجودة.",
        "capabilities": (
            "أستطيع الرجوع إلى البيانات المسجلة في IAmina مثل سكر الدم والوجبات والنوم والتوتر والعلاج المسجل "
            "وبيانات CGM والوثائق/التحاليل، ثم تلخيصها أو الإجابة عن سؤال محدد. لا أغيّر العلاج ولا أختلق بيانات."
        ),
        "history": (
            "نعم بالنسبة للسياق الحديث لهذه المحادثة. وبالنسبة لبيانات IAmina، "
            "لا أستخدم إلا المعلومات المسجلة والمتاحة فعلاً داخل التطبيق."
        ),
        "confusion": "معك حق، ردي السابق كان خارج الموضوع. قل لي ببساطة ماذا تريد أن تعرف.",
    },
    "ar-MA": {
        "greeting": "سلام 👋 أنا هنا معاك. شنو بغيتي تعرف؟",
        "thanks": "مرحبا 🙏",
        "farewell": "بالسلامة 👋",
        "identity": "أنا IAmina، كنعاونك فالمتابعة اعتماداً على الداتا المسجلة فـ IAmina وبلا ما نخترع شي معلومة ناقصة.",
        "capabilities": (
            "نقدر نقلب فالداتا المسجلة فـ IAmina بحال السكر، الماكلة، النعاس، الستريس، العلاج المسجل، CGM والوثائق/التحاليل، "
            "ونلخصها ولا نجاوبك على سؤال محدد. ما كنبدلش العلاج وما كنخترعش الداتا الناقصة."
        ),
        "history": (
            "إييه بالنسبة للسياق القريب ديال هاد المحادثة. وبالنسبة لداتا IAmina، "
            "كنستعمل غير المعلومات اللي مسجلة ومتاحة فعلاً فالتطبيق."
        ),
        "confusion": "عندك الحق، الجواب اللي فات كان خارج الموضوع. قول ليا غير شنو بغيتي تعرف.",
    },
    "ar-MA-latn": {
        "greeting": "Salam 👋 ana hna m3ak. Chno bghiti t3ref?",
        "thanks": "Marhba 🙏",
        "farewell": "Bslama 👋",
        "identity": (
            "Ana IAmina, kan3awnek f suivi 3la 7sab data li msjla f IAmina, "
            "bla ma nkhtare3 chi ma3louma ma kaynach."
        ),
        "capabilities": (
            "N9der nqleb f data li msjla f IAmina b7al sucre, makla, n3as, stress, traitement msjjel, "
            "CGM w documents/labs, w nlkhesha wela njawb 3la sou2al m7edded. "
            "Ma kanbeddelch traitement w ma kanzidch data ma kaynach."
        ),
        "history": (
            "Iyyeh 3la l-context l9rib dyal had lconversation. W bnisba l-data dyal IAmina, "
            "kansta3mel ghir dakchi li msjjel w disponible f l-app."
        ),
        "confusion": "3ndk l7e9, ljawab li fat kan barra mn sujet. Goul lia ghir chno bghiti t3ref.",
    },
}

_DARIJA_LATIN_HINTS = (
    "salam",
    "chokran",
    "bslama",
    "chno",
    "ach ",
    "wach ",
    "malek",
    "malk",
    "chkoun",
    "chkouen",
)


def _reply_locale(message: str, normalized: str, language: str) -> str:
    if language == "ar-MA" and not re.search(r"[\u0600-\u06ff]", message):
        return "ar-MA-latn"
    if not re.search(r"[\u0600-\u06ff]", message) and any(
        hint in normalized for hint in _DARIJA_LATIN_HINTS
    ):
        return "ar-MA-latn"
    return language if language in _REPLIES else "fr"


_FR_HELP_RE = re.compile(
    r"\b(?:aide-moi|aide moi|aidez-moi|aidez moi)\b",
    re.IGNORECASE,
)
_FR_ORGANIZE_RE = re.compile(r"\borganis(?:e|er|ation)\b", re.IGNORECASE)
_FR_ROUTINE_START_RE = re.compile(
    r"\bdu mal [àa] [êe]tre r[ée]gulier\b.*\b(?:j'oublie|oublie)\b",
    re.IGNORECASE,
)
_FR_ROUTINE_SIMPLE_RE = re.compile(
    r"\boubli[ée]\b.*\b(?:quelque chose de simple|plus simple)\b",
    re.IGNORECASE,
)


def _normalize(message: str) -> str:
    normalized = _INTERNAL_SPACE.sub(
        " ",
        message.strip().casefold().replace("’", "'"),
    )
    return _TRAILING_PUNCTUATION.sub("", normalized)


def _exact_practical_reply(normalized: str, language: str) -> str | None:
    if language == "fr":
        helper = bool(_FR_HELP_RE.search(normalized))
        if (
            helper
            and _FR_ORGANIZE_RE.search(normalized)
            and "suivi" in normalized
            and "semaine" in normalized
        ):
            return safe_fallback("fr", mode="practical", weekly=True)
        if _FR_ROUTINE_START_RE.search(normalized):
            return safe_fallback("fr", mode="practical")
        if _FR_ROUTINE_SIMPLE_RE.search(normalized):
            return safe_fallback("fr", mode="practical", very_long=True)

    if (
        language == "ar-MA"
        and "routine" in normalized
        and "sahla" in normalized
        and any(token in normalized for token in ("mntadem", "mntadam"))
        and any(
            token in normalized
            for token in ("bla nasi7a", "bla nassi7a")
        )
    ):
        return safe_fallback(
            "ar-MA",
            mode="practical",
            prefer_latin_script=True,
        )

    return None


def exact_chitchat_reply(message: str, language: str) -> str | None:
    """Return an exact bounded zero-model reply, otherwise fail closed."""
    normalized = _normalize(message)
    if not normalized:
        return None

    if normalized in _GREETING:
        intent = "greeting"
    elif normalized in _THANKS:
        intent = "thanks"
    elif normalized in _FAREWELLS:
        intent = "farewell"
    elif normalized in _IDENTITY:
        intent = "identity"
    elif normalized in _CAPABILITIES:
        intent = "capabilities"
    elif normalized in _HISTORY_ACCESS:
        intent = "history"
    elif normalized in _CONFUSION:
        intent = "confusion"
    else:
        return _exact_practical_reply(normalized, language)

    locale = _reply_locale(message, normalized, language)
    return _REPLIES[locale][intent]
