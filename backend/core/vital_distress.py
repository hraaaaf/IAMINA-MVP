"""Condition-agnostic deterministic vital-distress detection.

This module contains the shared legacy keyword coverage used before generative
AI. It deliberately has no dependency on a disease module.
"""

from __future__ import annotations

import re

_FR_CRITICAL = frozenset(
    {
        "inconscient",
        "inconsciente",
        "perd connaissance",
        "perdu connaissance",
        "perte de connaissance",
        "coma",
        "comateux",
        "convulsion",
        "convulsions",
        "épilepsie",
        "crise d'épilepsie",
        "arrêt cardiaque",
        "infarctus",
        "crise cardiaque",
        "hypoglycémie sévère",
        "très bas",
        "glycémie très basse",
        "j'appelle le samu",
        "je tombe dans les pommes",
        "ne répond plus",
        "ne bouge plus",
        "j'ai du mal à respirer",
        "difficulté à respirer",
        "essoufflement grave",
        "avc",
        "accident vasculaire",
        "vomissements incontrôlables",
        "vomissement continu",
        "déshydratation grave",
        "déshydraté",
    }
)

_DARIJA_CRITICAL = frozenset(
    {
        "ma3endouch l7al",
        "tayb3ed 3lik",
        "ghrib",
        "mchi mezyan",
        "khrj mn raso",
        "m3ih",
        "tay7 fl7al",
        "fqad l3ql",
        "mabghach y3aweb",
        "sukkar bhal zero",
        "sukkar bayna",
        "waqt l7al",
        "3yyan bzaf",
        "safi",
        "wqe3",
    }
)

_ARABIC_CRITICAL = frozenset(
    {
        "فقدان الوعي",
        "فقد الوعي",
        "غيبوبة",
        "تشنج",
        "تشنجات",
        "نوبة قلبية",
        "سكتة قلبية",
        "أزمة قلبية",
        "صعوبة التنفس",
        "لا يتنفس",
        "هبوط حاد",
        "انهيار",
        "مغشي عليه",
        "سكتة دماغية",
        "جلطة",
        "سكريتي وطا",
        "السكر وطا",
        "سكر واطي",
        "كنزووم",
        "كانزووم",
        "ساقط",
        "طايح",
        "ما كنشعرش",
        "ما كنقدرش",
        "كيدوخني",
    }
)

_NUMERIC_PATTERNS = (
    re.compile(
        r"(glycémie|glucose|sukkar|sucre\s+de\s+sang|taux\s+de\s+sucre|سكر|سكري|السكر)"
        r".{0,20}\b[1-4]\d\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b[1-4]\d\b.{0,20}(glycémie|glucose|mg.?dl|sukkar|سكر|سكري|السكر)",
        re.IGNORECASE,
    ),
)

_ALL_KEYWORDS = _FR_CRITICAL | _DARIJA_CRITICAL | _ARABIC_CRITICAL


def detect_vital_distress(text: str | None) -> bool:
    """Return whether text contains a deterministic critical-distress signal."""
    if not text:
        return False
    lowered = text.lower()
    if any(keyword in lowered for keyword in _ALL_KEYWORDS):
        return True
    return any(pattern.search(lowered) for pattern in _NUMERIC_PATTERNS)
