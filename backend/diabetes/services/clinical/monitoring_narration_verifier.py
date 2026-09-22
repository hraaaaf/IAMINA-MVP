"""Deterministic verifier for MONITORING_INTERPRETATION narration."""
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
            r"\b(?:change|modifie|modifiez|arrête|arrêtez|stop|increase|decrease|"
            r"reduce|réduis|reduis|augmente|diminue|double|halve)\b.{0,56}"
            r"\b(?:ton|ta|tes|votre|your)\s+(?:traitement|treatment|insulin(?:e)?|"
            r"médicament|medication|dose)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "recommend_compensatory_activity",
        re.compile(
            r"\b(?:marche|marcher|walk|exercise|sport|activité)\b.{0,64}"
            r"\b(?:faire\s+baisser|lower|corriger|correct|compens\w*)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "declare_clinical_improvement_or_deterioration",
        re.compile(
            r"(?:\b(?:ton|ta|your)\s+(?:diabète|diabetes|état|condition)\b.{0,48}"
            r"\b(?:s['’]?améliore|se\s+dégrade|improv\w*|worsen\w*)\b"
            r"|\b(?:tu\s+vas|you\s+are\s+doing)\s+(?:mieux|pire|better|worse)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "diagnose_from_monitoring",
        re.compile(
            r"(?:\b(?:tes?|vos?|your)\s+(?:chiffres|values?|glyc(?:é|e)mie|glucose)\b.{0,56}"
            r"\b(?:prouvent|confirment|prove|confirm)\b.{0,40}"
            r"\b(?:diabète|diabetes|hypoglycémie|hyperglycémie)\b"
            r"|\b(?:cela|ça|this)\s+(?:signifie|means)\s+que\s+tu\s+as\b)",
            re.IGNORECASE,
        ),
    ),
)


def observe_monitoring_narration_actions(text: str) -> tuple[str, ...]:
    if not isinstance(text, str) or not text.strip():
        return ("malformed_narration",)

    observed: list[str] = []
    for action, pattern in _ACTION_PATTERNS:
        if pattern.search(text) and action not in observed:
            observed.append(action)
    return tuple(observed)


def verify_monitoring_narration(
    decision: AdviceDecision,
    text: str,
) -> NarrationVerification:
    if not decision.rule_id.startswith("diabetes.monitoring."):
        return verify_observed_actions(decision, ("wrong_rule_family",))
    return verify_observed_actions(
        decision,
        observe_monitoring_narration_actions(text),
    )


def verified_monitoring_narration_or_fallback(
    decision: AdviceDecision,
    candidate: str,
    fallback: str,
) -> str:
    candidate_check = verify_monitoring_narration(decision, candidate)
    if candidate_check.passed:
        return candidate

    fallback_check = verify_monitoring_narration(decision, fallback)
    if not fallback_check.passed:
        raise PermissionError(
            "deterministic MONITORING fallback failed narration verification: "
            + ", ".join(fallback_check.violations)
        )
    return fallback


__all__ = [
    "observe_monitoring_narration_actions",
    "verified_monitoring_narration_or_fallback",
    "verify_monitoring_narration",
]
