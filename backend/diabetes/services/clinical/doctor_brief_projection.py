"""CAL-12 deterministic and provenance-bound legacy Doctor Brief adapter.

Patient-visible narration is authored only from a fixed language template and
a verified, typed consultation-brief.v1 item. Never pass this envelope to an LLM,
do not infer CGM norms from manual rows, and never echo free-text clinical items.
The reviewer-facing numbers and sources are exactly those present in evidence.
"""

from __future__ import annotations

import math
from datetime import datetime

from core.contracts.truth import TruthKind
from diabetes.services.clinical.consultation_brief_assembler import (
    RECORDED_STATS_EVIDENCE_ID,
    RECORDED_STATS_SOURCE,
    SOURCE_ADAPTER_VERSION,
)
from diabetes.services.clinical.consultation_brief_contract import (
    CONSULTATION_BRIEF_SCHEMA_VERSION,
    ConsultationAuthority,
    ConsultationBriefEnvelope,
    ConsultationNarrationPolicy,
)

_COPY = {
    "fr": {
        "unavailable": "Résumé descriptif indisponible : données vérifiables insuffisantes.",
        "narrative": "Résumé des glycémies enregistrées et synchronisées sur la période sélectionnée.",
        "insight": "Moyenne descriptive des mesures, sans conclusion clinique ni analyse CGM.",
        "brief": "Moyenne des glycémies enregistrées : {value:.1f} mg/dL. Moyenne descriptive, non pondérée par la durée du capteur.",
    },
    "en": {
        "unavailable": "Descriptive summary unavailable: insufficient verifiable records.",
        "narrative": "Summary of synchronized recorded glucose measurements in the selected period.",
        "insight": "Recorded-sample average only; no diagnosis or CGM interpretation.",
        "brief": "Average of recorded glucose measurements: {value:.1f} mg/dL. Descriptive average, not sensor-time-weighted.",
    },
    "ar": {
        "unavailable": "الملخص الوصفي غير متاح لعدم كفاية القراءات القابلة للتحقق.",
        "narrative": "ملخص وصفي لقياسات الغلوكوز المسجلة والمتزامنة خلال الفترة المحددة.",
        "insight": "متوسط وصفي للقياسات، دون استنتاج تشخيصي أو تفسير لبيانات المراقبة المستمرة.",
        "brief": "متوسط قياسات الغلوكوز المسجلة: {value:.1f} mg/dL. متوسط وصفي غير موزون بمدة عمل المستشعر.",
    },
    "ar-MA": {
        "unavailable": "الملخص الوصفي ما متوفرش حيث المعطيات الموثوقة ما كافياش.",
        "narrative": "هادشي غير ملخص وصفي لقياسات السكر المسجلة والمتزامنة فهاد المدة.",
        "insight": "غير معدل ديال القياسات المسجلة، بلا تشخيص ولا تفسير CGM.",
        "brief": "معدل قياسات السكر المسجلة: {value:.1f} mg/dL. هاد المعدل وصفي وماشي موزون بمدة المستشعر.",
    },
}
_MISSING = ("no_authorized_recorded_average",)
_LIMITS = (
    "consultation_preparation_only",
    "no_diagnosis_or_treatment_authority",
    "not_cgm_time_weighted",
    "no_model_generated_clinical_claims",
)


def _language(language: str) -> str:
    if language in _COPY:
        return language
    if language.lower().startswith("ar"):
        return "ar"
    if language.lower().startswith("en"):
        return "en"
    return "fr"


def project_deterministic_doctor_brief(
    envelope: ConsultationBriefEnvelope | None,
    *,
    language: str,
    days: int,
    generated_at: datetime,
    sufficient_rows: bool,
) -> dict[str, object]:
    """Return model-free text + only one allowlisted, source-bound metric."""
    copy = _COPY[_language(language)]
    result: dict[str, object] = {
        "doctor_brief": "",
        "narrative": copy["unavailable"],
        "key_insight": "",
        "days": days,
        "generated_at": generated_at.isoformat(),
        "has_sufficient_data": False,
        "schema_version": CONSULTATION_BRIEF_SCHEMA_VERSION,
        "authority": ConsultationAuthority.REVIEW_SUPPORT_ONLY.value,
        "window_start": None,
        "window_end": None,
        "evidence": [],
        "missing_data": list(_MISSING),
        "limitations": list(_LIMITS),
    }
    if not sufficient_rows or not isinstance(envelope, ConsultationBriefEnvelope):
        return result
    if (
        envelope.authority is not ConsultationAuthority.REVIEW_SUPPORT_ONLY
        or envelope.narration_policy
        is not ConsultationNarrationPolicy.APPROVED_STRUCTURED_FIELDS_ONLY
    ):
        return result

    result["window_start"] = envelope.window_start.isoformat()
    result["window_end"] = envelope.window_end.isoformat()
    result["missing_data"] = list(envelope.missing_data)

    # The only authorized numeric claim is the governed, descriptive recorded
    # mean. Clinical Twin status, patient names, untrusted free text, TIR and GMI
    # are not eligible for interpolation in this legacy public response.
    matching = [
        item for item in envelope.items
        if item.key == "recorded_glucose.average_mg_dl"
    ]
    if len(matching) != 1:
        result["missing_data"].append(_MISSING[0])
        return result
    metric = matching[0]
    if (
        metric.truth_kind is not TruthKind.DETERMINISTIC_DERIVATION
        or metric.source != RECORDED_STATS_SOURCE
        or metric.source_version != SOURCE_ADAPTER_VERSION
        or metric.evidence_id != RECORDED_STATS_EVIDENCE_ID
        or metric.unit != "mg/dL"
        or type(metric.value) not in (int, float)
        or not math.isfinite(metric.value)
        or metric.value <= 0
        or not math.isclose(metric.value, round(metric.value, 1), abs_tol=1e-9)
    ):
        result["missing_data"].append(_MISSING[0])
        return result

    result["narrative"] = copy["narrative"]
    result["key_insight"] = copy["insight"]
    result["doctor_brief"] = copy["brief"].format(value=metric.value)
    result["has_sufficient_data"] = True
    result["evidence"] = [{
        "key": metric.key,
        "value": float(metric.value),
        "unit": metric.unit,
        "truth_kind": metric.truth_kind.value,
        "source": metric.source,
        "source_version": metric.source_version,
        "evidence_id": metric.evidence_id,
        "window_start": result["window_start"],
        "window_end": result["window_end"],
        "limitations": list(metric.limitations),
    }]
    result["limitations"] = list(dict.fromkeys(_LIMITS + envelope.limitations))
    return result
