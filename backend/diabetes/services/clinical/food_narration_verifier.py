"""Deterministic verifier for narrated FOOD_DECISION output.

Clinical semantics stay inside the diabetes capsule. The core verifier remains
condition-agnostic and only decides whether observed actions fit AdviceDecision.
"""
from __future__ import annotations

import re

from core.contracts.advice_decision import AdviceDecision
from core.narration_verifier import NarrationVerification, verify_observed_actions

_ACTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "approve_food_personally",
        re.compile(
            r"(?:\b(?:oui[,\s]+)?tu\s+peux\s+(?:manger|prendre|boire)\b"
            r"|\byou\s+can\s+(?:eat|have|drink)\b"
            r"|(?:نعم.{0,12})?(?:تقدر|يمكنك)\s+(?:تاكل|تأكل|تشرب))",
            re.IGNORECASE,
        ),
    ),
    (
        "forbid_food_personally",
        re.compile(
            r"(?:\btu\s+ne\s+peux\s+pas\s+(?:manger|prendre|boire)\b"
            r"|\bne\s+(?:mange|prends|bois)\s+pas\b"
            r"|\byou\s+(?:cannot|can't|must\s+not)\s+(?:eat|have|drink)\b"
            r"|(?:لا\s+(?:تأكل|تاكل|تشرب)|ممنوع\s+عليك))",
            re.IGNORECASE,
        ),
    ),
    (
        "calculate_insulin_dose",
        re.compile(
            r"(?:\b(?:insulin(?:e)?|انسولين|أنسولين)\b.{0,48}"
            r"\b(?:dose|unit(?:s)?|unité(?:s)?|وحد(?:ة|ات))\b"
            r"|\b(?:dose|unit(?:s)?|unité(?:s)?|وحد(?:ة|ات))\b.{0,48}"
            r"\b(?:insulin(?:e)?|انسولين|أنسولين)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "change_treatment",
        re.compile(
            r"\b(?:change|changez|modifie|modifiez|arrête|arrêtez|stop|increase|"
            r"decrease|augmente|augmentez|diminue|diminuez)\b.{0,48}"
            r"\b(?:ton|votre|your)\s+(?:traitement|treatment|insulin(?:e)?|"
            r"médicament|medication)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "compensate_food_with_activity",
        re.compile(
            r"(?:\b(?:marche|marcher|activité|sport|exercise|walk)\b.{0,64}"
            r"\b(?:compens\w*|offset|brûl\w*|burn\w*|après|after)\b"
            r"|\b(?:compens\w*|offset|brûl\w*|burn\w*)\b.{0,64}"
            r"\b(?:marche|activité|sport|exercise|walk)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "infer_patient_specific_causality",
        re.compile(
            r"(?:\b(?:because|parce\s+que|car)\b.{0,64}"
            r"\b(?:glyc(?:é|e)mie|glucose)\b"
            r"|(?:بسبب).{0,64}(?:سكر|جلوكوز))",
            re.IGNORECASE,
        ),
    ),
    (
        "introduce_unapproved_threshold",
        re.compile(
            r"(?:[<>]=?\s*\d+\s*(?:g)?"
            r"|\b(?:plus|moins)\s+de\s+\d+\s*(?:g)?"
            r"|\b(?:more|less)\s+than\s+\d+\s*(?:g)?)"
            r"\s*(?:de\s+)?(?:glucides?|carbs?|carbohydrates?)",
            re.IGNORECASE,
        ),
    ),
    (
        "review_portion_and_carbohydrate_context",
        re.compile(
            r"(?:\bportion\b.{0,48}\b(?:glucides?|carbs?|carbohydrates?)\b"
            r"|\b(?:glucides?|carbs?|carbohydrates?)\b.{0,48}\bportion\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "request_food_label_or_portion",
        re.compile(
            r"(?:\b(?:donne-moi|envoie|partage|share|send|3tini)\b.{0,64}"
            r"\b(?:portion|étiquette|etiquette|label)\b"
            r"|(?:أرسل|عطيني).{0,64}(?:الكمية|الملصق|لابيتيكيت))",
            re.IGNORECASE,
        ),
    ),
    (
        "interpret_declared_portion_and_carbohydrate_information",
        re.compile(
            r"(?:\b(?:interprét\w*|interpret\w*|aider|help)\b.{0,64}"
            r"\b(?:portion|glucides?|carbs?|carbohydrates?)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "compare_food_options_by_portion_and_carbohydrate",
        re.compile(
            r"(?:\b(?:compare|comparer|n9aren)\b"
            r"|(?:أقارن|اقارن|مقارنة))",
            re.IGNORECASE,
        ),
    ),
)


def observe_food_narration_actions(text: str) -> tuple[str, ...]:
    if not isinstance(text, str) or not text.strip():
        return ("malformed_narration",)

    observed: list[str] = []
    for action, pattern in _ACTION_PATTERNS:
        if pattern.search(text) and action not in observed:
            observed.append(action)
    return tuple(observed)


def verify_food_narration(
    decision: AdviceDecision,
    text: str,
) -> NarrationVerification:
    if not decision.rule_id.startswith("diabetes.food."):
        return verify_observed_actions(decision, ("wrong_rule_family",))
    return verify_observed_actions(decision, observe_food_narration_actions(text))


def verified_food_narration_or_fallback(
    decision: AdviceDecision,
    candidate: str,
    fallback: str,
) -> str:
    candidate_check = verify_food_narration(decision, candidate)
    if candidate_check.passed:
        return candidate

    fallback_check = verify_food_narration(decision, fallback)
    if not fallback_check.passed:
        raise PermissionError(
            "deterministic FOOD fallback failed narration verification: "
            + ", ".join(fallback_check.violations)
        )
    return fallback


__all__ = [
    "observe_food_narration_actions",
    "verified_food_narration_or_fallback",
    "verify_food_narration",
]
