"""Governed FOOD_DECISION rule family for the diabetes capsule.

The rule does not label foods as universally allowed/forbidden. It authorizes
bounded education/practical support around portion and carbohydrate context.
Treatment, insulin dosing and compensatory exercise remain forbidden.
"""
from __future__ import annotations

import re
from enum import StrEnum

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution

ADA_2026_NUTRITION = "ADA_SOC_2026_SECTION_5"
NICE_NG17_DIETARY = "NICE_NG17_DIETARY_MANAGEMENT"
NICE_NG28_DIETARY = "NICE_NG28_DIETARY_ADVICE_2026"

_EVIDENCE = (
    ADA_2026_NUTRITION,
    NICE_NG17_DIETARY,
    NICE_NG28_DIETARY,
)

_FORBIDDEN = (
    "approve_food_personally",
    "forbid_food_personally",
    "compensate_food_with_activity",
    "calculate_insulin_dose",
    "change_treatment",
)

_ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f]")
_LATIN_DARIJA_RE = re.compile(
    r"\b(?:wach|wash|n9dar|nqder|nkdar|n9dr|nakol|nchrob|makla|gateau|7lowa|khobz)\b",
    re.IGNORECASE,
)

_FOOD_CONTEXT_RE = re.compile(
    r"(?:"
    r"\b(?:manger|boire|repas|aliment|dessert|g[âa]teau|pain|riz|p[aâ]tes|"
    r"eat|drink|food|meal|dessert|cake|bread|rice|pasta|"
    r"nakol|nchrob|makla|gateau|7lowa|khobz)\b"
    r"|(?:طعام|أكل|اكل|آكل|اكل|تناول|وجبة|حلوى|كيك|خبز|رز|ناكل|نشرب|الماكلة)"
    r")",
    re.IGNORECASE,
)

_PERMISSION_PATTERNS = (
    re.compile(
        r"\b(?:(?:est[- ]?ce que|est ce que)\s+)?(?:je\s+peux|j['’]?\s*peux|puis[- ]?je|"
        r"j['’]?ai\s+le\s+droit\s+de)\s+(?:manger|prendre|boire)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:est[- ]?ce que|est ce que)\b.{0,48}"
        r"\b(?:autorisé|autorisee?|permis|ok|okay)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bcan\s+i\s+(?:eat|have|drink)\b", re.IGNORECASE),
    re.compile(r"\bam\s+i\s+allowed\s+to\s+(?:eat|have|drink)\b", re.IGNORECASE),
    re.compile(r"\bis\s+it\s+(?:ok|okay)\s+if\s+i\s+(?:eat|have|drink)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:wach|wash)?\s*(?:n9dar|nqder|nkdar|n9dr)\s+(?:nakol|nchrob)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:هل\s+)?(?:أقدر|اقدر|نقدر|ممكن)\s+(?:آكل|اكل|ناكل|أشرب|اشرب|نشرب)"
    ),
    re.compile(
        r"هل\s+(?:يمكنني|أستطيع|استطيع)\s+(?:أن\s+)?"
        r"(?:آكل|اكل|أتناول|اتناول|أشرب|اشرب|تناول)"
    ),
    re.compile(r"(?:واش\s+)?نقدر\s+(?:ناكل|نشرب)"),
    re.compile(r"(?:عادي|ينفع|مسموح)\s+(?:لي\s+)?(?:آكل|اكل|أشرب|اشرب)"),
)

_STRONG_NUTRITION_RE = re.compile(
    r"(?:\b(?:gluc(?:ides?)?|carbohydrates?|carbs?|nutrition(?:nel|nelle)?s?)\b"
    r"|(?:كربوهيدرات|الكربوهيدرات))",
    re.IGNORECASE,
)

_PORTION_LABEL_RE = re.compile(
    r"(?:\b(?:portion|étiquette|etiquette|label)\b"
    r"|(?:الحصة|الكمية|الملصق الغذائي|ليبيتيكيت))",
    re.IGNORECASE,
)

_COMPARISON_PATTERNS = (
    re.compile(
        r"\b(?:quel(?:le)?\s+est\s+(?:le|la)\s+meilleur(?:e)?|"
        r"lequel|laquelle|mieux\s+entre|comparer?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:which\s+is\s+better|better\s+between|compare)\b", re.IGNORECASE),
    re.compile(r"\b(?:achmen|chno)\s+(?:ahssen|7sen)\b", re.IGNORECASE),
    re.compile(r"(?:شنو\s+حسن|شنو\s+أحسن|أيهما\s+أفضل|ايهما\s+افضل|أيهم\s+أفضل)"),
)


class FoodDecisionIntent(StrEnum):
    PERMISSION = "food_permission"
    PORTION_CARBOHYDRATE = "food_portion_carbohydrate"
    COMPARISON = "food_comparison"
    REPORTED_CONTEXT = "food_reported_context"


_ELLIPTICAL_FOOD_FOLLOWUP_RE = re.compile(
    r"^\s*(?:"
    r"et(?:\s+(?:pour|du|de\s+la|de\s+l['’]|le|la|les))?"
    r"|and(?:\s+what\s+about)?"
    r"|what\s+about"
    r"|w|ou"
    r"|وماذا\s+عن|ماذا\s+عن"
    r")\b",
    re.IGNORECASE,
)


def classify_food_decision(message: str) -> FoodDecisionIntent | None:
    text = (message or "").strip()
    if not text:
        return None

    if (
        any(pattern.search(text) for pattern in _PERMISSION_PATTERNS)
        and _FOOD_CONTEXT_RE.search(text)
    ):
        return FoodDecisionIntent.PERMISSION
    if (
        any(pattern.search(text) for pattern in _COMPARISON_PATTERNS)
        and _FOOD_CONTEXT_RE.search(text)
    ):
        return FoodDecisionIntent.COMPARISON
    if _STRONG_NUTRITION_RE.search(text):
        return FoodDecisionIntent.PORTION_CARBOHYDRATE
    if _PORTION_LABEL_RE.search(text) and _FOOD_CONTEXT_RE.search(text):
        return FoodDecisionIntent.PORTION_CARBOHYDRATE
    return None


def _script_variant(message: str, language: str) -> str:
    if language == "ar-MA":
        return "darija_ar" if _ARABIC_RE.search(message) else "darija_latin"
    if language in {"ar-SA", "ar-AE", "ar-KW", "ar-QA", "ar-OM"}:
        return "gulf"
    if language.startswith("ar"):
        return "ar"
    if language == "en":
        return "en"
    if _LATIN_DARIJA_RE.search(message) and not _ARABIC_RE.search(message):
        return "darija_latin"
    return "fr"


_PERMISSION_REPLY = {
    "fr": (
        "Je ne te donne pas un oui/non isolé pour un aliment. "
        "Le plus utile est de regarder la portion et la quantité de glucides "
        "dans le contexte du repas. Si tu me donnes la portion ou l’étiquette, "
        "je peux t’aider à les interpréter, sans calculer de dose ni modifier ton traitement."
    ),
    "en": (
        "I won’t give a stand-alone yes/no approval for a food. "
        "The useful things to look at are the portion and carbohydrate amount "
        "in the context of the meal. If you share the portion or label, I can "
        "help interpret it without calculating a dose or changing treatment."
    ),
    "darija_latin": (
        "Ma ghanch ngolik yes/no bo7dha 3la chi makla. "
        "Lahsan nchoufo lportion w ch7al men glucides kaynin f siyak dyal lmakla. "
        "Ila 3titini lportion wla l'étiquette, n9dar n3awnk tfesserhom bla dose w bla tbdel l3ilaj."
    ),
    "darija_ar": (
        "ما غاديش نعطيك غير جواب بنعم ولا لا على شي ماكلة. "
        "الأفيد هو نشوفو الكمية والكربوهيدرات فالسياق ديال الوجبة. "
        "إلا عطيتيني الكمية ولا لابيتيكيت نقدر نعاونك نفسرهم، بلا حساب الجرعة وبلا تبديل العلاج."
    ),
    "gulf": (
        "ما أقدر أعطيك جواب نعم أو لا بشكل عام على أكلة معيّنة. "
        "الأفضل نشوف الكمية والكربوهيدرات ضمن الوجبة. "
        "إذا ترسل لي الكمية أو الملصق أقدر أساعدك نفهمهم، "
        "من غير حساب جرعة أو تغيير علاج."
    ),
    "ar": (
        "لن أعطيك موافقة عامة بنعم أو لا على طعام معيّن. "
        "الأهم هو النظر إلى الكمية ومحتوى الكربوهيدرات ضمن سياق الوجبة. "
        "إذا أعطيتني الكمية أو الملصق الغذائي أستطيع مساعدتك في تفسيرهما، "
        "من دون حساب جرعة أو تغيير العلاج."
    ),
}

_PORTION_REPLY = {
    "fr": (
        "Oui, je peux t’aider à lire la portion et les glucides indiqués. "
        "Donne-moi la quantité réellement prévue et les valeurs de l’étiquette ou de la recette. "
        "Je resterai sur l’interprétation alimentaire, sans dose ni changement de traitement."
    ),
    "en": (
        "Yes, I can help interpret the stated portion and carbohydrate information. "
        "Share the amount you plan to have and the label or recipe values. "
        "I’ll stay with food interpretation only, without dose or treatment changes."
    ),
    "darija_latin": (
        "N9dar n3awnk nqra lportion w lglucides li mktoubin. "
        "3tini ch7al bghiti takol w l9iyam dyal l'étiquette wla recette. "
        "Ghadi nb9a ghir f tafsir dyal lmakla, bla dose w bla tbdel l3ilaj."
    ),
    "darija_ar": (
        "نقدر نعاونك نقرا الكمية والكربوهيدرات اللي مكتوبين. "
        "عطيني شحال ناوي تاكل والقيم ديال لابيتيكيت ولا الوصفة. "
        "غنبقا غير فتفسير الماكلة، بلا جرعة وبلا تبديل العلاج."
    ),
    "gulf": (
        "أقدر أساعدك تقرا الكمية والكربوهيدرات المكتوبة. "
        "أرسل الكمية اللي ناوي تاخذها وقيم الملصق أو الوصفة. "
        "بنبقى على تفسير الأكل فقط، من غير جرعة أو تغيير علاج."
    ),
    "ar": (
        "أستطيع مساعدتك في قراءة الكمية ومحتوى الكربوهيدرات المذكورين. "
        "أرسل الكمية التي تنوي تناولها وقيم الملصق أو الوصفة. "
        "سأبقى ضمن تفسير الطعام فقط، من دون جرعة أو تغيير علاج."
    ),
}

_REPORTED_CONTEXT_REPLY = {
    "fr": (
        "Merci. Pour interpréter ce que tu as mangé sans tirer de conclusion trop vite, "
        "le plus utile est la portion approximative de chaque élément et, si tu les as, "
        "les glucides indiqués. Je peux t’aider à les mettre en contexte, sans calculer "
        "de dose ni modifier ton traitement."
    ),
    "en": (
        "Thanks. To interpret what you ate without jumping to conclusions, the useful "
        "next details are the approximate portions and, if available, the stated "
        "carbohydrates. I can help put those in context without calculating a dose or "
        "changing treatment."
    ),
    "darija_latin": (
        "Chokran. Bach nfessro chno kliti bla ma nstntjou bzaf, l'ahamm howa "
        "lportion ta9riban dyal kol haja w ila kaynin lglucides mktoubin. "
        "N9dar n3awnk n7ethom f siyak bla dose w bla tbdel l3ilaj."
    ),
    "darija_ar": (
        "شكراً. باش نفسرو شنو كلّيتي بلا ما نستنتجو بزاف، الأهم هو الكمية تقريباً "
        "ديال كل حاجة وإذا كانت مكتوبة الكربوهيدرات. نقدر نعاونك نحطهم فالسياق، "
        "بلا حساب الجرعة وبلا تبديل العلاج."
    ),
    "gulf": (
        "شكراً. عشان نفهم اللي أكلته من غير ما نستنتج أكثر من اللازم، نحتاج تقريباً "
        "كمية كل شيء، وإذا موجودة كمية الكربوهيدرات المكتوبة. أقدر أساعدك نحطها "
        "في سياقها من غير حساب جرعة أو تغيير علاج."
    ),
    "ar": (
        "شكراً. لفهم ما تناولته من دون استنتاج زائد، نحتاج تقريباً إلى كمية كل عنصر "
        "وإلى محتوى الكربوهيدرات إن كان متاحاً. أستطيع مساعدتك في وضع ذلك في سياقه، "
        "من دون حساب جرعة أو تغيير العلاج."
    ),
}


_COMPARISON_REPLY = {
    "fr": (
        "Je peux comparer deux options sur des éléments concrets comme la portion "
        "et les glucides, mais pas déclarer qu’un aliment est universellement « autorisé » "
        "ou « interdit ». Donne-moi les deux options et, si possible, leurs portions ou étiquettes."
    ),
    "en": (
        "I can compare two options using concrete factors such as portion and carbohydrates, "
        "but I won’t label one food as universally allowed or forbidden. "
        "Send the two options and, if possible, their portions or labels."
    ),
    "darija_latin": (
        "N9dar n9aren bin jouj options 3la 7sab lportion w lglucides, "
        "walakin ma ghanch nsmi chi makla mamnou3a wla msmou7a lkolchi. "
        "3tini jouj options w ila mumkin lportion wla l'étiquette dyalhom."
    ),
    "darija_ar": (
        "نقدر نقارن بين جوج اختيارات على حساب الكمية والكربوهيدرات، "
        "ولكن ما غاديش نقول على شي ماكلة أنها مسموحة ولا ممنوعة بشكل عام. "
        "عطيني جوج الاختيارات وإذا أمكن الكمية ولا لابيتيكيت ديالهم."
    ),
    "gulf": (
        "أقدر أقارن بين خيارين على أشياء واضحة مثل الكمية والكربوهيدرات، "
        "لكن ما راح أصنف أكلة إنها مسموحة أو ممنوعة للجميع. "
        "أرسل الخيارين ومعهم الكمية أو الملصق إذا موجود."
    ),
    "ar": (
        "أستطيع مقارنة خيارين وفق عناصر واضحة مثل الكمية والكربوهيدرات، "
        "لكن لن أصنف طعامًا بأنه مسموح أو ممنوع للجميع. "
        "أرسل الخيارين، ومعهما الكمية أو الملصق إن أمكن."
    ),
}


def _resolve_food_intent(
    intent: FoodDecisionIntent,
    message: str,
    *,
    language: str = "fr",
) -> AdviceResolution:
    variant = _script_variant(message, language)

    if intent is FoodDecisionIntent.PERMISSION:
        decision = AdviceDecision(
            intent=intent.value,
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.food.permission",
            rule_version="1",
            allowed_actions=(
                "review_portion_and_carbohydrate_context",
                "request_food_label_or_portion",
            ),
            forbidden_actions=_FORBIDDEN,
            evidence_refs=_EVIDENCE,
            limitations=(
                "no_binary_food_permission",
                "no_insulin_dose",
                "no_treatment_change",
                "no_activity_compensation",
            ),
            language=language,
        )
        return AdviceResolution(decision=decision, reply=_PERMISSION_REPLY[variant])

    if intent is FoodDecisionIntent.COMPARISON:
        decision = AdviceDecision(
            intent=intent.value,
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.food.comparison",
            rule_version="1",
            allowed_actions=(
                "compare_food_options_by_portion_and_carbohydrate",
                "request_food_label_or_portion",
            ),
            forbidden_actions=_FORBIDDEN,
            evidence_refs=_EVIDENCE,
            limitations=(
                "no_universal_allowed_forbidden_label",
                "no_treatment_change",
            ),
            language=language,
        )
        return AdviceResolution(decision=decision, reply=_COMPARISON_REPLY[variant])

    decision = AdviceDecision(
        intent=intent.value,
        authority_level=AdviceAuthorityLevel.L1_EDUCATION,
        decision=AdviceDisposition.CONSTRAIN,
        rule_id="diabetes.food.portion_carbohydrate",
        rule_version="1",
        allowed_actions=(
            "interpret_declared_portion_and_carbohydrate_information",
            "request_food_label_or_portion",
        ),
        forbidden_actions=_FORBIDDEN,
        evidence_refs=_EVIDENCE,
        limitations=("no_dose", "no_treatment_change"),
        language=language,
    )
    return AdviceResolution(decision=decision, reply=_PORTION_REPLY[variant])


def resolve_reported_food_context(
    message: str,
    *,
    language: str = "fr",
) -> AdviceResolution:
    """Resolve a food report only after the caller has established food context."""
    variant = _script_variant(message, language)
    decision = AdviceDecision(
        intent=FoodDecisionIntent.REPORTED_CONTEXT.value,
        authority_level=AdviceAuthorityLevel.L1_EDUCATION,
        decision=AdviceDisposition.CONSTRAIN,
        rule_id="diabetes.food.reported_context",
        rule_version="1",
        allowed_actions=(
            "request_food_portion",
            "interpret_declared_food_and_carbohydrate_context",
        ),
        forbidden_actions=_FORBIDDEN,
        evidence_refs=_EVIDENCE,
        limitations=(
            "food_context_established_by_conversation",
            "no_quantity_inference_without_portion",
            "no_dose",
            "no_treatment_change",
        ),
        language=language,
    )
    return AdviceResolution(
        decision=decision,
        reply=_REPORTED_CONTEXT_REPLY[variant],
    )


def resolve_food_decision(
    message: str,
    *,
    language: str = "fr",
) -> AdviceResolution | None:
    intent = classify_food_decision(message)
    if intent is None:
        return None
    return _resolve_food_intent(intent, message, language=language)


def resolve_food_followup(
    message: str,
    previous_user_message: str,
    *,
    language: str = "fr",
) -> AdviceResolution | None:
    """Resolve a bounded elliptical FOOD continuation from prior user intent.

    The current message must still contain a food anchor and an explicit
    continuation marker. Comparison intent is not inherited because it requires
    an explicit pair of options.
    """
    text = (message or "").strip()
    previous = (previous_user_message or "").strip()
    if not text or not previous:
        return None
    if classify_food_decision(text) is not None:
        return resolve_food_decision(text, language=language)
    if not _ELLIPTICAL_FOOD_FOLLOWUP_RE.search(text):
        return None
    if not _FOOD_CONTEXT_RE.search(text):
        return None

    previous_intent = classify_food_decision(previous)
    if previous_intent not in {
        FoodDecisionIntent.PERMISSION,
        FoodDecisionIntent.PORTION_CARBOHYDRATE,
    }:
        return None
    return _resolve_food_intent(previous_intent, text, language=language)


__all__ = [
    "ADA_2026_NUTRITION",
    "FoodDecisionIntent",
    "NICE_NG17_DIETARY",
    "NICE_NG28_DIETARY",
    "classify_food_decision",
    "resolve_food_decision",
    "resolve_food_followup",
    "resolve_reported_food_context",
]
