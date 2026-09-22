"""Deterministic verifier for ACTIVITY_CONTEXT narration."""
from __future__ import annotations

import re

from core.contracts.advice_decision import AdviceDecision
from core.narration_verifier import NarrationVerification, verify_observed_actions

_ACTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("calculate_insulin_dose", re.compile(
        r"(?:\b\d+(?:[.,]\d+)?\s*(?:u|unit(?:s)?|unité(?:s)?|وحد(?:ة|ات))\b"
        r"|\b(?:insulin(?:e)?|أنسولين|انسولين)\b.{0,48}"
        r"\b(?:dose|unit(?:s)?|unité(?:s)?|وحد(?:ة|ات))\b)", re.IGNORECASE)),
    ("change_treatment", re.compile(
        r"\b(?:change|modifie|arrête|stop|increase|decrease|reduce|réduis|augmente|diminue)\b"
        r".{0,56}\b(?:traitement|treatment|insulin(?:e)?|médicament|medication|dose)\b",
        re.IGNORECASE)),
    ("recommend_compensatory_activity", re.compile(
        r"\b(?:marche|marcher|walk|exercise|exercice|sport|activité)\b.{0,72}"
        r"\b(?:faire\s+baisser|lower|corriger|correct|compens\w*)\b", re.IGNORECASE)),
    ("prescribe_exercise", re.compile(
        r"\b(?:tu\s+dois|vous\s+devez|you\s+should|fais|faites|do)\b.{0,40}"
        r"\b(?:marche|marcher|walk|exercise|exercice|sport|activité)\b", re.IGNORECASE)),
    ("diagnose_from_activity", re.compile(
        r"\b(?:sport|exercise|exercice|activité)\b.{0,64}"
        r"\b(?:prouve|prove|confirme|confirm)\b.{0,48}"
        r"\b(?:hypoglycémie|hypoglycemia|diabète|diabetes)\b", re.IGNORECASE)),
)


_CAUSALITY_RE = re.compile(
    r"\b(?:sport|exercise|exercice|activité|marche)\b.{0,72}"
    r"\b(?:cause|causes|causé|provoque|responsable|explains?|explique)\b"
    r"|\b(?:cause|causes|causé|provoque)\b.{0,72}"
    r"\b(?:glyc[eé]mi(?:e|que)|glucose|sucre|hypo|baisse)\b",
    re.IGNORECASE,
)
_CAUSALITY_NEGATION_RE = re.compile(
    r"(?:ne\s+(?:prouve|démontre)\s+pas|does\s+not\s+(?:prove|establish)|"
    r"doesn't\s+(?:prove|establish)|لا\s+يثبت)",
    re.IGNORECASE,
)


def _claims_activity_causality(text: str) -> bool:
    for sentence in re.split(r"[.!?\n]+", text):
        if _CAUSALITY_RE.search(sentence) and not _CAUSALITY_NEGATION_RE.search(sentence):
            return True
    return False


def observe_activity_narration_actions(text: str) -> tuple[str, ...]:
    if not isinstance(text, str) or not text.strip():
        return ("malformed_narration",)
    observed: list[str] = []
    for action, pattern in _ACTION_PATTERNS:
        if pattern.search(text) and action not in observed:
            observed.append(action)
    if _claims_activity_causality(text):
        observed.append("infer_activity_causality")
    return tuple(observed)


def verify_activity_narration(decision: AdviceDecision, text: str) -> NarrationVerification:
    if not decision.rule_id.startswith("diabetes.activity."):
        return verify_observed_actions(decision, ("wrong_rule_family",))
    return verify_observed_actions(decision, observe_activity_narration_actions(text))


def verified_activity_narration_or_fallback(
    decision: AdviceDecision, candidate: str, fallback: str
) -> str:
    candidate_check = verify_activity_narration(decision, candidate)
    if candidate_check.passed:
        return candidate
    fallback_check = verify_activity_narration(decision, fallback)
    if not fallback_check.passed:
        raise PermissionError(
            "deterministic ACTIVITY fallback failed narration verification: "
            + ", ".join(fallback_check.violations)
        )
    return fallback


__all__ = [
    "observe_activity_narration_actions",
    "verified_activity_narration_or_fallback",
    "verify_activity_narration",
]
