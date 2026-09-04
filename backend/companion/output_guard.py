"""Deterministic condition-agnostic scope/shape guard for narrator output.

Clinical context presence is evidence, not behavior-action authorization. Until a
dedicated authorization contract exists, the chassis keeps behavior/content
selection bounded and falls back to abstract organization only.
"""
from __future__ import annotations

import re

ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f]")
LATIN_RE = re.compile(r"[A-Za-zÀ-ÿ]")
_WORD_RE = re.compile(r"\b[\wÀ-ÿ]+\b", re.UNICODE)

_FREQUENCY_SELECTION_PATTERN = re.compile(
    r"(?:\b(?:chaque jour|tous les jours|jour précédent|daily|every day|kol nhar)\b|كل\s*(?:نهار|يوم))",
    re.IGNORECASE,
)
_CLINICIAN_THERAPEUTIC_PATTERN = re.compile(
    r"(?:\b(?:dose|dosage|insulin|insuline|bolus|treatment|traitement)\b|"
    r"جرع|(?:ال)?[اإأ]نسولين|(?:ال)?أنسولين|علاج|دواء|الدواء)",
    re.IGNORECASE,
)
_CLINICIAN_RISKY_QUESTION_PATTERN = re.compile(
    r"(?:\b(?:caus(?:e|es|ing)|corrective actions?|adjustments? to (?:my|your) routine)\b|"
    r"(?:سبب|أسباب|إجراء(?:ات)? تصحيحي|تعديل.{0,20}روتين))",
    re.IGNORECASE,
)
_ARABIC_HEALTH_ACTION = r"(?:قياس|فحص|تسجيل|تدوين|مراجعة|سج[ّ]?ل|سجّل|دوّن)"
_ARABIC_HEALTH_TARGET = r"(?:السكر|سكر|السكري|مستوى السكر|القراءات|قراءات السكر|القيم)"
_HEALTH_TRACKING_SELECTION_PATTERN = re.compile(
    r"(?:"
    rf"{_ARABIC_HEALTH_ACTION}.{{0,80}}{_ARABIC_HEALTH_TARGET}"
    rf"|{_ARABIC_HEALTH_TARGET}.{{0,80}}{_ARABIC_HEALTH_ACTION}"
    r"|\b(?:record|measure|check|log)\b.{0,24}\b(?:glucose|blood sugar|sugar reading)\b"
    r"|\b(?:glucose|blood sugar|sugar reading)\b.{0,24}\b(?:record|measure|check|log)\b"
    r"|(?:after dinner|before breakfast|before bed|after breakfast|after lunch).{0,32}(?:glucose|sugar|insulin)"
    r"|(?:glucose|sugar|insulin).{0,32}(?:after dinner|before breakfast|before bed|after breakfast|after lunch)"
    r"|(?:après le dîner|avant le petit-déjeuner|avant de me coucher|après le petit-déjeuner).{0,32}(?:glycémie|sucre|insuline)"
    r"|(?:glycémie|sucre|insuline).{0,32}(?:après le dîner|avant le petit-déjeuner|avant de me coucher|après le petit-déjeuner)"
    r")",
    re.IGNORECASE,
)
_ARABIC_WEEKDAY = r"(?:إثنين|اثنين|الإثنين|الاثنين|ثلاثاء|الثلاثاء|أربعاء|اربعاء|الأربعاء|الاربعاء|خميس|الخميس|جمعة|الجمعة|سبت|السبت|أحد|احد|الأحد|الاحد)"
_SPECIFIC_SCHEDULE_SELECTION_PATTERN = re.compile(
    r"(?:"
    r"\b(?:\d{1,2}[:h]\d{2}|\d{1,2}\s*(?:am|pm))\b"
    r"|\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b"
    r"|(?:كل\s*(?:يوم|٣|3)\s*أيام|كل\s*أسبوع|أسبوعياً|أسبوعيًا|يوميًا|يومياً)"
    rf"|(?:كل\s*{_ARABIC_WEEKDAY}|يوم\s*{_ARABIC_WEEKDAY})"
    r"|(?:\d{1,2}\s*[-‑–]\s*\d{1,2}\s*(?:ص|م))"
    r"|(?:\b(?:every|each)\s+(?:morning|evening|night|week|\d+\s*days?)\b)"
    r"|(?:\d+\s*(?:دقيقة|دقائق).{0,24}(?:بعد\s*(?:العشا|العشاء)|قبل\s*(?:الفطور|النوم)))"
    r")",
    re.IGNORECASE,
)
_TECHNICAL_FAILURE_PATTERN = re.compile(
    r"(?:temporary technical issue|technical issue|probl[eè]me technique temporaire|"
    r"مشكلة تقنية مؤقتة|عطل تقني مؤقت)",
    re.IGNORECASE,
)

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
    re.compile(
        r"\b(?:note|notes|consigne|consignes|mesure|mesures)\b"
        r"(?!\s+(?:une?|la|le)?\s*(?:case|checklist|liste|rappel)\b)",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:sji|sjel|ktb|kteb)\b", re.IGNORECASE),
    re.compile(
        r"\b\d+\s*(?:min|minute|minutes|d9i9a|d9aye9)\b.{0,60}"
        r"\b(?:humeur|mood|relation|3la9at|farha)\b",
        re.IGNORECASE,
    ),
    _FREQUENCY_SELECTION_PATTERN,
    _HEALTH_TRACKING_SELECTION_PATTERN,
    _SPECIFIC_SCHEDULE_SELECTION_PATTERN,
)

_SAFE_ORGANIZATION_FR = (
    "Garde une structure très simple : trois cases vides, sans contenu imposé. "
    "Remplis seulement avec les éléments que tu as déjà choisis."
)
_SAFE_COMPACT_FR = (
    "Réduis au minimum : une checklist de trois cases vides, sans contenu imposé. "
    "Coche ce qui est fait et repars de là."
)
_SAFE_WEEK_FR = (
    "Cette semaine, garde trois cases vides maximum, sans contenu imposé. "
    "Remplis seulement avec les éléments que tu as déjà choisis."
)
_SAFE_CLINICIAN_FR = (
    "Prépare ces 4 questions :\n"
    "- Quelles informations dois-je apporter ?\n"
    "- Quels changements dois-je vous signaler ?\n"
    "- Quels critères utilisez-vous pour réévaluer mon traitement ?\n"
    "- Quand dois-je vous recontacter ?"
)
_SAFE_EMOTIONAL_FR = "Ça a l’air lourd à porter au quotidien, et je reste avec toi dans ce moment-là."

_SAFE_ORGANIZATION_EN = (
    "Keep it very simple: three empty checklist boxes with no imposed content. "
    "Fill them only with items you already chose."
)
_SAFE_COMPACT_EN = (
    "Strip it down: keep three empty checklist boxes with no imposed content. "
    "Tick what is done and restart from there."
)
_SAFE_WEEK_EN = (
    "This week, keep at most three empty checklist boxes with no imposed content. "
    "Fill them only with items you already chose."
)
_SAFE_CLINICIAN_EN = (
    "Prepare these 4 questions:\n"
    "- What information should I bring?\n"
    "- What changes should I report?\n"
    "- What criteria do you use to reassess my treatment?\n"
    "- When should I contact you again?"
)
_SAFE_EMOTIONAL_EN = "That sounds exhausting to carry every day, and I’m here with you in this moment."

_SAFE_ORGANIZATION_AR = "خلّها بسيطة: ثلاث خانات فارغة بدون محتوى مفروض، واملأ فقط بما اخترته مسبقًا."
_SAFE_COMPACT_AR = "بسّطها أكثر: ثلاث خانات فارغة فقط بدون محتوى مفروض، وعلّم فقط ما تم إنجازه."
_SAFE_WEEK_AR = "لهذا الأسبوع، احتفظ بثلاث خانات فارغة كحد أقصى بدون محتوى مفروض، واملأ فقط بما اخترته مسبقًا."
_SAFE_CLINICIAN_AR = "حضّر هذه الأسئلة الأربعة: ما المعلومات التي يجب أن أحضرها؟ ما التغيّرات التي يجب أن أخبرك بها؟ ما معايير إعادة تقييم علاجي؟ ومتى أتواصل معك مجددًا؟"
_SAFE_EMOTIONAL_AR = "واضح إن التفكير في هذا كل يوم متعب جدًا، وأنا معك في هذه اللحظة بدون ما أزيد عليك مهام."

_SAFE_DARIJA_AR = "خليها بسيطة: ثلاث خانات خاويين بلا محتوى مفروض، وعمر غير باللي نتا اخترتي من قبل."
_SAFE_COMPACT_DARIJA_AR = "خليها بسيطة: ثلاث خانات خاويين بلا محتوى مفروض، وعلم غير على اللي كملتي."
_SAFE_WEEK_DARIJA_AR = "هاد السيمانة، خلي غير ثلاث خانات خاويين بلا محتوى مفروض، وعمر غير باللي نتا اخترتي من قبل."
_SAFE_CLINICIAN_DARIJA_AR = "وجد هاد الأسئلة: شنو المعلومات اللي نجيب معايا؟ شنو التغييرات اللي نبلغك بها؟ شنو المعايير اللي كتستعمل باش تعاود تقيم العلاج ديالي؟ وإمتى نعاود نتاصل بيك؟"
_SAFE_EMOTIONAL_DARIJA_AR = "باين بلي التفكير فهاد الشي كل نهار عياك بزاف، وأنا هنا معاك دابا بلا ما نزيد عليك شي حاجة."

_SAFE_DARIJA_LATIN = "Khlliha simple: 3 cases khawyin bla contenu mfroud, w 3emmer ghir b dakchi li nta khtarti mn 9bel."
_SAFE_COMPACT_DARIJA_LATIN = "Khlliha minimal: 3 cases khawyin bla contenu mfroud, w 3ellem ghir mlli tkmel."
_SAFE_WEEK_DARIJA_LATIN = "Had simana, khlli 3 cases khawyin max bla contenu mfroud, w 3emmer ghir b dakchi li nta khtarti mn 9bel."
_SAFE_CLINICIAN_DARIJA_LATIN = "Wjjed had 4 swalat: chno njib m3aya? chno taghyir n9ol lik 3lih? b ach kat3awd t9yyem l3ilaj dyali? w imta n3awd ntwassel m3ak?"
_SAFE_EMOTIONAL_DARIJA_LATIN = "Kayban belli had lham kol nhar m3yik bzaf, w ana hna m3ak daba bla ma nzid 3lik chi haja."

_GULF_ORGANIZATION = {
    "ar-SA": "خلّها بسيطة: ثلاث خانات فاضية بدون محتوى محدد، وحط علامة بس على اللي خلصته.",
    "ar-AE": "خلّها بسيطة وايد: ثلاث خانات فاضية من غير محتوى محدد، وعلّم بس على اللي خلصته.",
    "ar-KW": "خلّها بسيطة حيل: ثلاث خانات فاضية من غير محتوى محدد، وعلّم بس على اللي خلصته.",
    "ar-QA": "خلّها بسيطة وايد: ثلاث خانات فاضية من غير محتوى محدد، وعلّم بس على اللي خلصته.",
    "ar-OM": "خلّها بسيطة واجد: ثلاث خانات فاضية من غير محتوى محدد، وعلّم بس على اللي خلصته.",
}
_GULF_CLINICIAN = {
    "ar-SA": "جهّز هالـ4 أسئلة: وش المعلومات اللي أجيبها؟ وش التغيّرات اللي أقول لك عنها؟ وش المعايير اللي تعتمدها لإعادة تقييم علاجي؟ ومتى أتواصل معك مرة ثانية؟",
    "ar-AE": "جهّز هالـ4 أسئلة: شو المعلومات اللي أجيبها؟ شو التغيّرات اللي أخبرك عنها؟ شو المعايير اللي تعتمدها لإعادة تقييم علاجي؟ ومتى أتواصل وياك مرة ثانية؟",
    "ar-KW": "جهّز هالـ4 أسئلة: شنو المعلومات اللي أجيبها؟ شنو التغيّرات اللي أقول لك عنها؟ شنو المعايير اللي تعتمدها لإعادة تقييم علاجي؟ ومتى أتواصل معاك مرة ثانية؟",
    "ar-QA": "جهّز هالـ4 أسئلة: شنو المعلومات اللي أجيبها؟ شنو التغيّرات اللي أقول لك عنها؟ شنو المعايير اللي تعتمدها لإعادة تقييم علاجي؟ ومتى أتواصل معاك مرة ثانية؟",
    "ar-OM": "جهّز هالـ4 أسئلة: وش المعلومات اللي أجيبها؟ وش التغيّرات اللي أقول لك عنها؟ وش المعايير اللي تعتمدها لإعادة تقييم علاجي؟ ومتى أتواصل معك مرة ثانية؟",
}
_GULF_EMOTIONAL = {
    "ar-SA": "أفهمك، هالمشكلة مع التفكير بالسكري كل يوم متعبة فعلًا.",
    "ar-AE": "أفهمك، ترا التفكير بالسكري كل يوم يتعب الواحد فعلًا.",
    "ar-KW": "أفهمك، التفكير بالسكري كل يوم متعب حيل.",
    "ar-QA": "أفهمك، التفكير بالسكري كل يوم متعب وايد.",
    "ar-OM": "أفهمك، التفكير بالسكري كل يوم متعب واجد.",
}
_GULF_DIALECT_MARKERS = {
    "ar-SA": ("وش", "أبغ", "الحين", "هالمشكلة", "خلّها", "نخليها", "فاضية بس"),
    "ar-AE": ("شو", "أبا", "وايد", "عقب", "ترا", "وياك"),
    "ar-KW": ("شنو", "أبي", "حيل", "عقب", "هال"),
    "ar-QA": ("شنو", "أبي", "وايد", "عقب", "هال"),
    "ar-OM": ("وش", "واجد", "بعد العشا", "هال"),
}
_DARIJA_BAD_NATURALNESS = re.compile(r"(?:مقنّع|مقنع|بكمّك|بكمك|توعدنا|خانات\s+فارغة)")


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
    very_long: bool = False,
    prefer_latin_script: bool = False,
) -> str:
    if language == "ar-MA":
        if prefer_latin_script:
            if mode == "emotional":
                return _SAFE_EMOTIONAL_DARIJA_LATIN
            if mode == "clinician_prep":
                return _SAFE_CLINICIAN_DARIJA_LATIN
            if weekly:
                return _SAFE_WEEK_DARIJA_LATIN
            return _SAFE_COMPACT_DARIJA_LATIN if very_long else _SAFE_DARIJA_LATIN
        if mode == "emotional":
            return _SAFE_EMOTIONAL_DARIJA_AR
        if mode == "clinician_prep":
            return _SAFE_CLINICIAN_DARIJA_AR
        if weekly:
            return _SAFE_WEEK_DARIJA_AR
        return _SAFE_COMPACT_DARIJA_AR if very_long else _SAFE_DARIJA_AR
    if language in _GULF_ORGANIZATION:
        if mode == "emotional":
            return _GULF_EMOTIONAL[language]
        if mode == "clinician_prep":
            return _GULF_CLINICIAN[language]
        return _GULF_ORGANIZATION[language]
    if language.startswith("ar"):
        if mode == "emotional":
            return _SAFE_EMOTIONAL_AR
        if mode == "clinician_prep":
            return _SAFE_CLINICIAN_AR
        if weekly:
            return _SAFE_WEEK_AR
        return _SAFE_COMPACT_AR if very_long else _SAFE_ORGANIZATION_AR
    if language == "en":
        if mode == "emotional":
            return _SAFE_EMOTIONAL_EN
        if mode == "clinician_prep":
            return _SAFE_CLINICIAN_EN
        if weekly:
            return _SAFE_WEEK_EN
        return _SAFE_COMPACT_EN if very_long else _SAFE_ORGANIZATION_EN
    if mode == "emotional":
        return _SAFE_EMOTIONAL_FR
    if mode == "clinician_prep":
        return _SAFE_CLINICIAN_FR
    if weekly:
        return _SAFE_WEEK_FR
    return _SAFE_COMPACT_FR if very_long else _SAFE_ORGANIZATION_FR


def guard_narrator_output(
    reply: str,
    *,
    language: str,
    approved_session_context: bool,
    mode: str = "practical",
    weekly: bool = False,
    prefer_latin_script: bool = False,
) -> str:
    del approved_session_context

    forbidden = contains_unapproved_behavior_action(reply)
    technical_failure = bool(_TECHNICAL_FAILURE_PATTERN.search(reply))
    words = word_count(reply)
    lines = nonempty_line_count(reply)
    question_count = reply.count("?") + reply.count("؟")
    if language == "ar-MA":
        script_violation = (
            prefer_latin_script and bool(ARABIC_RE.search(reply))
        ) or (
            not prefer_latin_script
            and (not ARABIC_RE.search(reply) or bool(LATIN_RE.search(reply)))
        )
    else:
        script_violation = prefer_latin_script and bool(ARABIC_RE.search(reply))

    gulf_dialect_violation = language in _GULF_DIALECT_MARKERS and not any(
        marker in reply for marker in _GULF_DIALECT_MARKERS[language]
    )
    darija_naturalness_violation = (
        language == "ar-MA"
        and bool(_DARIJA_BAD_NATURALNESS.search(reply))
    )

    if mode == "emotional":
        invalid_shape = words > 30 or lines > 1
    elif mode == "clinician_prep":
        therapeutic = bool(_CLINICIAN_THERAPEUTIC_PATTERN.search(reply))
        risky_question = bool(_CLINICIAN_RISKY_QUESTION_PATTERN.search(reply))
        invalid_shape = (
            words > 80
            or not 2 <= question_count <= 4
            or lines > 6
            or therapeutic
            or risky_question
        )
    else:
        therapeutic = bool(_CLINICIAN_THERAPEUTIC_PATTERN.search(reply))
        question_only_shape = question_count >= 2
        invalid_shape = words > 45 or lines > 5 or therapeutic or question_only_shape

    if (
        forbidden
        or technical_failure
        or invalid_shape
        or script_violation
        or gulf_dialect_violation
        or darija_naturalness_violation
    ):
        return safe_fallback(
            language,
            mode=mode,
            weekly=weekly,
            very_long=words > 60,
            prefer_latin_script=prefer_latin_script,
        )
    return reply
