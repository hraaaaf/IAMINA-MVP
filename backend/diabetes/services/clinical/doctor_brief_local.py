"""V1-03: deterministic, non-prescriptive local consultation-summary copy.

No user observations, statistics, medical history or locale are routed to any
generative model by this formatter. Locale copy requires independent review
before clinical release; this is an engineering candidate only.
"""
from __future__ import annotations

from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


def _language(language: str) -> str:
    if language == "ar-MA":
        return "ar-MA"
    if language == "ar":
        return "ar"
    if language == "en" or language.startswith("en-"):
        return "en"
    return "fr"


def build_local_doctor_brief(
    kpis: AnalyticalKPIs, *, days: int, language: str
) -> dict[str, str]:
    """Create explanatory *recorded-data* copy without CGM target judgments.

    Deliberately use only counts and the descriptive recorded mean.
    Normative raw SQL TIR/CV/GMI must not be surfaced by this route.
    """
    locale = _language(language)
    if not kpis.has_sufficient_data:
        messages = {
            "fr": "Pas assez de mesures enregistrées pour préparer ce résumé.",
            "en": "Not enough recorded readings to prepare this summary.",
            "ar": "لا توجد قياسات مسجلة كافية لإعداد هذا الملخص.",
            "ar-MA": "ما كايناش قياسات مسجلة كافية باش نوجد هاد الملخص.",
        }
        return {"doctor_brief": "", "narrative": messages[locale], "key_insight": ""}

    count = kpis.log_count
    data_days = kpis.days_with_data
    mean = kpis.avg_glucose
    count_text = {
        "fr": f"{count} mesures enregistrées sur {data_days} jours.",
        "en": f"{count} recorded readings across {data_days} days.",
        "ar": f"{count} قياسًا مسجلًا خلال {data_days} أيام.",
        "ar-MA": f"{count} قياسات مسجلة فـ {data_days} أيام.",
    }[locale]
    notice = {
        "fr": (
            "Résumé descriptif des mesures enregistrées, sans diagnostic, "
            "interprétation CGM validée ni recommandation de traitement."
        ),
        "en": (
            "Recorded-data description only; no diagnosis, validated CGM "
            "interpretation or treatment recommendation."
        ),
        "ar": (
            "وصف للقياسات المسجلة فقط، دون تشخيص أو تفسير معتمد لبيانات CGM "
            "أو توصية علاجية."
        ),
        "ar-MA": (
            "غير وصف للقياسات المسجلة، ماشي تشخيص ولا تفسير CGM متحقق "
            "منو ولا نصيحة لتبديل العلاج."
        ),
    }[locale]
    mean_text = ""
    if mean is not None:
        formatted = f"{mean:.1f} mg/dL"
        mean_text = {
            "fr": f" Moyenne descriptive des valeurs enregistrées : {formatted}.",
            "en": f" Descriptive mean of recorded values: {formatted}.",
            "ar": f" المتوسط الوصفي للقياسات المسجلة: {formatted}.",
            "ar-MA": f" المتوسط الوصفي ديال القياسات المسجلة: {formatted}.",
        }[locale]
    return {
        "doctor_brief": f"{count_text}{mean_text} {notice}",
        "narrative": notice,
        "key_insight": count_text,
    }
