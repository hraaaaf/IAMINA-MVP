"""Fail-closed zero-model routing for exact non-clinical companion turns.

Only whole-message greetings and thanks are eligible. Any extra token, number,
clinical wording or ambiguity returns ``None`` and keeps the governed LLM path.
"""

import re

_TRAILING_PUNCTUATION = re.compile(r"[\s.!?…،؛:]+$")
_INTERNAL_SPACE = re.compile(r"\s+")

_GREETING = {
    "bonjour",
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

_REPLIES = {
    "fr": {
        "greeting": "Bonjour 👋 Je suis là. Que puis-je faire pour toi ?",
        "thanks": "Avec plaisir 🙏",
    },
    "en": {
        "greeting": "Hello 👋 I'm here. How can I help?",
        "thanks": "You're welcome 🙏",
    },
    "ar": {
        "greeting": "مرحباً 👋 أنا هنا. كيف يمكنني مساعدتك؟",
        "thanks": "بكل سرور 🙏",
    },
    "ar-MA": {
        "greeting": "سلام 👋 أنا هنا معاك.",
        "thanks": "مرحبا 🙏",
    },
}


def _normalize(message: str) -> str:
    normalized = _INTERNAL_SPACE.sub(" ", message.strip().casefold())
    return _TRAILING_PUNCTUATION.sub("", normalized)


def exact_chitchat_reply(message: str, language: str) -> str | None:
    """Return a zero-model reply only for an exact allow-listed whole message."""
    normalized = _normalize(message)
    if not normalized:
        return None

    if normalized in _GREETING:
        intent = "greeting"
    elif normalized in _THANKS:
        intent = "thanks"
    else:
        return None

    locale = language if language in _REPLIES else "fr"
    return _REPLIES[locale][intent]
