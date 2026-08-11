"""Fail-closed epistemic guard for generative clinical summary text.

This module does not decide whether a clinical pattern exists. It only prevents
generative narration from upgrading approved observations into a diagnosis,
confirmed mechanism/causality or an unauthorized therapeutic intervention.
"""

import re


_EPISTEMIC_OVERCLAIM_PATTERNS = (
    # French — affirmative causality / diagnostic mechanism claims.
    re.compile(
        r"\b(?:cette?|ces|les)\s+(?:donn[ée]es?|tendances?|mesures?|r[ée]sultats?)"
        r".{0,45}\b(?:prouve|prouvent|confirme|confirment|d[ée]montre|d[ée]montrent)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:est|sont)\s+(?:directement\s+)?(?:caus[ée]e?s?|provoqu[ée]e?s?)\s+par\b", re.IGNORECASE),
    re.compile(r"\bdirectement\s+li[ée]e?s?\s+[àa]\b", re.IGNORECASE),
    re.compile(r"\bph[ée]nom[eè]ne\s+de\s+l['’]?aube\b", re.IGNORECASE),
    re.compile(r"\bsomogyi\b", re.IGNORECASE),
    re.compile(r"\bdiagnostic\s+(?:de|d['’])\b", re.IGNORECASE),
    # English.
    re.compile(
        r"\b(?:this|these)\s+(?:data|pattern|trend|result|results)"
        r".{0,45}\b(?:proves?|confirms?|demonstrates?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:is|are)\s+(?:directly\s+)?caused\s+by\b", re.IGNORECASE),
    re.compile(r"\bdirectly\s+linked\s+to\b", re.IGNORECASE),
    re.compile(r"\bdawn\s+phenomenon\b", re.IGNORECASE),
    re.compile(r"\bsomogyi\b", re.IGNORECASE),
    re.compile(r"\bdiagnosis\s+of\b", re.IGNORECASE),
    # Arabic / Moroccan Arabic — affirmative proof/causality wording.
    re.compile(r"(?:هذه|هاد).{0,30}(?:تثبت|يثبت|تؤكد|يؤكد).{0,30}(?:السبب|التشخيص|الآلية)"),
    re.compile(r"(?:ناتج|ناتجة|ناتجين|ناتجات).{0,20}(?:عن|من|بسبب)"),
    re.compile(r"(?:تشخيص|التشخيص).{0,15}(?:هو|ديال|لـ)"),
)


_UNAUTHORIZED_INTERVENTION_PATTERNS = (
    # Non-prescription interventions that legacy summary examples could teach.
    re.compile(r"\b(?:collation|snack)\b", re.IGNORECASE),
    re.compile(r"\b(?:marche|marcher|walk)\b.{0,25}\b\d+\s*(?:min|minutes?)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:mange|manger|consomme|eat|consume)\b.{0,35}"
        r"\b(?:glucides?|carbs?|carbohydrates?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?:تناول|كل).{0,25}(?:كربوهيدرات|سكريات)"),
)


def violates_epistemic_claim_policy(text: str | None) -> bool:
    """Return True when generated summary text exceeds its evidence authority."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _EPISTEMIC_OVERCLAIM_PATTERNS) or any(
        pattern.search(text) for pattern in _UNAUTHORIZED_INTERVENTION_PATTERNS
    )
