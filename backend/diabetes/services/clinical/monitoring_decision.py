"""Governed MONITORING_INTERPRETATION advice family.

This first CI-6 slice is deliberately descriptive. It can explain already
computed monitoring summaries but cannot convert them into diagnosis, treatment
optimization, insulin dosing, or a claim that glucose is clinically
better/worse. Missing or insufficient monitoring context fails closed.
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

_MONITORING_METRIC_RE = re.compile(
    r"(?:\b(?:tir|time in range|temps dans la cible|temps dans la plage|"
    r"glyc[eé]mie moyenne|average glucose|variabilit[eé] glyc[eé]mique|"
    r"glucose variability)\b|(?:الوقت في النطاق|متوسط السكر|تقلب السكر))",
    re.IGNORECASE,
)
_GLUCOSE_RE = re.compile(
    r"(?:\b(?:glyc[eé]mi(?:e|que)|glucose|sucre|sugar|cgm)\b|(?:سكر|جلوكوز))",
    re.IGNORECASE,
)
_TREND_RE = re.compile(
    r"(?:\b(?:tendance|trend|évolution|evolution|semaine|week|compare|comparer|cv)\b"
    r"|(?:اتجاه|أسبوع|اسبوع|قارن))",
    re.IGNORECASE,
)

_EVIDENCE = (
    "rule.metric.recorded-range-fractions.v1",
    "rule.metric.recorded-glucose-stats.v1",
    "rule.metric.week-over-week-recorded-range.v1",
)

_FORBIDDEN = (
    "diagnose_from_monitoring",
    "declare_clinical_improvement_or_deterioration",
    "calculate_insulin_dose",
    "change_treatment",
    "recommend_compensatory_activity",
)

_LIMITATIONS = (
    "descriptive_monitoring_only",
    "recorded_readings_are_not_automatically_validated_cgm_time_metrics",
    "no_diagnosis_or_treatment_change",
)


def classify_monitoring_interpretation(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False
    if _MONITORING_METRIC_RE.search(text):
        return True
    return bool(_GLUCOSE_RE.search(text) and _TREND_RE.search(text))


def _has_monitoring_data(context: DomainContext) -> bool:
    if not context.has_sufficient_data:
        return False
    summary = context.kpi_summary or {}
    return any(
        summary.get(key) is not None
        for key in ("avg_glucose", "tir_pct", "cv_pct", "tar_pct", "tbr_pct")
    ) or bool(context.trend)


def _reply(context: DomainContext, language: str) -> str:
    if language == "en":
        return (
            "I can explain the monitoring summary descriptively: the recorded values "
            "and their trend can be compared over the available window, but that does "
            "not by itself prove clinical improvement or deterioration and does not "
            "justify changing treatment."
        )
    if language == "ar-MA":
        return (
            "نقدر نفسر ليك ملخص المراقبة بشكل وصفي: القياسات المسجلة والتوجه ديالها "
            "نقدرو نقارنوهم فالفترة المتوفرة، ولكن هاد الشي بوحدو ما كيثبتش تحسن ولا "
            "تدهور سريري وما كيبررش تبديل العلاج."
        )
    return (
        "Je peux interpréter le résumé de suivi de façon descriptive : les valeurs "
        "enregistrées et leur tendance peuvent être comparées sur la fenêtre disponible, "
        "mais cela ne prouve pas à lui seul une amélioration ou une dégradation clinique "
        "et ne justifie pas de modifier le traitement."
    )


def _missing_reply(language: str) -> str:
    if language == "en":
        return (
            "I do not have enough verified monitoring data to interpret this safely. "
            "I can explain the available measurements, but I will not infer a clinical "
            "trend or suggest a treatment change from missing data."
        )
    if language == "ar-MA":
        return (
            "ما عنديش معطيات مراقبة كافية ومتحققة باش نفسر هاد الشي بأمان. "
            "نقدر نفسر القياسات المتوفرة، ولكن ما غاديش نستنتج توجه سريري ولا نقترح "
            "تبديل العلاج من معطيات ناقصة."
        )
    return (
        "Je n’ai pas assez de données de suivi vérifiées pour interpréter cela de façon "
        "sûre. Je peux expliquer les mesures disponibles, mais je ne déduirai pas une "
        "tendance clinique ni un changement de traitement à partir de données manquantes."
    )


def resolve_monitoring_interpretation(
    message: str,
    context: DomainContext,
    *,
    language: str = "fr",
) -> AdviceResolution | None:
    if not classify_monitoring_interpretation(message):
        return None

    if not _has_monitoring_data(context):
        decision = AdviceDecision(
            intent="monitoring_interpretation",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.monitoring.insufficient_data",
            rule_version="1",
            allowed_actions=("explain_available_monitoring_data",),
            forbidden_actions=_FORBIDDEN,
            required_facts=("sufficient_monitoring_window",),
            missing_facts=("sufficient_monitoring_window",),
            evidence_refs=_EVIDENCE,
            limitations=_LIMITATIONS + ("insufficient_monitoring_data",),
            language=language,
        )
        return AdviceResolution(decision=decision, reply=_missing_reply(language))

    decision = AdviceDecision(
        intent="monitoring_interpretation",
        authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
        decision=AdviceDisposition.CONSTRAIN,
        rule_id="diabetes.monitoring.descriptive_interpretation",
        rule_version="1",
        allowed_actions=(
            "explain_recorded_monitoring_summary",
            "compare_descriptive_monitoring_trend",
        ),
        forbidden_actions=_FORBIDDEN,
        required_facts=("sufficient_monitoring_window",),
        evidence_refs=_EVIDENCE,
        limitations=_LIMITATIONS,
        language=language,
    )
    return AdviceResolution(decision=decision, reply=_reply(context, language))


__all__ = [
    "classify_monitoring_interpretation",
    "resolve_monitoring_interpretation",
]
