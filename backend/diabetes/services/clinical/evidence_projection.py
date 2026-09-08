"""Evidence-gated projection of analytical glucose data.

SQL analytics may compute descriptive statistics from every recorded glucose row.
That does not make every result eligible for normative CGM interpretation. This
module is the single diabetes-owned boundary that converts raw analytics into
patient/LLM-facing metric authority.
"""

from diabetes.services.clinical.cgm_analytics import VerifiedCgmMetrics
from diabetes.services.clinical.cgm_eligibility import (
    CgmWindowSufficiency,
    assess_cgm_sufficiency,
)
from diabetes.services.clinical.evidence_registry import ClinicalAuthority, evidence_for_kpi
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs

_NORMATIVE_CGM_FIELD_EVIDENCE = {
    "cv_pct": "cv_pct",
    "tir_pct": "tir_pct",
    "tar_pct": "tar_pct",
    "tbr_pct": "tbr_pct",
    "gmi": "gmi",
    "gri": "gri",
    "gri_zone": "gri",
    "gri_label": "gri",
    "tbr_level2_pct": "tbr_level2_pct",
    "tbr_level1_pct": "tbr_level1_pct",
    "tar_level1_pct": "tar_level1_pct",
    "tar_level2_pct": "tar_level2_pct",
}

_PROMOTED_CGM_FIELDS = {
    "cv_pct": "cv_pct",
    "tir_pct": "tir_pct",
    "tar_pct": "tar_pct",
    "tbr_pct": "tbr_pct",
}


def _sufficiency_metadata(
    kpis: AnalyticalKPIs,
    cgm_window: CgmWindowSufficiency | None,
) -> tuple[bool, dict[str, object]]:
    if cgm_window is not None:
        return cgm_window.verified, cgm_window.to_metadata()
    legacy = assess_cgm_sufficiency(kpis)
    return legacy.verified, legacy.to_metadata()


def guard_normative_kpis(
    kpis: AnalyticalKPIs,
    *,
    cgm_window: CgmWindowSufficiency | None = None,
    cgm_metrics: VerifiedCgmMetrics | None = None,
) -> AnalyticalKPIs:
    """Return a KPI snapshot safe for normative clinical consumers.

    A normative CGM field is released only when three independent gates pass:
    persisted CGM sufficiency is verified, the evidence registry marks the rule
    as ``GOVERNED_RULE``, and the value was recomputed from session-linked CGM
    readings rather than mixed/manual ``LogEntry`` rows. Candidate rules remain
    fail-closed even when sufficiency is valid.
    """
    verified, _ = _sufficiency_metadata(kpis, cgm_window)
    guarded_values = vars(kpis).copy()

    for field, metric_name in _NORMATIVE_CGM_FIELD_EVIDENCE.items():
        evidence = evidence_for_kpi(metric_name)
        allowed = verified and evidence.clinical_authority == ClinicalAuthority.GOVERNED_RULE
        source_field = _PROMOTED_CGM_FIELDS.get(field)
        if allowed and source_field and cgm_metrics is not None:
            guarded_values[field] = getattr(cgm_metrics, source_field)
        else:
            guarded_values[field] = None

    return AnalyticalKPIs(**guarded_values)


def project_public_kpis(
    kpis: AnalyticalKPIs,
    *,
    cgm_window: CgmWindowSufficiency | None = None,
    cgm_metrics: VerifiedCgmMetrics | None = None,
) -> dict[str, object]:
    """Build the stable patient/LLM-facing KPI projection.

    ``recorded_*`` values are explicitly descriptive fractions/statistics of the
    rows available to IAmina. Promoted TIR/TAR/TBR/CV values, when present, come
    only from session-linked readings inside a verified CGM window.
    """
    cgm_verified, sufficiency = _sufficiency_metadata(kpis, cgm_window)
    guarded = guard_normative_kpis(
        kpis,
        cgm_window=cgm_window,
        cgm_metrics=cgm_metrics,
    )
    evidence = {
        name: evidence_for_kpi(name).to_metadata()
        for name in (
            "avg_glucose",
            "std_dev",
            "cv_pct",
            "tir_pct",
            "tar_pct",
            "tbr_pct",
            "gmi",
            "gri",
            "trend",
        )
    }
    return {
        "avg_glucose": guarded.avg_glucose,
        "std_dev": guarded.std_dev,
        "cv_pct": guarded.cv_pct,
        "tir_pct": guarded.tir_pct,
        "tar_pct": guarded.tar_pct,
        "tbr_pct": guarded.tbr_pct,
        "gmi": guarded.gmi,
        "gri": guarded.gri,
        "gri_zone": guarded.gri_zone,
        "gri_label_fr": guarded.gri_label,
        "gmi_confidence": guarded.gmi_confidence if guarded.gmi is not None else None,
        "gmi_basis": (
            guarded.gmi_basis
            if guarded.gmi is not None
            else (
                "couverture CGM non vérifiée"
                if not cgm_verified
                else "règle GMI non promue"
            )
        ),
        "log_count": kpis.log_count,
        "days_with_data": kpis.days_with_data,
        "has_sufficient_data": kpis.has_sufficient_data,
        "recorded_cv_pct": kpis.cv_pct,
        "recorded_range_pct": kpis.tir_pct,
        "recorded_above_pct": kpis.tar_pct,
        "recorded_below_pct": kpis.tbr_pct,
        "cgm_row_fraction_pct": kpis.cgm_active_pct,
        "cgm_sufficiency": sufficiency,
        "cgm_metric_reading_count": cgm_metrics.reading_count if cgm_metrics else 0,
        "evidence": evidence,
    }
