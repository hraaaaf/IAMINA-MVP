"""Deterministic filter for invented practical content and known bad live-parity phrasing.

This layer fails closed on exact phrases observed in retained synthetic parity.
It does not interpret clinical data and never adds health actions, schedules,
reminders, or treatment content.
"""
from __future__ import annotations

import re

_KUWAITI_INVENTED_TRACKING_CONTENT = re.compile(
    r"ملاحظاتك\s+أو\s+توقيت\s+المتابعة",
    re.IGNORECASE,
)
_OMANI_INVENTED_MEMORY_TRIGGER = re.compile(
    r"وقت\s+ما\s+تحس[ّ]?\s+إنك\s+تذك[ّ]?رت",
    re.IGNORECASE,
)
_DARIJA_INVENTED_CHOSEN_CONTENT = re.compile(
    r"اخترت\s+هاد\s+الشي",
    re.IGNORECASE,
)
_DARIJA_BAD_DINNER_PHRASING = re.compile(
    r"كتفطر\s+العشا",
    re.IGNORECASE,
)
_EMIRATI_BAD_EMPATHY = re.compile(
    r"وكلنا\s+نحتاج\s+نفك[ّ]?س\s+شوية",
    re.IGNORECASE,
)
_FRENCH_INVENTED_TRACKING_CHECKLIST = re.compile(
    r"(?:"
    r"j[’']ai\s+not[ée]\s+mon\s+suivi\s+du\s+diab[èe]te"
    r"|j[’']ai\s+v[ée]rifi[ée]\s+le\s+point\s+essentiel"
    r"|utilise[‐‑–—-]?la\s+chaque\s+soir"
    r")",
    re.IGNORECASE,
)


def sanitize_practical_boundary(reply: str) -> str:
    """Fail closed on exact live-parity inventions or malformed phrasing."""
    if _KUWAITI_INVENTED_TRACKING_CONTENT.search(reply):
        return "خلّها بسيطة حيل: ثلاث خانات فاضية بس بدون محتوى مفروض."
    if _OMANI_INVENTED_MEMORY_TRIGGER.search(reply):
        return "خلّها بسيطة واجد: ثلاث خانات فاضية بس بدون محتوى مفروض."
    if _DARIJA_INVENTED_CHOSEN_CONTENT.search(reply) or _DARIJA_BAD_DINNER_PHRASING.search(reply):
        return "خليها بسيطة: ثلاث خانات خاويين بلا محتوى مفروض، وعمر غير باللي نتا اخترت من قبل."
    if _EMIRATI_BAD_EMPATHY.search(reply):
        return "ترا هالشي متعب وايد كل يوم، وأنا وياك بهاللحظة بدون ما أزيد عليك شي."
    if _FRENCH_INVENTED_TRACKING_CHECKLIST.search(reply):
        return "Pour le soir après le dîner, garde trois cases vides, sans contenu imposé."
    return reply
