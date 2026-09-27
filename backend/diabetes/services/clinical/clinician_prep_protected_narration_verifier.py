"""Strict wrapper verifier for protected CLINICIAN_PREP narration.

The deterministic clinical body must remain byte-for-byte intact. A model may only
add a short non-clinical relational wrapper around that body.
"""
from __future__ import annotations

import re

from diabetes.services.clinical.clinician_prep_narration_verifier import (
    ClinicianPrepNarrationVerification,
    verify_clinician_prep_narration,
)

_WRAPPER_CLINICAL_RE = re.compile(
    r"(?:\b(?:diab[eè]te|diabetes|glucose|glyc[eé]mie|sugar|insulin(?:e)?|"
    r"dose|traitement|treatment|m[eé]dicament|medication|doctor|clinician|"
    r"m[eé]decin|medecin|sympt[oô]me|symptom|urgent|urgence|hypo|hyper)\b|"
    r"(?:سكري|السكر|سكر|جلوكوز|أنسولين|انسولين|جرعة|علاج|دواء|طبيب|دكتور|"
    r"أعراض|اعراض|طوارئ))",
    re.IGNORECASE,
)
_MAX_WRAPPER_CHARS = 120


def _wrapper_violations(wrapper: str) -> tuple[str, ...]:
    normalized = " ".join(wrapper.split())
    if not normalized:
        return ()

    violations: list[str] = []
    if len(normalized) > _MAX_WRAPPER_CHARS:
        violations.append("wrapper_too_long")
    if any(char.isdigit() for char in normalized):
        violations.append("wrapper_contains_number")
    if _WRAPPER_CLINICAL_RE.search(normalized):
        violations.append("wrapper_contains_clinical_content")
    return tuple(violations)


def verify_clinician_prep_protected_narration(
    decision,
    candidate: str,
    fallback: str,
) -> ClinicianPrepNarrationVerification:
    """Accept only a benign wrapper around one exact deterministic body."""
    fallback_check = verify_clinician_prep_narration(decision, fallback, fallback)
    if not fallback_check.passed:
        return fallback_check

    if not isinstance(candidate, str) or not candidate.strip():
        return ClinicianPrepNarrationVerification(False, ("malformed_narration",))

    if candidate.count(fallback) != 1:
        return ClinicianPrepNarrationVerification(
            False,
            ("protected_body_not_present_exactly_once",),
        )

    wrapper = candidate.replace(fallback, "", 1).strip()
    violations = _wrapper_violations(wrapper)
    if violations:
        return ClinicianPrepNarrationVerification(False, violations)
    return ClinicianPrepNarrationVerification(True, ())


def verified_clinician_prep_protected_narration_or_fallback(
    decision,
    candidate: str,
    fallback: str,
) -> str:
    """Return protected candidate only when wrapper + exact body both pass."""
    check = verify_clinician_prep_protected_narration(
        decision,
        candidate,
        fallback,
    )
    return candidate.strip() if check.passed else fallback.strip()


__all__ = [
    "verified_clinician_prep_protected_narration_or_fallback",
    "verify_clinician_prep_protected_narration",
]
