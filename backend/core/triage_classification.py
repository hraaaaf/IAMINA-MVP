"""Deterministic crisis and glycemic-emergency classification.

This classifier belongs to the shared safety core because it decides whether a
patient message must bypass generative AI. Condition modules may consume the
result, but core safety must not depend on a condition module to make the gate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from safety.crisis import (
    CRISIS_RESOURCES,
    crisis_support_response,
    is_hyperbole,
    is_ideation,
)

__all__ = [
    "CRISIS_RESOURCES",
    "GlycemicSafetyVariant",
    "TriageClass",
    "classify",
    "crisis_support_response",
    "glycemic_emergency_variant_inventory",
    "select_triage_response",
]


class TriageClass(str, Enum):
    NONE = "none"
    GLYCEMIC_EMERGENCY = "glycemic_emergency"
    SUICIDAL_IDEATION = "suicidal_ideation"


@dataclass(frozen=True, slots=True)
class GlycemicSafetyVariant:
    """One exact high-severity phrase that requires native review coverage."""

    locale: str
    input_form: str
    text: str


_GLYCEMIC_FR = frozenset(
    {
        "perte de connaissance",
        "evanoui",
        "evanouie",
        "je vais m'evanouir",
        "convulsion",
        "convulsions",
        "je tremble",
        "tremblements",
        "malaise",
        "vertige",
        "vertiges",
        "confusion",
        "hypo severe",
        "coma",
        "inconscient",
        "inconsciente",
        "je vois flou",
        "sueurs froides",
    }
)

_GLYCEMIC_DARIJA = frozenset(
    {
        "ghadi ntih",
        "ghadi ntah",
        "ghadi nti7",
        "ghadi nte7",
        "kantih",
        "fqad l3ql",
        "fqdt l3ql",
        "fqedt l3a9l",
        "f9edt l3a9l",
        "f9dt l3ql",
        "tahwid",
        "kayrjraj",
        "kanrjef",
        "kanrjaf",
        "kanr3ed",
        "kanr3ad",
        "rj fou",
        "rajef",
        "ma kan7ml",
        "ma kan7mlch",
        "dwakht",
        "dayakht",
        "dwekh",
        "dawkhani",
        "ma kanchoufch",
        "ma kanchofch",
        "ma kanchufch",
        "ma kanchouf walou",
        "ma kanchouf walo",
    }
)

_GLYCEMIC_ARABIC = frozenset(
    {
        "فقدان الوعي",
        "غيبوبة",
        "إغماء",
        "اغماء",
        "تشنج",
        "تشنجات",
        "رعشة",
        "دوخة",
        "فقدت الوعي",
        "ما كنشوفش",
        "ما كنشوف والو",
        "غادي نطيح",
        "غادي نغمى عليا",
        "غادي يغمى عليا",
        "كنترعد",
        "كنرجف",
    }
)

# High-precision numeric distress: 10-49 mg/dL or 300-599 mg/dL near a
# glucose-related term. Ordinary values such as 140 must not trigger triage.
_NUMERIC_GLUCOSE = re.compile(
    r"\b([1-4]\d|3\d{2}|4\d{2}|5\d{2})\b[^\d]{0,20}"
    r"\b(sukkar|sucre|glyc\w*|sugar|سكر)\b"
    r"|\b(sukkar|sucre|glyc\w*|sugar|سكر)\b[^\d]{0,20}"
    r"\b([1-4]\d|3\d{2}|4\d{2}|5\d{2})\b",
    re.IGNORECASE,
)


def glycemic_emergency_variant_inventory() -> tuple[GlycemicSafetyVariant, ...]:
    """Return every exact phrase used by the deterministic high-severity gate.

    The inventory is stable-sorted and deliberately excludes the numeric regex,
    which is covered by separate representative corpus cases. Adding or removing
    a phrase changes the safety review packet fingerprint and invalidates stale
    human approvals.
    """
    variants = [
        *(GlycemicSafetyVariant("fr", "native_script", text) for text in _GLYCEMIC_FR),
        *(
            GlycemicSafetyVariant("ar-MA", "latin_transliteration", text)
            for text in _GLYCEMIC_DARIJA
        ),
        *(
            GlycemicSafetyVariant(
                "ar-MA" if "كن" in text or "غادي" in text or "ما " in text else "ar",
                "arabic_script",
                text,
            )
            for text in _GLYCEMIC_ARABIC
        ),
    ]
    return tuple(sorted(variants, key=lambda item: (item.locale, item.input_form, item.text)))


def _normalize(message: str) -> str:
    return re.sub(r"\s+", " ", message.strip().lower())


def classify(message: str) -> TriageClass:
    """Classify a message using deterministic safety-first ordering.

    Hyperbole is evaluated before ideation to avoid false positives in common
    Darija expressions. Confirmed ideation and glycemic emergencies bypass the
    normal generative path.
    """
    if not message:
        return TriageClass.NONE

    normalized = _normalize(message)

    if is_hyperbole(normalized):
        return TriageClass.NONE
    if is_ideation(normalized):
        return TriageClass.SUICIDAL_IDEATION
    if _NUMERIC_GLUCOSE.search(normalized):
        return TriageClass.GLYCEMIC_EMERGENCY
    if any(keyword in normalized for keyword in _GLYCEMIC_FR):
        return TriageClass.GLYCEMIC_EMERGENCY
    if any(keyword in normalized for keyword in _GLYCEMIC_DARIJA):
        return TriageClass.GLYCEMIC_EMERGENCY
    if any(keyword in message for keyword in _GLYCEMIC_ARABIC):
        return TriageClass.GLYCEMIC_EMERGENCY

    return TriageClass.NONE


def select_triage_response(
    triage_class: TriageClass,
    *,
    glycemic_template: str,
    region: str = "MA",
    lang: str = "fr",
) -> str | None:
    """Select a fixed non-generative response for a classified emergency."""
    if triage_class is TriageClass.SUICIDAL_IDEATION:
        return crisis_support_response(region=region, lang=lang)
    if triage_class is TriageClass.GLYCEMIC_EMERGENCY:
        return glycemic_template
    return None
