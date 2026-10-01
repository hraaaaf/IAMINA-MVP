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

_PERSONAL_DIABETES_RE = re.compile(
    r"(?:\b(?:mon|my)\s+(?:diab[eè]te|diabetes)\b|(?:سكري|السكري)\s+(?:ديالي|عندي))",
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


def _is_broad_personal_weekly_request(message: str) -> bool:
    text = (message or "").strip()
    return bool(
        text
        and _PERSONAL_DIABETES_RE.search(text)
        and _TREND_RE.search(text)
    )


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


def _missing_reply(context: DomainContext, language: str) -> str:
    summary = context.kpi_summary or {}
    log_count = summary.get("log_count")
    days_with_data = summary.get("days_with_data")

    if isinstance(log_count, int) and log_count == 0:
        if language == "en":
            return (
                "I have no recorded glucose measurements in this window, so I cannot "
                "calculate a glucose average, TIR, GMI, or trend without inventing data."
            )
        if language == "ar-MA":
            return (
                "ما عنديش حتى قياس ديال السكر مسجل فهاد الفترة، لذلك ما نقدرش نحسب "
                "المتوسط ولا TIR ولا GMI ولا التوجه بلا ما نخترع معطيات."
            )
        return (
            "Je n’ai aucune glycémie enregistrée sur cette fenêtre. Je ne peux donc pas "
            "calculer une glycémie moyenne, un TIR, un GMI ou une tendance sans inventer "
            "de données."
        )

    if isinstance(log_count, int) and isinstance(days_with_data, int):
        if language == "en":
            return (
                f"I have {log_count} recorded measurements across {days_with_data} days, "
                "which is not enough verified monitoring data for a reliable interpretation. "
                "I will not infer a trend or treatment change from missing data."
            )
        if language == "ar-MA":
            return (
                f"عندي {log_count} قياسات مسجلة على {days_with_data} أيام، ولكن هاد المعطيات "
                "ما كافياش باش نفسر التوجه بأمان. ما غاديش نستنتج توجه سريري ولا تبديل العلاج."
            )
        return (
            f"Je dispose de {log_count} mesures réparties sur {days_with_data} jours, "
            "ce qui n’est pas assez pour une interprétation fiable du suivi. Je ne "
            "déduirai pas une tendance clinique ni un changement de traitement à partir "
            "de données manquantes."
        )

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
    metric_or_trend_request = classify_monitoring_interpretation(message)
    broad_weekly_request = _is_broad_personal_weekly_request(message)
    if not metric_or_trend_request and not broad_weekly_request:
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
        return AdviceResolution(decision=decision, reply=_missing_reply(context, language))

    # Broad weekly questions use the approved clinical narrator when data exist,
    # preserving actual seven-day context instead of generic deterministic copy.
    if broad_weekly_request and not metric_or_trend_request:
        return None

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
