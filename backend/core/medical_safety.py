"""
Central medical safety policy for patient-visible AI output.
"""
from __future__ import annotations

import re

from django.conf import settings

_FORBIDDEN_PATTERNS = [
    re.compile(r"\baugment(?:e|ez|er)?\b.{0,40}\b(?:dose|insuline|traitement)\b", re.IGNORECASE),
    re.compile(r"\bdiminu(?:e|ez|er)?\b.{0,40}\b(?:dose|insuline|traitement)\b", re.IGNORECASE),
    re.compile(r"\barr[eê]t(?:e|ez|er)?\b.{0,40}\b(?:traitement|insuline|m[ée]dicament)\b", re.IGNORECASE),
    re.compile(r"\bprends?\b.{0,20}\b\d+\s*(?:u|unit[ée]s?)\b", re.IGNORECASE),
    re.compile(r"\bbolus\b", re.IGNORECASE),
    re.compile(r"\binsuline rapide\b", re.IGNORECASE),
    re.compile(r"\btu as s[uû]rement\b", re.IGNORECASE),
    re.compile(r"\bvous avez s[uû]rement\b", re.IGNORECASE),
    re.compile(r"\bpas besoin de m[ée]decin\b", re.IGNORECASE),
    re.compile(r"\bgu[ée]rir\b", re.IGNORECASE),
]


def medical_pilot_mode_enabled() -> bool:
    return bool(getattr(settings, "MEDICAL_PILOT_MODE", False))


def medical_streaming_enabled() -> bool:
    return bool(getattr(settings, "LLM_MEDICAL_STREAMING", False))


def insulin_advice_allowed() -> bool:
    return bool(getattr(settings, "ALLOW_INSULIN_ADVICE", False))


def diagnosis_allowed() -> bool:
    return bool(getattr(settings, "ALLOW_DIAGNOSIS", False))


def no_prescription_message(language: str = "fr") -> str:
    if language == "ar-MA":
        return (
            "Ma nqderch nbadel lik traitement, n3ti dosage dial insuline, "
            "wla n9ol tashkhis. Nqder n3awnk tfham l-ma3loumat dyalk "
            "w t7dder as2ila l-tabib."
        )
    return (
        "Je ne peux pas prescrire, modifier une dose d'insuline, arreter un traitement, "
        "ou poser un diagnostic. Je peux t'aider a organiser tes observations "
        "et preparer les bonnes questions pour ton medecin."
    )


def violates_no_prescription_policy(text: str) -> bool:
    if not text:
        return False

    for pattern in _FORBIDDEN_PATTERNS:
        if pattern.search(text):
            return True
    return False


def apply_no_prescription_policy(text: str, language: str = "fr") -> str:
    if not text:
        return text
    if violates_no_prescription_policy(text):
        return no_prescription_message(language)
    return text


# ── Input-side insulin prescription request detection ──────────────────────
# Blocks user INPUT asking for insulin doses/prescriptions before it reaches the LLM.
# Educational questions (what is insulin, how to store it) must NOT be blocked.

_INSULIN_INPUT_PATTERNS = [
    # French — dose/prescription questions
    re.compile(r"\bcombien\b.{0,30}\b(?:d['']|d')?unit[ée]s?\b.{0,20}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bcombien\b.{0,30}\binsul(?:ine|in)\b.{0,20}\b(?:d['']|d')?unit[ée]s?\b", re.IGNORECASE),
    re.compile(r"\bcombien\b.{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\b(?:dose|dosage)\b.{0,20}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\binsul(?:ine|in)\b.{0,20}\b(?:dose|dosage)\b", re.IGNORECASE),
    re.compile(r"\bprends?\b.{0,20}\b\d+\s*(?:u|unit[ée]s?)\b", re.IGNORECASE),
    re.compile(r"\bprends?\b.{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bprendre\b.{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bje\s+dois\b.{0,30}\bprendre\b.{0,20}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bje\s+dois\b.{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bcombien\b.{0,20}\bprendre\b.{0,20}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bbolus\b.{0,20}\b(?:quantit[ée]|montant|volume|combien)\b", re.IGNORECASE),
    re.compile(r"\bquantit[ée]\b.{0,20}\bbolus\b", re.IGNORECASE),
    # French — adjustment questions
    re.compile(r"\b(?:augment|diminu|chang|adjust|modifi|adapt)[^\n]{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\binsul(?:ine|in)\b.{0,30}\b(?:augment|diminu|chang|adjust|modifi|adapt)\b", re.IGNORECASE),
    # Darija (Latin script)
    re.compile(r"\bchhal\b.{0,20}\b(?:nakhod|nakhud|nqder|n9der|neds|nedi|nadi)\b.{0,20}\binsulin(?:e)?\b", re.IGNORECASE),
    re.compile(r"\bchhal\b.{0,20}\binsulin(?:e)?\b", re.IGNORECASE),
    re.compile(r"\binsulin(?:e)?\b.{0,20}\bchhal\b", re.IGNORECASE),
    re.compile(r"\binsulin(?:e)?\b.{0,20}\b(?:dose|jra3a|jra3a)\b", re.IGNORECASE),
    # Arabic script
    re.compile(r"كم\s+وحدة\s+أنسولين"),
    re.compile(r"كم\s+وحدة\s+انسولين"),
    re.compile(r"جرعة\s+الأنسولين"),
    re.compile(r"جرعة\s+انسولين"),
    re.compile(r"كم\s+أنسولين"),
    re.compile(r"كم\s+انسولين"),
]


def is_insulin_prescription_request(text: str | None) -> bool:
    """Return True if user input is asking for an insulin dose, amount, or prescription.

    Returns False for educational / informational questions about insulin
    (what is it, how to store it, side effects, etc.).
    """
    if not text:
        return False
    for pattern in _INSULIN_INPUT_PATTERNS:
        if pattern.search(text):
            return True
    return False
