"""Governed ACTIVITY_CONTEXT advice family.

This resolver interprets only explicitly recorded activity context already present
in the deterministic domain context. It never infers causality, prescribes
exercise, compensates food/glucose with activity, or changes treatment.
"""
from __future__ import annotations

import re

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.domain_context import DomainContext

_ACTIVITY_RE = re.compile(
    r"(?:\b(?:sport|exercise|exercice|activité|activite|marche|marcher|walk|"
    r"workout|training|entraînement|entrainement)\b|(?:رياضة|تمرين|مشي|نشاط))",
    re.IGNORECASE,
)
_GLUCOSE_RE = re.compile(
    r"(?:\b(?:glyc[eé]mi(?:e|que)|glucose|sucre|sugar|cgm|hypo)\b|"
    r"(?:سكر|جلوكوز|هبوط))",
    re.IGNORECASE,
)
_CONTEXT_RE = re.compile(
    r"(?:\b(?:effet|effect|impact|après|apres|after|avant|before|avec|with|"
    r"lié|lie|related|cause|causé|caused|baisse|lower|monte|rise|change)\b|"
    r"(?:بعد|قبل|مع|تأثير|سبب))",
    re.IGNORECASE,
)

_EVIDENCE = (
    "rule.pattern.low-with-recorded-activity.v1",
    "rule.personal-response.repetition.v1",
)
_FORBIDDEN = (
    "infer_activity_causality",
    "prescribe_exercise",
    "recommend_compensatory_activity",
    "calculate_insulin_dose",
    "change_treatment",
    "diagnose_from_activity",
)
_LIMITATIONS = (
    "explicit_recorded_activity_context_only",
    "temporal_or_longitudinal_association_does_not_establish_causality",
    "no_exercise_prescription_or_treatment_change",
)


def classify_activity_context(message: str) -> bool:
    text = (message or "").strip()
    if not text or not _ACTIVITY_RE.search(text):
        return False
    return bool(_GLUCOSE_RE.search(text) or _CONTEXT_RE.search(text))


def _has_activity_context(context: DomainContext) -> bool:
    if not context.has_sufficient_data:
        return False
    haystack = " ".join(
        [
            context.pivot_text or "",
            *(str(value) for value in context.detected_patterns),
            *(str(value) for value in context.insights),
        ]
    ).lower()
    return any(
        token in haystack
        for token in (
            "activity",
            "exercise",
            "exercised",
            "low_glucose_with_recorded_activity",
            "context:activity",
            "activité",
            "activite",
            "رياضة",
        )
    )


def _reply(language: str, *, sufficient: bool) -> str:
    if language.startswith("ar"):
        if sufficient:
            return (
                "المعطيات المسجلة تبيّن تزامناً وصفياً بين النشاط وقياسات السكر. "
                "هذا لا يثبت أن النشاط هو السبب، ولا يبرر تغيير العلاج أو جرعة الأنسولين."
            )
        return (
            "ما كايناش معطيات مسجلة كافية باش نفسر العلاقة بين النشاط وقياسات السكر. "
            "نقدر نفسر غير السياق المسجل، بلا افتراض السبب ولا تغيير العلاج."
        )
    if language.startswith("en"):
        if sufficient:
            return (
                "The recorded data show a descriptive association between activity and "
                "glucose readings. This does not establish that activity caused the change "
                "and does not justify changing treatment or insulin dose."
            )
        return (
            "There is not enough explicitly recorded activity context to interpret an "
            "activity-glucose association. I can only describe recorded context without "
            "inferring causality or changing treatment."
        )
    if sufficient:
        return (
            "Les données enregistrées montrent une association descriptive entre l’activité "
            "et les mesures de glycémie. Cela ne prouve pas que l’activité en est la cause "
            "et ne justifie ni modification du traitement ni dose d’insuline."
        )
    return (
        "Il n’y a pas assez de contexte d’activité explicitement enregistré pour interpréter "
        "une association activité-glycémie. Je peux seulement décrire le contexte enregistré, "
        "sans inférer de causalité ni modifier le traitement."
    )


def resolve_activity_context(
    message: str,
    context: DomainContext,
    *,
    language: str = "fr",
) -> AdviceResolution | None:
    if not classify_activity_context(message):
        return None

    sufficient = _has_activity_context(context)
    if sufficient:
        decision = AdviceDecision(
            intent="activity_context",
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.activity.descriptive_context",
            rule_version="1",
            allowed_actions=(
                "explain_recorded_activity_context",
                "describe_activity_glucose_association",
            ),
            forbidden_actions=_FORBIDDEN,
            evidence_refs=_EVIDENCE,
            limitations=_LIMITATIONS,
            language=language,
        )
    else:
        decision = AdviceDecision(
            intent="activity_context",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.activity.insufficient_data",
            rule_version="1",
            allowed_actions=("explain_available_activity_context",),
            forbidden_actions=_FORBIDDEN,
            evidence_refs=_EVIDENCE,
            required_facts=("explicit_recorded_activity_context",),
            missing_facts=("sufficient_recorded_activity_context",),
            limitations=_LIMITATIONS,
            language=language,
        )

    return AdviceResolution(decision=decision, reply=_reply(language, sufficient=sufficient))


__all__ = [
    "classify_activity_context",
    "resolve_activity_context",
]
