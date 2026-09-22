"""Governed longitudinal personalization from certified CompanionContext only.

This rule family creates no new clinical truth. It may describe one already-governed
longitudinal observation when the patient explicitly asks about their own repeated
patterns/history. It never infers causality, diagnosis, treatment response, future
outcomes or medication/dose changes.
"""
from __future__ import annotations

import re

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.companion_context import CompanionContext, CompanionPattern
from core.input_safety import ALLOW, evaluate_input_safety

_RULE_EVIDENCE_ID = "rule.personal-response.repetition.v1"
_APPROVED_CONTEXT_VERSION = "companion-overview.v1"
_APPROVED_PATTERN_VERSION = "companion-personal-pattern-intelligence.v1"
_EMPTY_CONTEXT_VERSION = "companion-context.empty.v1"

_PERSONAL_TERMS = (
    "chez moi", "mes données", "mes donnees", "mon historique", "ma glycémie",
    "ma glycemie", "mes glycémies", "mes glycemies", "pour moi", "my data",
    "my history", "my glucose", "for me", "3ndi", "dyali", "data dyali",
    "عندي", "بياناتي", "سجلي", "تاريخي",
)
_LONGITUDINAL_TERMS = (
    "sur la durée", "sur la duree", "dans le temps", "se répète", "se repete",
    "répète", "repete", "récurrent", "recurrent", "souvent", "historique",
    "longitudinal", "pattern", "tendance personnelle", "remarque", "observe",
    "over time", "repeat", "recurring", "often", "history", "notice",
    "kayt3awd", "مع الوقت", "يتكرر", "متكرر", "تاريخ",
)
_OBSERVATION_TERMS = (
    "donnée", "donnee", "data", "glyc", "glucose", "activité", "activite",
    "sport", "stress", "sommeil", "fatigue", "malade", "maladie", "repas",
    "observe", "remarque", "pattern", "exercise", "activity", "sleep", "illness",
    "meal", "notice", "قياس", "سكر", "رياض", "توتر", "نوم", "تعب", "مرض", "أكل",
)

_FOCUS_TERMS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("petit-déjeuner", "petit dejeuner", "breakfast", "ftor", "فطور"), ("meal:breakfast",)),
    (("déjeuner", "dejeuner", "lunch", "ghda", "غداء"), ("meal:lunch",)),
    (("dîner", "diner", "dinner", "3cha", "عشاء"), ("meal:dinner",)),
    (("snack", "collation", "gouter", "goûter", "سناك"), ("meal:snack",)),
    (("suhoor", "suhur", "سحور"), ("meal:suhoor",)),
    (("iftar", "ftour", "إفطار"), ("meal:iftar",)),
    (("activité", "activite", "sport", "exercise", "activity", "riyada", "رياض"), ("context:activity",)),
    (("stress", "stressed", "توتر", "ستريس"), ("context:stress",)),
    (("sommeil", "sleep", "n3as", "نوم"), ("context:poor_sleep",)),
    (("fatigue", "tired", "3ya", "تعب"), ("context:fatigue",)),
    (("malade", "maladie", "illness", "sick", "مرض"), ("context:illness",)),
    (("repas", "meal", "makla", "أكل", "وجبة"), ("meal:",)),
)

_LABELS = {
    "context:stress": ("stress enregistré", "recorded stress", "التوتر المسجل", "stress li tsjjel"),
    "context:activity": ("activité enregistrée", "recorded activity", "النشاط المسجل", "activity li tsjlat"),
    "context:illness": ("maladie enregistrée", "recorded illness", "المرض المسجل", "lmerd li tsjjel"),
    "context:poor_sleep": ("mauvais sommeil enregistré", "recorded poor sleep", "سوء النوم المسجل", "n3as ma mzyanch li tsjjel"),
    "context:fatigue": ("fatigue enregistrée", "recorded fatigue", "التعب المسجل", "l3ya li tsjjel"),
    "meal:breakfast": ("petit-déjeuner enregistré", "recorded breakfast", "الفطور المسجل", "lftor li tsjjel"),
    "meal:lunch": ("déjeuner enregistré", "recorded lunch", "الغداء المسجل", "lghda li tsjjel"),
    "meal:dinner": ("dîner enregistré", "recorded dinner", "العشاء المسجل", "l3cha li tsjjel"),
    "meal:snack": ("collation enregistrée", "recorded snack", "الوجبة الخفيفة المسجلة", "snack li tsjjel"),
    "meal:suhoor": ("suhoor enregistré", "recorded suhoor", "السحور المسجل", "s7or li tsjjel"),
    "meal:iftar": ("iftar enregistré", "recorded iftar", "الإفطار المسجل", "ftar Ramadan li tsjjel"),
}
_DENSITY_FR = {"limited": "limitée", "moderate": "modérée", "strong": "forte"}
_DENSITY_AR = {"limited": "محدودة", "moderate": "متوسطة", "strong": "مرتفعة"}
_ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f]")


def _norm(text: str) -> str:
    return " ".join((text or "").casefold().split())


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.casefold() in text for term in terms)


def classify_longitudinal_personalization(message: str) -> bool:
    text = (message or "").strip()
    if not text or evaluate_input_safety(text).action != ALLOW:
        return False
    normalized = _norm(text)
    return (
        _has_any(normalized, _PERSONAL_TERMS)
        and _has_any(normalized, _LONGITUDINAL_TERMS)
        and _has_any(normalized, _OBSERVATION_TERMS)
    )


def _focus_keys(message: str) -> tuple[str, ...] | None:
    normalized = _norm(message)
    for terms, keys in _FOCUS_TERMS:
        if _has_any(normalized, terms):
            return keys
    return None


def _date(value: str | None) -> str:
    if not isinstance(value, str) or len(value) < 10:
        raise ValueError("longitudinal pattern requires an observation date")
    return value[:10]


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _validate_pattern(pattern: CompanionPattern) -> None:
    if pattern.observation_key not in _LABELS:
        raise ValueError("unapproved longitudinal observation key")
    if pattern.evidence_id != _RULE_EVIDENCE_ID:
        raise ValueError("longitudinal pattern has unapproved evidence id")
    if pattern.source_version != _APPROVED_PATTERN_VERSION:
        raise ValueError("longitudinal pattern has unapproved source version")
    if pattern.current_state not in {"active", "resolved"}:
        raise ValueError("longitudinal pattern has unapproved current state")
    if pattern.evidence_density not in {"limited", "moderate", "strong"}:
        raise ValueError("longitudinal pattern has unapproved evidence density")
    if type(pattern.recurrence_count) is not int or pattern.recurrence_count < 1:
        raise ValueError("longitudinal pattern requires a positive recurrence count")
    _date(pattern.first_observed_at)
    _date(pattern.last_observed_at)


def _select_pattern(context: CompanionContext, message: str) -> CompanionPattern | None:
    approved = tuple(item for item in context.patterns if item.observation_key in _LABELS)
    focus = _focus_keys(message)
    if focus is not None:
        if len(focus) == 1 and focus[0].endswith(":"):
            candidates = tuple(item for item in approved if item.observation_key.startswith(focus[0]))
        else:
            candidates = tuple(item for item in approved if item.observation_key in focus)
        return candidates[0] if candidates else None
    return approved[0] if approved else None


def _label(pattern: CompanionPattern, language: str, message: str) -> str:
    fr, en, ar, darija_latin = _LABELS[pattern.observation_key]
    if language == "ar-MA" and not _ARABIC_RE.search(message):
        return darija_latin
    if language.startswith("ar"):
        return ar
    if language.startswith("en"):
        return en
    return fr


def _reply(message: str, pattern: CompanionPattern, language: str) -> str:
    first = _date(pattern.first_observed_at)
    last = _date(pattern.last_observed_at)
    episodes = pattern.recurrence_count
    density = pattern.evidence_density
    active = pattern.current_state == "active"

    if language == "ar-MA" and not _ARABIC_RE.search(message):
        state = "mazal active f projection longitudinal daba" if active else "ma b9ach active f projection longitudinal daba"
        return (
            f"F l'historique gouverné dyalk, « {_label(pattern, language, message)} » {state}. "
            f"Tban mn {first} 7tta {last}, f {episodes} episode(s), b repeatability density {density}. "
            "Hadchi association wasfiya faqat: ma kaytbetch sabab, effet dyal traitement, wala chno ghadi yوقع."
        )

    if language.startswith("ar"):
        state = "نشط في الإسقاط الطولي الحالي" if active else "غير نشط في الإسقاط الطولي الحالي"
        return (
            f"في تاريخك الطولي المنظّم، « {_label(pattern, language, message)} » {state}. "
            f"ظهر من {first} إلى {last} عبر {episodes} دورة ملاحظة، وبكثافة تكرار {_DENSITY_AR[density]}. "
            "هذا ارتباط وصفي فقط: لا يثبت سببًا، ولا استجابة للعلاج، ولا يتنبأ بما سيحدث لاحقًا."
        )

    if language.startswith("en"):
        state = "is active in the current longitudinal projection" if active else "is not active in the current longitudinal projection"
        return (
            f"In your governed longitudinal history, “{_label(pattern, language, message)}” {state}. "
            f"It was observed from {first} to {last} across {episodes} observation episode(s), "
            f"with {density} repeatability density. This is descriptive association only: "
            "it does not prove causality, treatment response, or what will happen next."
        )

    state = "est active dans la projection longitudinale actuelle" if active else "n’est plus active dans la projection longitudinale actuelle"
    return (
        f"Dans ton historique longitudinal gouverné, « {_label(pattern, language, message)} » {state}. "
        f"Elle a été observée du {first} au {last}, sur {episodes} épisode(s) d’observation, "
        f"avec une densité de répétition {_DENSITY_FR[density]}. C’est une association descriptive : "
        "elle ne prouve ni une cause, ni un effet du traitement, ni ce qui se passera ensuite."
    )


def _insufficient_reply(message: str, language: str) -> str:
    if language == "ar-MA" and not _ARABIC_RE.search(message):
        return (
            "Ma 3ndich daba observations longitudinales gouvernées kafiin bach njawb bla ma nkhmen. "
            "Donc ma ghadi nstنتj sabab, effet dyal traitement, wala future outcome."
        )
    if language.startswith("ar"):
        return (
            "لا توجد لديّ الآن ملاحظات طولية منظّمة كافية للإجابة بدون تخمين. "
            "لذلك لن أستنتج سببًا أو علاجًا أو توقعًا مستقبليًا."
        )
    if language.startswith("en"):
        return (
            "I do not have enough governed longitudinal observations to answer without guessing. "
            "I therefore will not infer a cause, treatment effect, or future outcome."
        )
    return (
        "Je n’ai pas assez d’observations longitudinales gouvernées pour répondre sans inventer. "
        "Je n’en déduis donc ni cause, ni effet du traitement, ni évolution future."
    )


def resolve_longitudinal_personalization_from_context(
    message: str,
    context: CompanionContext,
    *,
    language: str = "fr",
) -> AdviceResolution | None:
    if not classify_longitudinal_personalization(message):
        return None

    if context.source_version == _EMPTY_CONTEXT_VERSION:
        pattern = None
    elif context.source_version != _APPROVED_CONTEXT_VERSION:
        raise ValueError("longitudinal personalization requires certified companion overview")
    else:
        pattern = _select_pattern(context, message)

    if pattern is None:
        return AdviceResolution(
            decision=AdviceDecision(
                intent="longitudinal_personalization",
                authority_level=AdviceAuthorityLevel.L1_EDUCATION,
                decision=AdviceDisposition.CONSTRAIN,
                rule_id="diabetes.longitudinal.insufficient_data",
                rule_version="1",
                allowed_actions=("explain_longitudinal_data_insufficiency",),
                forbidden_actions=(
                    "infer_causality",
                    "infer_treatment_response",
                    "predict_future_outcome",
                    "diagnose_from_longitudinal_history",
                    "calculate_insulin_dose",
                    "change_treatment",
                    "promote_heuristic_inference",
                    "invent_longitudinal_facts",
                ),
                required_facts=("governed_longitudinal_pattern",),
                missing_facts=("governed_longitudinal_pattern",),
                evidence_refs=(_RULE_EVIDENCE_ID,),
                limitations=("fail_closed_without_governed_longitudinal_pattern",),
                language=language,
            ),
            reply=_insufficient_reply(message, language),
        )

    _validate_pattern(pattern)
    return AdviceResolution(
        decision=AdviceDecision(
            intent="longitudinal_personalization",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.longitudinal.descriptive_personalization",
            rule_version="1",
            allowed_actions=("describe_governed_longitudinal_observation",),
            forbidden_actions=(
                "infer_causality",
                "infer_treatment_response",
                "predict_future_outcome",
                "diagnose_from_longitudinal_history",
                "calculate_insulin_dose",
                "change_treatment",
                "promote_heuristic_inference",
                "invent_longitudinal_facts",
            ),
            required_facts=(
                "governed_longitudinal_pattern",
                "recurrence_count",
                "first_observed_at",
                "last_observed_at",
                "evidence_density",
            ),
            evidence_refs=(pattern.evidence_id,),
            limitations=_dedupe(
                (
                    "certified_companion_context_only",
                    "repeatability_density_is_not_probability_or_clinical_confidence",
                    "descriptive_association_does_not_establish_causality",
                    *pattern.limitations,
                )
            ),
            language=language,
        ),
        reply=_reply(message, pattern, language),
    )


__all__ = [
    "classify_longitudinal_personalization",
    "resolve_longitudinal_personalization_from_context",
]
