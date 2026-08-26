"""Deterministic guard for narrator-only unapproved behavior actions.

The guard is intentionally narrow: it blocks explicit behavior recommendations
when no approved session context authorizes them. Mere mention or organization
of already-recorded health topics remains allowed.
"""
from __future__ import annotations

import re

ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f]")

FORBIDDEN_BEHAVIOR_PATTERNS = (
    re.compile(r"\b(?:fais|faire)\b.{0,20}\b(?:de la )?marche\b", re.IGNORECASE),
    re.compile(r"\bmarch(?:e|er)\b.{0,24}\b(?:\d+\s*)?(?:min|minute|minutes|pas)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:fais|faire|pratique|pratiquer|essaie|essayez)\b.{0,30}"
        r"\b(?:exercice|sport|activité physique)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:bois|boire)\b.{0,20}\b(?:eau|verre)\b", re.IGNORECASE),
    re.compile(r"\b(?:hydrate-toi|hydratez-vous)\b", re.IGNORECASE),
    re.compile(r"(?:^|[.!?]\s+|\n\s*[-•]?\s*)mange\b", re.IGNORECASE),
    re.compile(
        r"\b(?:essaie|essayez|pense à|tu peux|vous pouvez|je te conseille de)\b"
        r".{0,30}\b(?:marcher|boire|manger|dormir)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:try|you can|consider|remember to)\b.{0,30}"
        r"\b(?:walk|exercise|work out|drink|eat|sleep)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bwalk\b.{0,24}\b(?:\d+\s*)?(?:min|minute|minutes|steps)\b", re.IGNORECASE),
    re.compile(r"\bdrink\b.{0,20}\b(?:water|glass)\b", re.IGNORECASE),
    re.compile(r"\b(?:chreb|chrab)\b.{0,20}\b(?:lma|ma)\b", re.IGNORECASE),
    re.compile(r"\b(?:tmcha|mchi)\b.{0,20}\b(?:d9i9a|d9aye9|minute|minutes)\b", re.IGNORECASE),
    re.compile(r"\b(?:dir|diri)\b.{0,20}\b(?:riyada|riayada)\b", re.IGNORECASE),
    re.compile(r"(?:اشرب|إشرب).{0,20}(?:ماء|الماء)"),
    re.compile(r"(?:امش|إمش|مشي).{0,20}(?:دقيق|دقيقة|دقائق)"),
    re.compile(r"(?:قم|قومي|حاول|حاولي).{0,20}(?:بتمرين|بالرياضة|بالمشي)"),
)

_SAFE_ORGANIZATION = {
    "fr": "Pour cette semaine : choisis un moment fixe, mets un rappel, garde une checklist courte et coche-la quand c’est fait.",
    "en": "For this week: pick one fixed time, set one reminder, keep a short checklist, and tick it off when done.",
    "ar": "لهذا الأسبوع: اختر وقتًا ثابتًا، وضع تذكيرًا واحدًا، واحتفظ بقائمة قصيرة، ثم ضع علامة عند الإنجاز.",
    "ar-MA": "هاد السيمانة: اختار وقت ثابت، دير تذكير واحد، وخلي لائحة قصيرة وعلّم عليها ملي تكمل.",
}
_SAFE_DARIJA_LATIN = "Had simana: khtar wa9t tabet, dir reminder wa7ed, khlli checklist sghira, w 3ellem 3liha mlli tkml."


def contains_unapproved_behavior_action(reply: str) -> bool:
    return any(pattern.search(reply) for pattern in FORBIDDEN_BEHAVIOR_PATTERNS)


def safe_organization_fallback(language: str, *, prefer_latin_script: bool = False) -> str:
    if language == "ar-MA" and prefer_latin_script:
        return _SAFE_DARIJA_LATIN
    if language.startswith("ar-") and language != "ar-MA":
        return _SAFE_ORGANIZATION["ar"]
    return _SAFE_ORGANIZATION.get(language, _SAFE_ORGANIZATION["fr"])


def guard_unapproved_behavior(
    reply: str,
    *,
    language: str,
    approved_session_context: bool,
    prefer_latin_script: bool = False,
) -> str:
    if approved_session_context or not contains_unapproved_behavior_action(reply):
        return reply
    return safe_organization_fallback(language, prefer_latin_script=prefer_latin_script)
