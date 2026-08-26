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
    "salam",
    "سلام",
    "السلام عليكم",
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
    },
    "en": {
        "greeting": "Hello 👋 I'm here. How can I help?",
        "thanks": "You're welcome 🙏",
        "farewell": "See you soon 👋",
    },
    "ar": {
        "greeting": "مرحباً 👋 أنا هنا. كيف يمكنني مساعدتك؟",
        "thanks": "بكل سرور 🙏",
        "farewell": "إلى اللقاء 👋",
    },
    "ar-MA": {
        "greeting": "سلام 👋 أنا هنا معاك.",
        "thanks": "مرحبا 🙏",
        "farewell": "بالسلامة 👋",
    },
}

_FR_HELP_RE = re.compile(
    r"\b(?:aide-moi|aide moi|aidez-moi|aidez moi)\b",
    re.IGNORECASE,
)
_FR_PREP_RE = re.compile(r"\bpr[ée]parer\b", re.IGNORECASE)
_FR_CLINICIAN_RE = re.compile(r"\b(?:m[ée]decin|docteur)\b", re.IGNORECASE)
_FR_ASK_RE = re.compile(r"\b(?:demander|questions?)\b", re.IGNORECASE)
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
            and _FR_PREP_RE.search(normalized)
            and _FR_CLINICIAN_RE.search(normalized)
            and _FR_ASK_RE.search(normalized)
        ):
            return safe_fallback("fr", mode="clinician_prep")
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
    else:
        return _exact_practical_reply(normalized, language)

    locale = language if language in _REPLIES else "fr"
    return _REPLIES[locale][intent]
