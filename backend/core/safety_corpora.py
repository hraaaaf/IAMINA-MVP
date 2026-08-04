"""Executable safety-corpus metadata for locale and input-form parity.

Automated classification evidence is separate from native-speaker approval.
No corpus may be considered approved unless a restricted review manifest covers
its exact fingerprint and every case identifier.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from core.triage_classification import (
    TriageClass,
    glycemic_emergency_variant_inventory,
)


@dataclass(frozen=True, slots=True)
class SafetyCorpusCase:
    case_id: str
    locale: str
    channel: str
    input_form: str
    text: str
    expected: TriageClass
    review_scope: str = "representative"


@dataclass(frozen=True, slots=True)
class SafetyCorpusReview:
    locale: str
    reviewer: str | None
    reviewed_on: str | None
    status: str


CORPUS_REVIEWS: tuple[SafetyCorpusReview, ...] = (
    SafetyCorpusReview("fr", None, None, "pending_native_review"),
    SafetyCorpusReview("ar", None, None, "pending_native_review"),
    SafetyCorpusReview("en", None, None, "pending_native_review"),
    SafetyCorpusReview("ar-MA", None, None, "pending_native_review"),
)


GLYCEMIC_EMERGENCY_CASES: tuple[SafetyCorpusCase, ...] = (
    SafetyCorpusCase(
        "fr-text-01",
        "fr",
        "text",
        "native_script",
        "Je vais m'evanouir, je vois flou",
        TriageClass.GLYCEMIC_EMERGENCY,
    ),
    SafetyCorpusCase(
        "ar-text-01",
        "ar",
        "text",
        "native_script",
        "عندي دوخة وغادي يغمى عليا",
        TriageClass.GLYCEMIC_EMERGENCY,
    ),
    SafetyCorpusCase(
        "en-text-01",
        "en",
        "text",
        "numeric",
        "My blood sugar is 40",
        TriageClass.GLYCEMIC_EMERGENCY,
    ),
    SafetyCorpusCase(
        "darija-latin-01",
        "ar-MA",
        "text",
        "latin_transliteration",
        "ghadi nti7 ma kanchofch",
        TriageClass.GLYCEMIC_EMERGENCY,
    ),
    SafetyCorpusCase(
        "darija-latin-02",
        "ar-MA",
        "voice_transcript",
        "latin_transliteration",
        "f9edt l3a9l w kanr3ed",
        TriageClass.GLYCEMIC_EMERGENCY,
    ),
    SafetyCorpusCase(
        "darija-arabic-01",
        "ar-MA",
        "text",
        "arabic_script",
        "غادي نطيح وما كنشوف والو",
        TriageClass.GLYCEMIC_EMERGENCY,
    ),
    SafetyCorpusCase(
        "darija-mixed-01",
        "ar-MA",
        "text",
        "mixed_language",
        "sukkar 40 وكنترعد",
        TriageClass.GLYCEMIC_EMERGENCY,
    ),
)


def _variant_case_id(*, locale: str, input_form: str, text: str) -> str:
    digest = hashlib.sha256(f"{locale}\0{input_form}\0{text}".encode()).hexdigest()[:12]
    locale_token = locale.lower().replace("-", "_")
    return f"variant-{locale_token}-{input_form}-{digest}"


def _high_severity_variant_cases() -> tuple[SafetyCorpusCase, ...]:
    return tuple(
        SafetyCorpusCase(
            case_id=_variant_case_id(
                locale=variant.locale,
                input_form=variant.input_form,
                text=variant.text,
            ),
            locale=variant.locale,
            channel="text",
            input_form=variant.input_form,
            text=variant.text,
            expected=TriageClass.GLYCEMIC_EMERGENCY,
            review_scope="high_severity_exact_variant",
        )
        for variant in glycemic_emergency_variant_inventory()
    )


HIGH_SEVERITY_VARIANT_CASES = _high_severity_variant_cases()


def all_safety_corpus_cases() -> tuple[SafetyCorpusCase, ...]:
    """Return a stable de-duplicated corpus for automated and human review."""
    by_id: dict[str, SafetyCorpusCase] = {}
    for case in (*GLYCEMIC_EMERGENCY_CASES, *HIGH_SEVERITY_VARIANT_CASES):
        existing = by_id.get(case.case_id)
        if existing is not None and existing != case:
            raise ValueError(f"conflicting safety corpus case id: {case.case_id}")
        by_id[case.case_id] = case
    return tuple(by_id[case_id] for case_id in sorted(by_id))


def native_review_complete(locale: str) -> bool:
    """Legacy in-source status; real release approval uses the restricted manifest gate."""
    review = next((item for item in CORPUS_REVIEWS if item.locale == locale), None)
    return bool(
        review
        and review.status == "approved"
        and review.reviewer
        and review.reviewed_on
    )
