"""Deterministic filter for invented practical tracking content.

This layer removes only concrete practical content or memory triggers that the
user did not choose. It does not interpret clinical data and never adds health
actions, schedules, reminders, or treatment content.
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


def sanitize_practical_boundary(reply: str) -> str:
    """Fail closed on exact live-parity practical inventions."""
    if _KUWAITI_INVENTED_TRACKING_CONTENT.search(reply):
        return "خلّها بسيطة حيل: ثلاث خانات فاضية بس بدون محتوى مفروض."
    if _OMANI_INVENTED_MEMORY_TRIGGER.search(reply):
        return "خلّها بسيطة واجد: ثلاث خانات فاضية بس بدون محتوى مفروض."
    return reply
