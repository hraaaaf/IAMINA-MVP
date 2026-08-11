"""
Central medical safety policy for patient-visible AI output.
"""

from __future__ import annotations

import re

from django.conf import settings

_FORBIDDEN_PATTERNS = [
    re.compile(r"\baugment(?:e|ez|er)?\b.{0,40}\b(?:dose|insuline|traitement)\b", re.IGNORECASE),
    re.compile(r"\bdiminu(?:e|ez|er)?\b.{0,40}\b(?:dose|insuline|traitement)\b", re.IGNORECASE),
    re.compile(
        r"\barr[eê]t(?:e|ez|er)?\b.{0,40}\b(?:traitement|insuline|m[ée]dicament)\b", re.IGNORECASE
    ),
    re.compile(r"\bprends?\b.{0,20}\b\d+\s*(?:u|unit[ée]s?)\b", re.IGNORECASE),
    re.compile(r"\bbolus\b", re.IGNORECASE),
    re.compile(r"\binsuline rapide\b", re.IGNORECASE),
    re.compile(r"\btu as s[uû]rement\b", re.IGNORECASE),
    re.compile(r"\bvous avez s[uû]rement\b", re.IGNORECASE),
    re.compile(r"\bpas besoin de m[ée]decin\b", re.IGNORECASE),
    re.compile(r"\bgu[ée]rir\b", re.IGNORECASE),
]


def medical_pilot_mode_enabled() -> bool:
    return bool(getattr(settings, "MEDICAL_PILOT_MODE", False))


def medical_streaming_enabled() -> bool:
    return bool(getattr(settings, "LLM_MEDICAL_STREAMING", False))


def insulin_advice_allowed() -> bool:
    return bool(getattr(settings, "ALLOW_INSULIN_ADVICE", False))


def diagnosis_allowed() -> bool:
    return bool(getattr(settings, "ALLOW_DIAGNOSIS", False))


def no_prescription_message(language: str = "fr") -> str:
    if language == "ar-MA":
        return (
            "Ma nqderch nbadel lik traitement, n3ti dosage dial insuline, "
            "wla n9ol tashkhis. Nqder n3awnk tfham l-ma3loumat dyalk "
            "w t7dder as2ila l-tabib."
        )
    if language == "ar":
        return (
            "لا يمكنني وصف علاج أو تعديل جرعة الأنسولين أو إيقاف دواء أو تشخيص حالة. "
            "يمكنني مساعدتك في تنظيم ملاحظاتك وتحضير أسئلة لطبيبك."
        )
    if language == "en":
        return (
            "I cannot prescribe treatment, change an insulin dose, stop medication, "
            "or diagnose a condition. I can help organize your observations and "
            "prepare questions for your clinician."
        )
    return (
        "Je ne peux pas prescrire, modifier une dose d'insuline, arreter un traitement, "
        "ou poser un diagnostic. Je peux t'aider a organiser tes observations "
        "et preparer les bonnes questions pour ton medecin."
    )


def violates_no_prescription_policy(text: str) -> bool:
    if not text:
        return False

    for pattern in _FORBIDDEN_PATTERNS:
        if pattern.search(text):
            return True
    return False


def apply_no_prescription_policy(text: str, language: str = "fr") -> str:
    if not text:
        return text
    if violates_no_prescription_policy(text):
        return no_prescription_message(language)
    return text


_STRUCTURED_CLINICAL_INSIGHT_KEYS = frozenset(
    {"code", "priority", "icon", "title", "content", "action"}
)


def _observation_only_envelope(language: str) -> dict[str, str]:
    """Return the fail-closed patient wording for a structured clinical insight.

    Detector codes, model prose and compatibility-era fallback strings are not
    patient-visible authority. Until a richer evidence-bearing presentation
    contract is supplied, the safe boundary is an observation-only envelope.
    """
    if language == "ar-MA":
        return {
            "title": "ملاحظة فالمعطيات ديالك",
            "content": (
                "بان واحد النمط فالمعطيات اللي تحللات. هاد الملاحظة بوحدها ما كتكفيش "
                "باش نحددو السبب ولا نشخصو شي حالة."
            ),
            "action": (
                "تقدر تدوّن السياق وتوجد هاد الملاحظة باش تهضر عليها مع المختص الصحي ديالك."
            ),
        }
    if language == "ar":
        return {
            "title": "ملاحظة في بياناتك",
            "content": (
                "ظهرت ملاحظة متكررة في البيانات التي تم تحليلها. هذه الملاحظة وحدها "
                "لا تكفي لإثبات سبب أو تشخيص."
            ),
            "action": (
                "يمكنك تدوين السياق وتحضير هذه الملاحظة لمناقشتها مع مختص الرعاية الصحية."
            ),
        }
    if language == "en":
        return {
            "title": "Observation in your data",
            "content": (
                "A pattern was found in the data analyzed. This observation alone is not "
                "enough to establish a cause or diagnosis."
            ),
            "action": (
                "You can note the context and prepare this observation to discuss with "
                "your healthcare professional."
            ),
        }
    return {
        "title": "Observation dans tes données",
        "content": (
            "Une tendance a été repérée dans les données analysées. Cette observation ne "
            "suffit pas, à elle seule, à établir une cause ou un diagnostic."
        ),
        "action": (
            "Tu peux noter le contexte et préparer cette observation pour en parler avec "
            "ton professionnel de santé."
        ),
    }


def _looks_like_structured_clinical_insight(value: dict) -> bool:
    """Recognize the stable structured-insight response shape, not arbitrary dicts."""
    return _STRUCTURED_CLINICAL_INSIGHT_KEYS.issubset(value)


def _sanitize_structured_clinical_insight(value: dict, language: str) -> dict:
    """Strip model/legacy clinical authority while preserving stable metadata."""
    safe = dict(value)
    safe.update(_observation_only_envelope(language))

    for key, item in list(safe.items()):
        if isinstance(item, str):
            safe[key] = apply_no_prescription_policy(item, language)
        elif isinstance(item, (list, tuple, dict)):
            safe[key] = sanitize_patient_visible(item, language)
    return safe


# ── Input-side insulin prescription request detection ──────────────────────
# Blocks user INPUT asking for insulin doses/prescriptions before it reaches the LLM.
# Educational questions (what is insulin, how to store it) must NOT be blocked.

_INSULIN_INPUT_PATTERNS = [
    # French — dose/prescription questions
    re.compile(
        r"\bcombien\b.{0,30}\b(?:d['']|d')?unit[ée]s?\b.{0,20}\binsul(?:ine|in)\b", re.IGNORECASE
    ),
    re.compile(
        r"\bcombien\b.{0,30}\binsul(?:ine|in)\b.{0,20}\b(?:d['']|d')?unit[ée]s?\b", re.IGNORECASE
    ),
    re.compile(r"\bcombien\b.{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\b(?:dose|dosage)\b.{0,20}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\binsul(?:ine|in)\b.{0,20}\b(?:dose|dosage)\b", re.IGNORECASE),
    re.compile(r"\bprends?\b.{0,20}\b\d+\s*(?:u|unit[ée]s?)\b", re.IGNORECASE),
    re.compile(r"\bprends?\b.{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bprendre\b.{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bje\s+dois\b.{0,30}\bprendre\b.{0,20}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bje\s+dois\b.{0,30}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bcombien\b.{0,20}\bprendre\b.{0,20}\binsul(?:ine|in)\b", re.IGNORECASE),
    re.compile(r"\bbolus\b.{0,20}\b(?:quantit[ée]|montant|volume|combien)\b", re.IGNORECASE),
    re.compile(r"\bquantit[ée]\b.{0,20}\bbolus\b", re.IGNORECASE),
    # French — adjustment questions
    re.compile(
        r"\b(?:augment|diminu|chang|adjust|modifi|adapt)[^\n]{0,30}\binsul(?:ine|in)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\binsul(?:ine|in)\b.{0,30}\b(?:augment|diminu|chang|adjust|modifi|adapt)\b", re.IGNORECASE
    ),
    # Darija (Latin script)
    re.compile(
        r"\bchhal\b.{0,20}\b(?:nakhod|nakhud|nqder|n9der|neds|nedi|nadi)\b.{0,20}\binsulin(?:e)?\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bchhal\b.{0,20}\binsulin(?:e)?\b", re.IGNORECASE),
    re.compile(r"\binsulin(?:e)?\b.{0,20}\bchhal\b", re.IGNORECASE),
    re.compile(r"\binsulin(?:e)?\b.{0,20}\b(?:dose|jra3a|jra3a)\b", re.IGNORECASE),
    # Arabic script
    re.compile(r"كم\s+وحدة\s+أنسولين"),
    re.compile(r"كم\s+وحدة\s+انسولين"),
    re.compile(r"جرعة\s+الأنسولين"),
    re.compile(r"جرعة\s+انسولين"),
    re.compile(r"كم\s+أنسولين"),
    re.compile(r"كم\s+انسولين"),
]


def is_insulin_prescription_request(text: str | None) -> bool:
    """Return True if user input is asking for an insulin dose, amount, or prescription.

    Returns False for educational / informational questions about insulin
    (what is it, how to store it, side effects, etc.).
    """
    if not text:
        return False
    for pattern in _INSULIN_INPUT_PATTERNS:
        if pattern.search(text):
            return True
    return False


# Additional multilingual output-side prescription patterns. These are defense in
# depth for generated/fallback text; input-side blocking remains authoritative.
_FORBIDDEN_PATTERNS.extend(
    [
        re.compile(
            r"\b(?:increase|decrease|reduce|double|change|adjust|stop)\b.{0,45}"
            r"\b(?:dose|insulin|medication|medicine|treatment)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:take|inject|use)\b.{0,25}\b\d+(?:[.,]\d+)?\s*(?:u|units?)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\brapid[- ]acting insulin\b", re.IGNORECASE),
        re.compile(
            r"(?:زد|زِد|نقص|خفف|ضاعف|أوقف|اوقف).{0,30}"
            r"(?:جرعة|الأنسولين|الانسولين|دواء|العلاج)"
        ),
        re.compile(r"(?:خذ|خد|حقن).{0,20}\d+(?:[.,]\d+)?\s*(?:وحدة|وحدات)"),
        re.compile(
            r"\b(?:zid|n9es|nqes|doubli|hbes|wa9ef)\b.{0,30}"
            r"\b(?:dose|insulin|insuline|dwa|traitement)\b",
            re.IGNORECASE,
        ),
    ]
)

_INSULIN_INPUT_PATTERNS.extend(
    [
        re.compile(
            r"\b(?:how much|how many)\b.{0,30}\b(?:insulin|units?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:what|which)\b.{0,15}\b(?:dose|dosage)\b.{0,25}\binsulin\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\binsulin\b.{0,30}\b(?:dose|dosage|how much|how many)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bshould i\b.{0,30}\b(?:take|inject|increase|decrease|double)\b.{0,30}\binsulin\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bch7al\b.{0,25}\binsulin(?:e)?\b", re.IGNORECASE),
    ]
)

_TREATMENT_INPUT_PATTERNS = [
    re.compile(
        r"\b(?:dois[- ]?je|je dois|est[- ]?ce que je dois|puis[- ]?je)\b.{0,45}"
        r"\b(?:arr[eê]ter|stopper|doubler|augmenter|diminuer|changer|modifier|adapter)\b.{0,45}"
        r"\b(?:traitement|m[ée]dicament|metformine|dose|insuline)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:quelle?|combien)\b.{0,25}\b(?:dose|dosage)\b.{0,35}"
        r"\b(?:m[ée]dicament|metformine|traitement)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bprescri(?:s|re|vez|ption)\b.{0,40}"
        r"\b(?:moi|traitement|m[ée]dicament|dose)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bshould i\b.{0,40}\b(?:stop|double|increase|decrease|change|adjust|skip)\b.{0,40}"
        r"\b(?:medication|medicine|treatment|metformin|dose)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:what|which|how much)\b.{0,20}\b(?:dose|dosage)\b.{0,35}"
        r"\b(?:medication|medicine|metformin|treatment)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bprescribe\b.{0,35}\b(?:medication|medicine|treatment|dose)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:هل|واش).{0,20}(?:أوقف|اوقف|نوقف|نحبس|أضاعف|اضاعف|نضاعف|نزيد|ننقص)"
        r".{0,35}(?:الدواء|دواء|العلاج|الجرعة|جرعة)"
    ),
    re.compile(
        r"(?:ما هي|ماهي|شنو|شحال|كم).{0,20}(?:الجرعة|جرعة)"
        r".{0,25}(?:الدواء|دواء|الميتفورمين|متفورمين)"
    ),
    re.compile(
        r"\b(?:wach|wash)\b.{0,25}\b(?:nhbes|hbes|nwa9ef|nzid|n9es|nqes|ndoubli)\b"
        r".{0,35}\b(?:dwa|dose|traitement|metformin|metformine)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:chhal|ch7al)\b.{0,25}\b(?:dose|dwa|metformin|metformine)\b",
        re.IGNORECASE,
    ),
]


def is_treatment_prescription_request(text: str | None) -> bool:
    """Detect requests to prescribe, stop, change or dose a treatment."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _TREATMENT_INPUT_PATTERNS)


def sanitize_patient_visible(value, language: str = "fr"):
    """Apply prescription and epistemic safety to patient-visible structures."""
    if isinstance(value, str):
        return apply_no_prescription_policy(value, language)
    if isinstance(value, list):
        return [sanitize_patient_visible(item, language) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_patient_visible(item, language) for item in value)
    if isinstance(value, dict):
        if _looks_like_structured_clinical_insight(value):
            return _sanitize_structured_clinical_insight(value, language)
        return {key: sanitize_patient_visible(item, language) for key, item in value.items()}
    return value
