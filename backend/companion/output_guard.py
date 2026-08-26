"""Deterministic scope/shape guard for narrator-only output.

It blocks explicit unapproved behavior recommendations and bounds responses that
violate the narrator contract when no approved session context exists. Mere
mention or organization of recorded health topics remains allowed.
"""
from __future__ import annotations

import re

ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f]")
_WORD_RE = re.compile(r"\b[\wÀ-ÿ]+\b", re.UNICODE)

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

_SAFE_ORGANIZATION_FR = (
    "Encore plus simple : mets un seul rappel à heure fixe et garde une seule case "
    "à cocher. Si tu oublies, reprends au rappel suivant sans refaire tout le planning."
)
_SAFE_WEEK_FR = (
    "Cette semaine : choisis un seul moment fixe, mets un rappel et garde trois cases "
    "maximum. Coche seulement ce qui est fait, puis prépare deux questions pour ton médecin."
)
_SAFE_CLINICIAN_FR = (
    "Prépare ces 4 questions :\n"
    "- Quelles informations voulez-vous que je note ?\n"
    "- Quels changements dois-je vous signaler ?\n"
    "- Quels critères utilisez-vous pour réévaluer mon traitement ?\n"
    "- Quand dois-je vous recontacter ?"
)
_SAFE_EMOTIONAL_FR = "Ça a l’air lourd à porter au quotidien, et je reste avec toi dans ce moment-là."
_SAFE_ORGANIZATION_EN = (
    "Keep it simple: set one reminder at a fixed time and keep one box to tick. "
    "If you miss it, resume at the next reminder without rebuilding the plan."
)
_SAFE_WEEK_EN = (
    "This week: choose one fixed time, set one reminder, and keep at most three boxes. "
    "Tick only what is done, then prepare two questions for your clinician."
)
_SAFE_CLINICIAN_EN = (
    "Prepare these 4 questions:\n"
    "- What information should I record?\n"
    "- What changes should I report?\n"
    "- What criteria do you use to reassess my treatment?\n"
    "- When should I contact you again?"
)
_SAFE_EMOTIONAL_EN = "That sounds exhausting to carry every day, and I’m here with you in this moment."
_SAFE_ORGANIZATION_AR = "خلّيها بسيطة: تذكير واحد في وقت ثابت وقائمة قصيرة جدًا، وإذا فاتك يوم كمّل مع التذكير التالي بدون ما تعيد الخطة من البداية."
_SAFE_WEEK_AR = "لهذا الأسبوع: اختر وقتًا ثابتًا واحدًا، وضع تذكيرًا واحدًا وثلاث خانات كحد أقصى، ثم حضّر سؤالين لطبيبك."
_SAFE_CLINICIAN_AR = "حضّر هذه الأسئلة الأربعة: ما المعلومات التي تريدني أن أسجلها؟ ما التغيّرات التي يجب أن أخبرك بها؟ ما معايير إعادة تقييم علاجي؟ ومتى أتواصل معك مجددًا؟"
_SAFE_EMOTIONAL_AR = "واضح إن التفكير في هذا كل يوم متعب جدًا، وأنا معك في هذه اللحظة بدون ما أزيد عليك مهام."
_SAFE_DARIJA_LATIN = "Khlliha sahla: dir reminder wa7ed f wa9t tabet, w khlli checklist dyal 3 cases max. Ila nsiti, kmml m3a reminder li b3do bla ma t3awd kolchi."
_SAFE_WEEK_DARIJA_LATIN = "Had simana: khtar wa9t tabet wa7ed, dir reminder wa7ed, w khlli 3 cases max. F lekher, wjjed juj swalat l-tbib."
_SAFE_CLINICIAN_DARIJA_LATIN = "Wjjed had 4 swalat: chno n9yed? chno taghyir n9ol lik 3lih? b ach kat3awd t9yyem l3ilaj dyali? w imta n3awd ntwassel m3ak?"
_SAFE_EMOTIONAL_DARIJA_LATIN = "Kayban belli had lham kol nhar m3yik bzaf, w ana hna m3ak daba bla ma nzid 3lik chi haja."


def word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def nonempty_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def contains_unapproved_behavior_action(reply: str) -> bool:
    return any(pattern.search(reply) for pattern in FORBIDDEN_BEHAVIOR_PATTERNS)


def safe_fallback(
    language: str,
    *,
    mode: str,
    weekly: bool = False,
    prefer_latin_script: bool = False,
) -> str:
    if language == "ar-MA" and prefer_latin_script:
        if mode == "emotional":
            return _SAFE_EMOTIONAL_DARIJA_LATIN
        if mode == "clinician_prep":
            return _SAFE_CLINICIAN_DARIJA_LATIN
        return _SAFE_WEEK_DARIJA_LATIN if weekly else _SAFE_DARIJA_LATIN
    if language.startswith("ar"):
        if mode == "emotional":
            return _SAFE_EMOTIONAL_AR
        if mode == "clinician_prep":
            return _SAFE_CLINICIAN_AR
        return _SAFE_WEEK_AR if weekly else _SAFE_ORGANIZATION_AR
    if language == "en":
        if mode == "emotional":
            return _SAFE_EMOTIONAL_EN
        if mode == "clinician_prep":
            return _SAFE_CLINICIAN_EN
        return _SAFE_WEEK_EN if weekly else _SAFE_ORGANIZATION_EN
    if mode == "emotional":
        return _SAFE_EMOTIONAL_FR
    if mode == "clinician_prep":
        return _SAFE_CLINICIAN_FR
    return _SAFE_WEEK_FR if weekly else _SAFE_ORGANIZATION_FR


def guard_narrator_output(
    reply: str,
    *,
    language: str,
    approved_session_context: bool,
    mode: str = "practical",
    weekly: bool = False,
    prefer_latin_script: bool = False,
) -> str:
    if approved_session_context:
        return reply

    forbidden = contains_unapproved_behavior_action(reply)
    words = word_count(reply)
    lines = nonempty_line_count(reply)

    if mode == "emotional":
        invalid_shape = words > 30 or lines > 1
    elif mode == "clinician_prep":
        question_count = reply.count("?") + reply.count("؟")
        invalid_shape = words > 80 or not 2 <= question_count <= 4 or lines > 6
    else:
        invalid_shape = words > 45 or lines > 5

    if forbidden or invalid_shape:
        return safe_fallback(
            language,
            mode=mode,
            weekly=weekly,
            prefer_latin_script=prefer_latin_script,
        )
    return reply
