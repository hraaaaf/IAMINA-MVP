"""Evidence-gated projection of analytical glucose data.

SQL analytics may compute descriptive statistics from every recorded glucose row.
That does not make every result eligible for normative CGM interpretation. This
module is the single diabetes-owned boundary that converts raw analytics into
patient/LLM-facing metric authority.
"""
from __future__ import annotations

from dataclasses import replace

from diabetes.services.clinical.cgm_eligibility import assess_cgm_sufficiency
from diabetes.services.clinical.evidence_registry import evidence_for_kpi
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


_NORMATIVE_CGM_FIELDS = (
    "cv_pct",
    "tir_pct",
    "tar_pct",
    "tbr_pct",
    "gmi",
    "gri",
    "gri_zone",
    "gri_label",
    "tbr_level2_pct",
    "tbr_level1_pct",
    "tar_level1_pct",
    "tar_level2_pct",
)


def guard_normative_kpis(kpis: AnalyticalKPIs) -> AnalyticalKPIs:
    """Return a KPI snapshot safe for normative clinical consumers.

    Today the ingestion contract cannot prove sensor wear-time/cadence, so CGM
    metrics fail closed. Descriptive mean/SD and record counts remain available.
    A future CGM-ingestion LOT may unlock these fields only through
    ``assess_cgm_sufficiency``.
    """
    if assess_cgm_sufficiency(kpis).verified:
        return kpis
    return replace(
        kpis,
        **{field: None for field in _NORMATIVE_CGM_FIELDS},
    )


def project_public_kpis(kpis: AnalyticalKPIs) -> dict[str, object]:
    """Build the stable patient/LLM-facing KPI projection.

    ``recorded_*`` values are explicitly descriptive fractions/statistics of the
    rows available to IAmina. They are not CGM Time in/Above/Below Range and do
    not receive population-target judgements without verified CGM sufficiency.
    """
    sufficiency = assess_cgm_sufficiency(kpis)
    guarded = guard_normative_kpis(kpis)
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
        "gmi_confidence": guarded.gmi_confidence if sufficiency.verified else None,
        "gmi_basis": guarded.gmi_basis if sufficiency.verified else "couverture CGM non vérifiée",
        "log_count": kpis.log_count,
        "days_with_data": kpis.days_with_data,
        "has_sufficient_data": kpis.has_sufficient_data,
        "recorded_cv_pct": kpis.cv_pct,
        "recorded_range_pct": kpis.tir_pct,
        "recorded_above_pct": kpis.tar_pct,
        "recorded_below_pct": kpis.tbr_pct,
        "cgm_row_fraction_pct": kpis.cgm_active_pct,
        "cgm_sufficiency": sufficiency.to_metadata(),
        "evidence": evidence,
    }
