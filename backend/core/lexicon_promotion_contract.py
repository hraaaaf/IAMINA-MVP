"""Fail-closed contract for promoting reviewed locale evidence into runtime safety logic.

This module does not register phrases with the classifier. It only defines the
minimum evidence required before a separate runtime change may do so.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.safety_corpus_review import safety_corpus_fingerprint

APPROVED_FOR_RUNTIME = "approved_for_runtime"
REQUIRED_LOCALE = "ar-MA"
ALLOWED_CHANNELS = frozenset({"text", "voice_transcript"})
ALLOWED_INPUT_FORMS = frozenset(
    {"arabic_script", "latin_transliteration", "mixed_language"}
)
REQUIRED_REGRESSION_KINDS = frozenset(
    {"positive", "negative", "contextual", "hyperbole", "ambiguity"}
)
_REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,127}$")


@dataclass(frozen=True, slots=True)
class LexiconPromotionCandidate:
    candidate_id: str
    locale: str
    phrase: str
    channel: str
    input_form: str
    source_evidence_reference: str
    safety_corpus_fingerprint: str
    native_review_reference: str
    clinical_review_reference: str
    safety_owner_review_reference: str
    parity_review_reference: str
    regression_kinds: frozenset[str]
    decision: str


def _valid_reference(reference: str) -> bool:
    return bool(_REFERENCE_RE.fullmatch(reference))


def runtime_promotion_blockers(candidate: LexiconPromotionCandidate) -> tuple[str, ...]:
    """Return deterministic blockers. An empty tuple is required before promotion."""
    blockers: list[str] = []

    if not candidate.candidate_id.strip():
        blockers.append("candidate_id:missing")
    if candidate.locale != REQUIRED_LOCALE:
        blockers.append(f"locale:unsupported:{candidate.locale}")
    if not candidate.phrase.strip():
        blockers.append("phrase:missing")
    if candidate.channel not in ALLOWED_CHANNELS:
        blockers.append(f"channel:unsupported:{candidate.channel}")
    if candidate.input_form not in ALLOWED_INPUT_FORMS:
        blockers.append(f"input_form:unsupported:{candidate.input_form}")

    references = {
        "source_evidence": candidate.source_evidence_reference,
        "native_review": candidate.native_review_reference,
        "clinical_review": candidate.clinical_review_reference,
        "safety_owner_review": candidate.safety_owner_review_reference,
        "parity_review": candidate.parity_review_reference,
    }
    for label, reference in references.items():
        if not _valid_reference(reference):
            blockers.append(f"{label}:missing_or_invalid")

    current_fingerprint = safety_corpus_fingerprint()
    if candidate.safety_corpus_fingerprint != current_fingerprint:
        blockers.append("safety_corpus:fingerprint_mismatch")

    missing_regressions = REQUIRED_REGRESSION_KINDS - candidate.regression_kinds
    if missing_regressions:
        blockers.extend(
            f"regression:missing:{kind}" for kind in sorted(missing_regressions)
        )

    unexpected_regressions = candidate.regression_kinds - REQUIRED_REGRESSION_KINDS
    if unexpected_regressions:
        blockers.extend(
            f"regression:unknown:{kind}" for kind in sorted(unexpected_regressions)
        )

    if candidate.decision != APPROVED_FOR_RUNTIME:
        blockers.append(f"decision:not_approved:{candidate.decision or 'missing'}")

    return tuple(sorted(blockers))


def runtime_promotion_ready(candidate: LexiconPromotionCandidate) -> bool:
    """True only when every deterministic promotion gate is satisfied."""
    return not runtime_promotion_blockers(candidate)
