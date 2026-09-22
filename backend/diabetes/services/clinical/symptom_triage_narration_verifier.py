"""Deterministic verifier for SYMPTOM_TRIAGE narration."""
from __future__ import annotations

import re

from core.contracts.advice_decision import AdviceDecision
from core.narration_verifier import NarrationVerification, verify_observed_actions

_ACTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "calculate_insulin_dose",
        re.compile(
            r"(?:\b\d+(?:[.,]\d+)?\s*(?:u|unit(?:s)?|unité(?:s)?|وحد(?:ة|ات))\b"
            r"|\b(?:insulin(?:e)?|أنسولين|انسولين)\b.{0,48}"
            r"\b(?:dose|unit(?:s)?|unité(?:s)?|وحد(?:ة|ات))\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "change_treatment",
        re.compile(
            r"\b(?:change|modifie|arrête|stop|increase|decrease|reduce|réduis|augmente|diminue)\b"
            r".{0,56}\b(?:traitement|treatment|insulin(?:e)?|médicament|medication|dose)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reassure_symptom_is_benign",
        re.compile(
            r"(?:ce\s+n['’]?est\s+pas\s+grave|pas\s+inqui[eé]tant|"
            r"nothing\s+to\s+worry\s+about|not\s+serious|harmless)",
            re.IGNORECASE,
        ),
    ),
    (
        "downgrade_emergency_urgency",
        re.compile(
            r"(?:ce\s+n['’]?est\s+pas\s+une\s+urgence|"
            r"pas\s+besoin\s+d['’]?urgence|not\s+an\s+emergency|"
            r"no\s+need\s+for\s+emergency)",
            re.IGNORECASE,
        ),
    ),
    (
        "delay_professional_assessment",
        re.compile(
            r"(?:attends?\s+(?:demain|quelques\s+jours)|wait\s+until\s+tomorrow|"
            r"no\s+need\s+to\s+(?:see|contact)\s+(?:a\s+)?doctor|"
            r"pas\s+besoin\s+de\s+(?:voir|contacter)\s+(?:un\s+)?m[eé]decin)",
            re.IGNORECASE,
        ),
    ),
    (
        "prescribe_symptom_treatment",
        re.compile(
            r"\b(?:prends?|take)\b.{0,40}"
            r"\b(?:m[eé]dicament|medicine|parac[eé]tamol|acetaminophen|ibuprofen|aspirin)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "diagnose_from_symptom",
        re.compile(
            r"\b(?:tu\s+as|vous\s+avez|you\s+have|this\s+is|c['’]?est)\b.{0,32}"
            r"\b(?:hypoglyc[eé]mie|hyperglyc[eé]mie|ketoacidosis|ketoacidose|"
            r"acidoc[eé]tose|infection|diabetes|diab[eè]te)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "attribute_symptom_to_glucose",
        re.compile(
            r"\b(?:fatigue|fatigu[eé]|naus[eé]e|vomit\w*|sympt[oô]me|tired|nausea)\b"
            r".{0,56}\b(?:caus[eé]|cause|because\s+of|à\s+cause\s+de|explique)\b"
            r".{0,40}\b(?:glucose|glyc[eé]mie|sugar|sucre|diab[eè]te|diabetes)\b",
            re.IGNORECASE,
        ),
    ),
)


def observe_symptom_triage_actions(text: str) -> tuple[str, ...]:
    if not isinstance(text, str) or not text.strip():
        return ("malformed_narration",)
    observed: list[str] = []
    for action, pattern in _ACTION_PATTERNS:
        if pattern.search(text) and action not in observed:
            observed.append(action)
    return tuple(observed)


def verify_symptom_triage_narration(
    decision: AdviceDecision,
    text: str,
) -> NarrationVerification:
    if not decision.rule_id.startswith("diabetes.symptom."):
        return verify_observed_actions(decision, ("wrong_rule_family",))
    return verify_observed_actions(
        decision,
        observe_symptom_triage_actions(text),
    )


def verified_symptom_triage_narration_or_fallback(
    decision: AdviceDecision,
    candidate: str,
    fallback: str,
) -> str:
    candidate_check = verify_symptom_triage_narration(decision, candidate)
    if candidate_check.passed:
        return candidate

    fallback_check = verify_symptom_triage_narration(decision, fallback)
    if not fallback_check.passed:
        raise PermissionError(
            "deterministic SYMPTOM_TRIAGE fallback failed narration verification: "
            + ", ".join(fallback_check.violations)
        )
    return fallback


__all__ = [
    "observe_symptom_triage_actions",
    "verified_symptom_triage_narration_or_fallback",
    "verify_symptom_triage_narration",
]
