"""Executable safety-corpus metadata for locale and input-form parity.

Automated classification evidence is separate from native-speaker approval.
No corpus may be considered approved unless reviewer identity, review date and
review status are explicitly recorded.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.triage_classification import TriageClass


@dataclass(frozen=True)
class SafetyCorpusCase:
    case_id: str
    locale: str
    channel: str
    input_form: str
    text: str
    expected: TriageClass


@dataclass(frozen=True)
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


def native_review_complete(locale: str) -> bool:
    review = next((item for item in CORPUS_REVIEWS if item.locale == locale), None)
    return bool(
        review
        and review.status == "approved"
        and review.reviewer
        and review.reviewed_on
    )
