"""
Medical-advice disclaimer filter.
===================================
Deterministic post-processor — runs after LLM reply generation.
Ensures "consult your doctor" disclaimers are not repeated more than
once per 24h sliding window per patient.

Design: detect → decide (keep / suppress) → stamp ONLY if kept.
Never stamp on suppression (would push the window forward and
silently suffocate the next legitimate disclaimer).

Pattern set aligned with prompts.py LANGUAGE_LABELS vocabulary so the
detector covers exactly what the LLM was taught to produce.
"""
import re

# ── Pattern set ──────────────────────────────────────────────────────────────
# Sources: prompts.py LANGUAGE_LABELS + few-shot examples in CHAT_USER / REACTION_USER.
# Case-insensitive, punctuation-tolerant.

_PATTERNS_FR = [
    r"consult[ez]?\s+(ton|votre|un)\s+médecin",
    r"parle[sz]?\s*(-\s*)?en\s+à\s+(ton|votre)\s+médecin",
    r"contacter?\s+(ton|votre|un)\s+(médecin|docteur|soignant)",
    r"voir?\s+un?\s+(médecin|docteur|professionnel de santé)",
    r"ton\s+équipe\s+soignante",
    r"avis\s+médical",
    r"professionnel\s+de\s+santé",
]

_PATTERNS_DARIJA_ARABIC = [
    r"شوف\s+الطبيب",
    r"تواصل\s+مع\s+الطبيب",
    r"راجع\s+الطبيب",
    r"روح\s+للطبيب",
    r"الطبيب\s+ديالك",
    r"استشر\s+الطبيب",
    r"كلم\s+الطبيب",
]

_PATTERNS_MSA = [
    r"(استشر|تستشر|يستشر)\s+طبيبك",  # imperative + indicative conjugations
    r"راجع\s+طبيبك",
    r"تحدث\s+مع\s+طبيبك",
    r"يجب\s+عليك\s+زيارة\s+الطبيب",
    r"فريق\s+الرعاية\s+الصحية",
]

_ALL_PATTERNS = [
    re.compile(p, re.IGNORECASE | re.UNICODE)
    for p in _PATTERNS_FR + _PATTERNS_DARIJA_ARABIC + _PATTERNS_MSA
]

# Sentence splitter — handles Arabic + Latin scripts.
# Splits on [.!?؟।\n] followed by whitespace or end-of-string.
_SENTENCE_RE = re.compile(r'(?<=[.!?؟\n])\s+')


def contains_medical_advice(reply: str) -> bool:
    """Return True if reply contains a medical-advice disclaimer."""
    for pattern in _ALL_PATTERNS:
        if pattern.search(reply):
            return True
    return False


def strip_medical_advice(reply: str) -> str:
    """
    Remove sentences containing a medical-advice disclaimer.
    Rejoins remaining sentences cleanly.
    Returns empty string if nothing survives (caller must handle this case).
    """
    sentences = _SENTENCE_RE.split(reply.strip())
    kept = [s for s in sentences if s.strip() and not contains_medical_advice(s)]
    if not kept:
        return ""  # caller decides what to do with an unsuppressible disclaimer
    result = " ".join(kept).strip()
    # Ensure terminal punctuation is preserved
    if reply.rstrip() and reply.rstrip()[-1] in ".!?؟" and result and result[-1] not in ".!?؟":
        result += "."
    return result


def apply_advice_throttle(reply: str, deep) -> str:
    """
    Main entry point — call after every LLM reply before returning to patient.

    Rules (order is mandatory):
      1. No disclaimer detected → return reply unchanged, no stamp.
      2. Disclaimer detected + outside 24h window → keep reply, stamp now.
      3. Disclaimer detected + inside 24h window → strip disclaimer, do NOT stamp.
         If stripping leaves an empty result (e.g. ، clause without sentence break),
         return the original rather than an empty response — never stamp in this case.

    deep must expose: advice_given_within(hours) and record_advice_given().
    """
    if not contains_medical_advice(reply):
        return reply

    if not deep.advice_given_within(24):
        # First disclaimer in this window — keep it and stamp
        deep.record_advice_given()
        return reply

    # Repeat within 24h — suppress surgically, never re-stamp
    stripped = strip_medical_advice(reply)
    if not stripped.strip():
        # Suppression would leave empty response (e.g. Darija clause joined by ،).
        # Return original — disclaimer shows, timestamp unchanged (no re-stamp).
        return reply
    return stripped
