"""Versioned evidence registry for diabetes clinical analytics and observations.

The registry is deliberately code-first and immutable. Clinical definitions are
release-governed code, not mutable patient data. A database table would create a
second runtime authority that could change independently of review/CI.

External evidence uses the three maturity classes defined by the diabetes
evidence-intelligence skill. IAmina-owned deterministic rules use the separate
``INTERNAL_GOVERNED_RULE`` maturity and may reference external source records.
Regulatory status is orthogonal to evidence maturity.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class RecordKind(StrEnum):
    SOURCE = "source"
    RULE = "rule"


class EvidenceMaturity(StrEnum):
    STANDARD_OF_CARE = "standard_of_care"
    EMERGING_EVIDENCE = "emerging_evidence"
    INVESTIGATIONAL = "investigational"
    INTERNAL_GOVERNED_RULE = "internal_governed_rule"


class FinalityStatus(StrEnum):
    FINAL = "final"
    DRAFT = "draft"
    VERSIONED_PRODUCT_RULE = "versioned_product_rule"


class ClinicalAuthority(StrEnum):
    NONE = "none"
    NARRATIVE_ONLY = "narrative_only"
    GOVERNED_RULE_CANDIDATE = "governed_rule_candidate"
    GOVERNED_RULE = "governed_rule"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    kind: RecordKind
    topic: str
    claim_or_rule: str
    evidence_maturity: EvidenceMaturity
    source_organization: str
    source_title: str
    identifier: str
    publication_or_version_date: str
    finality_status: FinalityStatus
    population: tuple[str, ...]
    modality: tuple[str, ...]
    jurisdiction: str
    regulatory_status: str
    reviewed_at: str
    clinical_authority: ClinicalAuthority
    limitations: str
    supporting_evidence_ids: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    superseded_by: tuple[str, ...] = ()

    @property
    def supersession_state(self) -> str:
        return "superseded" if self.superseded_by else "current"

    def to_metadata(self) -> dict[str, object]:
        """Return JSON-safe provenance metadata for clinical output contracts."""
        return {
            "evidence_id": self.evidence_id,
            "evidence_maturity": self.evidence_maturity.value,
            "source_organization": self.source_organization,
            "source_title": self.source_title,
            "identifier": self.identifier,
            "publication_or_version_date": self.publication_or_version_date,
            "finality_status": self.finality_status.value,
            "population": list(self.population),
            "modality": list(self.modality),
            "jurisdiction": self.jurisdiction,
            "regulatory_status": self.regulatory_status,
            "reviewed_at": self.reviewed_at,
            "clinical_authority": self.clinical_authority.value,
            "supersession_state": self.supersession_state,
            "limitations": self.limitations,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
        }


REVIEWED_AT = "2026-08-12"

# External source records -----------------------------------------------------

_SOURCE_ADA_2026_SECTION6 = EvidenceRecord(
    evidence_id="source.ada.2026.section6",
    kind=RecordKind.SOURCE,
    topic="glycemic assessment and hypoglycemia",
    claim_or_rule=(
        "Current final ADA 2026 glycemic-assessment framework, including CGM "
        "metrics, population-specific targets, and level 1/2 hypoglycemia definitions."
    ),
    evidence_maturity=EvidenceMaturity.STANDARD_OF_CARE,
    source_organization="American Diabetes Association",
    source_title=(
        "Standards of Care in Diabetes—2026, Section 6: Glycemic Goals, "
        "Hypoglycemia, and Hyperglycemic Crises"
    ),
    identifier="DOI 10.2337/dc26-S006",
    publication_or_version_date="2026",
    finality_status=FinalityStatus.FINAL,
    population=(
        "people with diabetes; target applicability varies by age, pregnancy, "
        "comorbidity and individualized treatment goals",
    ),
    modality=("BGM", "CGM with metric-specific data sufficiency"),
    jurisdiction="international clinical guidance; local regulation still applies",
    regulatory_status="not_applicable",
    reviewed_at=REVIEWED_AT,
    clinical_authority=ClinicalAuthority.NONE,
    limitations=(
        "Population targets are not autonomous patient instructions. CGM target "
        "interpretation requires valid CGM data sufficiency and population applicability."
    ),
)

_SOURCE_GMI_2018 = EvidenceRecord(
    evidence_id="source.bergenstal.2018.gmi",
    kind=RecordKind.SOURCE,
    topic="glucose management indicator",
    claim_or_rule=(
        "GMI (%) = 3.31 + 0.02392 × mean sensor glucose (mg/dL), developed from CGM data."
    ),
    evidence_maturity=EvidenceMaturity.STANDARD_OF_CARE,
    source_organization="Diabetes Care / American Diabetes Association",
    source_title=(
        "Glucose Management Indicator (GMI): A New Term for Estimating A1C "
        "From Continuous Glucose Monitoring"
    ),
    identifier="DOI 10.2337/dc18-1581; PMID 30224348",
    publication_or_version_date="2018-09-17",
    finality_status=FinalityStatus.FINAL,
    population=("people with diabetes represented in the CGM derivation cohorts",),
    modality=("CGM",),
    jurisdiction="not jurisdiction-specific",
    regulatory_status="not_applicable",
    reviewed_at=REVIEWED_AT,
    clinical_authority=ClinicalAuthority.NONE,
    limitations=(
        "GMI is CGM-derived and is not laboratory A1C. Individual discordance with "
        "laboratory A1C can be clinically meaningful."
    ),
    supporting_evidence_ids=("source.ada.2026.section6",),
)

_SOURCE_PHNH_2025 = EvidenceRecord(
    evidence_id="source.gonzalez-vidal.2025.phnh",
    kind=RecordKind.SOURCE,
    topic="post-hypoglycemic nocturnal hyperglycemia",
    claim_or_rule=(
        "Observational CGM study of nocturnal hypoglycemia followed by later "
        "hyperglycemia in adults with type 1 diabetes."
    ),
    evidence_maturity=EvidenceMaturity.EMERGING_EVIDENCE,
    source_organization="Peer-reviewed observational study",
    source_title=(
        "Post-hypoglycemic nocturnal hyperglycemia in type 1 diabetes: "
        "the Somogyi hypothesis revisited"
    ),
    identifier="DOI 10.1007/s42000-025-00680-0; PMID 40465171",
    publication_or_version_date="2025",
    finality_status=FinalityStatus.FINAL,
    population=("adults with type 1 diabetes in the published study",),
    modality=("FreeStyle Libre 2 CGM",),
    jurisdiction="study population; not jurisdiction-specific guidance",
    regulatory_status="not_applicable",
    reviewed_at=REVIEWED_AT,
    clinical_authority=ClinicalAuthority.NONE,
    limitations=(
        "Observational association; does not diagnose a mechanism and must not "
        "be generalized to unsupported populations or used for treatment advice."
    ),
)

_SOURCE_GRI_2026 = EvidenceRecord(
    evidence_id="source.gri.2026.consensus",
    kind=RecordKind.SOURCE,
    topic="glycemia risk index",
    claim_or_rule="2026 consensus report on GRI use in clinical practice and research.",
    evidence_maturity=EvidenceMaturity.EMERGING_EVIDENCE,
    source_organization="Diabetes Technology Society expert consensus",
    source_title="Integrating the Glycemia Risk Index Into Clinical Practice and Research",
    identifier="DOI 10.1177/19322968261432498; PMID 41793701",
    publication_or_version_date="2026-03-07",
    finality_status=FinalityStatus.FINAL,
    population=("people with diabetes using CGM; population applicability must be checked",),
    modality=("CGM",),
    jurisdiction="not jurisdiction-specific",
    regulatory_status="not_applicable",
    reviewed_at=REVIEWED_AT,
    clinical_authority=ClinicalAuthority.NONE,
    limitations=(
        "IAmina does not currently publish GRI because its LogEntry schema cannot "
        "prove CGM wear-time coverage. This source does not activate the metric."
    ),
)

# IAmina-owned deterministic rules -------------------------------------------

_INTERNAL_SOURCE_TITLE = "IAmina deterministic clinical contract v2026-08"
_INTERNAL_ID = "docs/MEDICAL_DATA_PLAN.md + release-governed runtime"


def _internal_rule(
    *,
    evidence_id: str,
    topic: str,
    claim_or_rule: str,
    population: tuple[str, ...],
    modality: tuple[str, ...],
    limitations: str,
    supporting: tuple[str, ...] = (),
    authority: ClinicalAuthority = ClinicalAuthority.GOVERNED_RULE,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        kind=RecordKind.RULE,
        topic=topic,
        claim_or_rule=claim_or_rule,
        evidence_maturity=EvidenceMaturity.INTERNAL_GOVERNED_RULE,
        source_organization="IAmina",
        source_title=_INTERNAL_SOURCE_TITLE,
        identifier=_INTERNAL_ID,
        publication_or_version_date="2026-08",
        finality_status=FinalityStatus.VERSIONED_PRODUCT_RULE,
        population=population,
        modality=modality,
        jurisdiction="product rule; external clinical/regulatory applicability checked separately",
        regulatory_status="not_applicable",
        reviewed_at=REVIEWED_AT,
        clinical_authority=authority,
        limitations=limitations,
        supporting_evidence_ids=supporting,
    )


_RULE_RECORDED_STATS = _internal_rule(
    evidence_id="rule.metric.recorded-glucose-stats.v1",
    topic="descriptive glucose statistics",
    claim_or_rule="Compute arithmetic mean, sample standard deviation and CV from recorded glucose rows.",
    population=("patients with recorded glucose values",),
    modality=("manual", "voice", "CGM provenance", "imported glucose"),
    limitations=(
        "These are descriptive statistics of recorded rows. They do not prove CGM "
        "wear coverage, and CV must not receive a normative CGM stability label unless "
        "a separate validated CGM sufficiency contract is satisfied."
    ),
)

_RULE_RECORDED_RANGES = _internal_rule(
    evidence_id="rule.metric.recorded-range-fractions.v1",
    topic="recorded glucose range fractions",
    claim_or_rule=(
        "Compute fractions of recorded glucose rows within/below/above the selected range; "
        "default boundaries are 70–180 mg/dL."
    ),
    population=("patients with recorded glucose values",),
    modality=("mixed recorded glucose rows",),
    limitations=(
        "Without verified CGM wear-time, these values are fractions of recorded readings, "
        "not validated CGM Time in/Above/Below Range metrics or population target assessment."
    ),
    supporting=("source.ada.2026.section6",),
)

_RULE_GMI = _internal_rule(
    evidence_id="rule.metric.gmi-cgm.v1",
    topic="glucose management indicator",
    claim_or_rule=(
        "Use the Bergenstal GMI equation only when CGM modality and sufficient CGM "
        "coverage are independently verified."
    ),
    population=("people with diabetes for whom GMI is applicable",),
    modality=("CGM with verified sufficiency",),
    limitations=(
        "The current LogEntry schema records only source provenance and cannot prove "
        "wear-time/cadence coverage. Patient-facing GMI authority therefore fails closed "
        "until a real CGM coverage contract is available. GMI is not laboratory A1C."
    ),
    supporting=("source.bergenstal.2018.gmi", "source.ada.2026.section6"),
)

_RULE_CGM_VARIABILITY = _internal_rule(
    evidence_id="rule.pattern.cgm-high-variability.v1",
    topic="CGM glucose variability",
    claim_or_rule=(
        "Surface CV above the ADA general CGM reference only after validated CGM "
        "data sufficiency and population applicability."
    ),
    population=("applicable nonpregnant diabetes populations; special populations require review",),
    modality=("CGM with verified sufficiency",),
    limitations=(
        "`source='cgm'` row fraction is not sensor wear-time. The current schema cannot "
        "prove the required CGM sufficiency, so normative surfacing must fail closed."
    ),
    supporting=("source.ada.2026.section6",),
)

_RULE_GRI = _internal_rule(
    evidence_id="rule.metric.gri.v1",
    topic="glycemia risk index",
    claim_or_rule=(
        "Retain the normative GRI formula for a future validated-CGM path but do not "
        "publish GRI without verified CGM wear-time coverage."
    ),
    population=("people with diabetes when the GRI evidence is applicable",),
    modality=("CGM with verified sufficiency",),
    limitations="Current runtime intentionally returns GRI as null because valid wear-time is unproven.",
    supporting=("source.gri.2026.consensus",),
    authority=ClinicalAuthority.GOVERNED_RULE_CANDIDATE,
)

_RULE_AGP = _internal_rule(
    evidence_id="rule.metric.agp-hourly-profile.v1",
    topic="hourly descriptive glucose profile",
    claim_or_rule="Compute hourly mean and p5/p25/p50/p75/p95 from available recorded glucose rows.",
    population=("patients with recorded glucose values",),
    modality=("mixed recorded glucose rows",),
    limitations=(
        "This implementation is a descriptive hourly profile from available rows. It must "
        "not be represented as a validated standardized AGP report without a CGM coverage contract."
    ),
)

_RULE_TREND = _internal_rule(
    evidence_id="rule.metric.week-over-week-recorded-range.v1",
    topic="week-over-week recorded glucose trend",
    claim_or_rule=(
        "Compare the fraction of recorded readings inside the configured range between "
        "two seven-day windows; ±3 percentage points is the product display deadband."
    ),
    population=("patients with recorded glucose values",),
    modality=("mixed recorded glucose rows",),
    limitations=(
        "Direction is a product descriptive trend, not a validated clinical deterioration "
        "or improvement threshold and not a CGM TIR trend without verified coverage."
    ),
)

_RULE_HYPO_ALERTS = _internal_rule(
    evidence_id="rule.alert.hypoglycemia.v1",
    topic="hypoglycemia safety alerts",
    claim_or_rule=(
        "Use <70 mg/dL as level-1 low-glucose warning and <54 mg/dL as level-2 "
        "clinically significant low-glucose emergency trigger in the deterministic safety layer."
    ),
    population=("people with diabetes; emergency context remains individualized",),
    modality=("single glucose reading",),
    limitations=(
        "A glucose threshold alone is not a complete diagnosis. Emergency messaging and "
        "local contact resources remain governed by the shared deterministic safety layer."
    ),
    supporting=("source.ada.2026.section6",),
)

_RULE_HYPER_ALERTS = _internal_rule(
    evidence_id="rule.alert.hyperglycemia-product.v1",
    topic="conservative hyperglycemia product alerts",
    claim_or_rule=(
        "IAmina product rule: >300 mg/dL triggers critical escalation; repeated >250 mg/dL "
        "triggers a warning. These are conservative product-safety thresholds, not diagnostic criteria."
    ),
    population=("patients logging glucose values",),
    modality=("single/recent recorded glucose readings",),
    limitations=(
        "Internal safety rule; do not present 250/300 mg/dL as universal guideline emergency "
        "or diagnostic thresholds. Symptoms, ketones and clinical context can change urgency."
    ),
)

_RULE_MORNING_NIGHT = _internal_rule(
    evidence_id="rule.pattern.morning-night-difference.v1",
    topic="morning versus nighttime glucose",
    claim_or_rule="Surface repeated descriptive morning/night glucose differences under the coded product criteria.",
    population=("patients with sufficient timestamped glucose observations",),
    modality=("recorded glucose rows",),
    limitations="Descriptive chronology only; it does not diagnose dawn phenomenon or establish cause.",
)

_RULE_ACTIVITY_LOW = _internal_rule(
    evidence_id="rule.pattern.low-with-recorded-activity.v1",
    topic="low glucose with explicitly recorded activity",
    claim_or_rule=(
        "Surface repeated <70 mg/dL readings on days where activity was explicitly recorded."
    ),
    population=("patients with explicit activity context and glucose records",),
    modality=("recorded glucose + explicit patient activity context",),
    limitations="Temporal co-occurrence only; activity is not asserted to be the cause.",
    supporting=("source.ada.2026.section6",),
)

_RULE_NIGHT_LOW_MORNING_HIGH = _internal_rule(
    evidence_id="rule.pattern.night-low-later-morning-high.v1",
    topic="night low followed by later morning high",
    claim_or_rule=(
        "Surface a repeated CGM chronology of nighttime low readings followed by later "
        "morning high readings without naming or diagnosing a mechanism."
    ),
    population=("patients with applicable CGM observations; published support was adults with type 1 diabetes",),
    modality=("CGM provenance with explicit timestamps",),
    limitations=(
        "The supporting study is observational and population-limited. The rule is chronology-only, "
        "not a Somogyi diagnosis and not treatment advice."
    ),
    supporting=("source.gonzalez-vidal.2025.phnh",),
    authority=ClinicalAuthority.NARRATIVE_ONLY,
)

_RULE_CONTEXT = _internal_rule(
    evidence_id="rule.pattern.explicit-context-observation.v1",
    topic="explicit lifestyle/context observation",
    claim_or_rule=(
        "Describe repeated glucose observations sharing an explicitly positive context against "
        "the whole-window descriptive median; no negative-control causal inference."
    ),
    population=("patients with explicit context fields and repeated glucose records",),
    modality=("recorded glucose + patient-entered context",),
    limitations="Product descriptive association only; currently excluded from the active summary/doctor detector set.",
    authority=ClinicalAuthority.NARRATIVE_ONLY,
)

_RULE_FOOD = _internal_rule(
    evidence_id="rule.pattern.food-text-observation.v1",
    topic="meal-text glucose observation",
    claim_or_rule="Describe repeated meal-text/post-meal observations under the coded product criteria.",
    population=("patients with explicit meal/post-meal records",),
    modality=("recorded glucose + patient-entered meal context",),
    limitations="Non-causal product observation; currently excluded from the active summary/doctor detector set.",
    authority=ClinicalAuthority.NARRATIVE_ONLY,
)

_RULE_PRE_POST_MEAL = _internal_rule(
    evidence_id="rule.pattern.explicit-pre-post-meal-rise.v1",
    topic="explicit pre/post-meal glucose rise",
    claim_or_rule=(
        "Describe repeated explicitly marked pre→post-meal rises within two hours under the coded product criteria."
    ),
    population=("patients with explicit pre/post-meal context",),
    modality=("recorded glucose + explicit pre/post-meal markers",),
    limitations="Descriptive product threshold; no cause or treatment conclusion. Not active in summary/doctor detector set.",
    authority=ClinicalAuthority.NARRATIVE_ONLY,
)

_RULE_PERSONAL_RESPONSE = _internal_rule(
    evidence_id="rule.personal-response.repetition.v1",
    topic="longitudinal personal response observations",
    claim_or_rule=(
        "Require at least three matching observations across at least two distinct days within "
        "a maximum 90-day window; evidence grade is a product repetition grade, not probability."
    ),
    population=("patients with explicit journal context and repeated glucose observations",),
    modality=("server-synced recorded glucose + explicit patient context",),
    limitations="Observed association only; no causality, prediction, diagnosis or treatment optimization.",
)


_RECORDS = (
    _SOURCE_ADA_2026_SECTION6,
    _SOURCE_GMI_2018,
    _SOURCE_PHNH_2025,
    _SOURCE_GRI_2026,
    _RULE_RECORDED_STATS,
    _RULE_RECORDED_RANGES,
    _RULE_GMI,
    _RULE_CGM_VARIABILITY,
    _RULE_GRI,
    _RULE_AGP,
    _RULE_TREND,
    _RULE_HYPO_ALERTS,
    _RULE_HYPER_ALERTS,
    _RULE_MORNING_NIGHT,
    _RULE_ACTIVITY_LOW,
    _RULE_NIGHT_LOW_MORNING_HIGH,
    _RULE_CONTEXT,
    _RULE_FOOD,
    _RULE_PRE_POST_MEAL,
    _RULE_PERSONAL_RESPONSE,
)

EVIDENCE_REGISTRY: Mapping[str, EvidenceRecord] = MappingProxyType(
    {record.evidence_id: record for record in _RECORDS}
)

KPI_EVIDENCE_IDS: Mapping[str, str] = MappingProxyType(
    {
        "avg_glucose": "rule.metric.recorded-glucose-stats.v1",
        "std_dev": "rule.metric.recorded-glucose-stats.v1",
        "cv_pct": "rule.metric.recorded-glucose-stats.v1",
        "tir_pct": "rule.metric.recorded-range-fractions.v1",
        "tar_pct": "rule.metric.recorded-range-fractions.v1",
        "tbr_pct": "rule.metric.recorded-range-fractions.v1",
        "tbr_level2_pct": "rule.metric.recorded-range-fractions.v1",
        "tbr_level1_pct": "rule.metric.recorded-range-fractions.v1",
        "tar_level1_pct": "rule.metric.recorded-range-fractions.v1",
        "tar_level2_pct": "rule.metric.recorded-range-fractions.v1",
        "gmi": "rule.metric.gmi-cgm.v1",
        "gri": "rule.metric.gri.v1",
        "agp_profile": "rule.metric.agp-hourly-profile.v1",
        "trend": "rule.metric.week-over-week-recorded-range.v1",
    }
)

PATTERN_EVIDENCE_IDS: Mapping[str, str] = MappingProxyType(
    {
        "MORNING_NIGHT_GLUCOSE_DIFFERENCE": "rule.pattern.morning-night-difference.v1",
        "LOW_GLUCOSE_WITH_RECORDED_ACTIVITY": "rule.pattern.low-with-recorded-activity.v1",
        "NIGHT_LOW_THEN_MORNING_HIGH": "rule.pattern.night-low-later-morning-high.v1",
        "CGM_HIGH_VARIABILITY": "rule.pattern.cgm-high-variability.v1",
        "GLUCOSE_WITH_RECORDED_STRESS": "rule.pattern.explicit-context-observation.v1",
        "GLUCOSE_WITH_RECORDED_POOR_SLEEP": "rule.pattern.explicit-context-observation.v1",
        "GLUCOSE_WITH_RECORDED_FATIGUE": "rule.pattern.explicit-context-observation.v1",
        "GLUCOSE_WITH_RECORDED_ILLNESS": "rule.pattern.explicit-context-observation.v1",
        "REPEATED_RECORDED_MEAL_WITH_HIGH_READINGS": "rule.pattern.food-text-observation.v1",
        "REPEATED_PRE_POST_MEAL_RISE": "rule.pattern.explicit-pre-post-meal-rise.v1",
    }
)

ALERT_EVIDENCE_IDS: Mapping[str, str] = MappingProxyType(
    {
        "hypoglycemia_level2": "rule.alert.hypoglycemia.v1",
        "hypoglycemia_level1": "rule.alert.hypoglycemia.v1",
        "hyperglycemia_critical": "rule.alert.hyperglycemia-product.v1",
        "hyperglycemia_repeated": "rule.alert.hyperglycemia-product.v1",
    }
)

PERSONAL_RESPONSE_EVIDENCE_ID = "rule.personal-response.repetition.v1"


def get_evidence(evidence_id: str) -> EvidenceRecord:
    """Fail closed on an unknown evidence ID."""
    try:
        return EVIDENCE_REGISTRY[evidence_id]
    except KeyError as exc:
        raise KeyError(f"Unknown diabetes evidence_id: {evidence_id}") from exc


def evidence_metadata(evidence_id: str) -> dict[str, object]:
    return get_evidence(evidence_id).to_metadata()


def evidence_for_kpi(metric_name: str) -> EvidenceRecord:
    try:
        evidence_id = KPI_EVIDENCE_IDS[metric_name]
    except KeyError as exc:
        raise KeyError(f"Unregistered diabetes KPI evidence: {metric_name}") from exc
    return get_evidence(evidence_id)


def evidence_for_pattern(pattern_code: str) -> EvidenceRecord:
    try:
        evidence_id = PATTERN_EVIDENCE_IDS[pattern_code]
    except KeyError as exc:
        raise KeyError(f"Unregistered diabetes pattern evidence: {pattern_code}") from exc
    return get_evidence(evidence_id)


def evidence_for_alert(alert_code: str) -> EvidenceRecord:
    try:
        evidence_id = ALERT_EVIDENCE_IDS[alert_code]
    except KeyError as exc:
        raise KeyError(f"Unregistered diabetes alert evidence: {alert_code}") from exc
    return get_evidence(evidence_id)


def validate_registry() -> tuple[str, ...]:
    """Return deterministic registry invariant violations."""
    errors: list[str] = []
    ids = [record.evidence_id for record in _RECORDS]
    if len(ids) != len(set(ids)):
        errors.append("duplicate evidence_id")

    for record in _RECORDS:
        if not record.population:
            errors.append(f"{record.evidence_id}: population missing")
        if not record.modality:
            errors.append(f"{record.evidence_id}: modality missing")
        if not record.reviewed_at:
            errors.append(f"{record.evidence_id}: reviewed_at missing")
        if record.evidence_maturity == EvidenceMaturity.STANDARD_OF_CARE:
            if record.finality_status != FinalityStatus.FINAL:
                errors.append(f"{record.evidence_id}: standard_of_care must be final")
        if record.kind == RecordKind.SOURCE:
            if record.evidence_maturity == EvidenceMaturity.INTERNAL_GOVERNED_RULE:
                errors.append(f"{record.evidence_id}: external source cannot be internal rule")
            if record.clinical_authority != ClinicalAuthority.NONE:
                errors.append(f"{record.evidence_id}: source record cannot directly hold runtime authority")
        if record.kind == RecordKind.RULE:
            if record.evidence_maturity != EvidenceMaturity.INTERNAL_GOVERNED_RULE:
                errors.append(f"{record.evidence_id}: IAmina rule must use internal_governed_rule maturity")
            if record.finality_status != FinalityStatus.VERSIONED_PRODUCT_RULE:
                errors.append(f"{record.evidence_id}: IAmina rule must be versioned_product_rule")
        if (
            record.evidence_maturity in {EvidenceMaturity.EMERGING_EVIDENCE, EvidenceMaturity.INVESTIGATIONAL}
            and record.clinical_authority == ClinicalAuthority.GOVERNED_RULE
        ):
            errors.append(f"{record.evidence_id}: immature external evidence cannot be governed runtime rule")
        for linked_id in (*record.supporting_evidence_ids, *record.supersedes, *record.superseded_by):
            if linked_id not in EVIDENCE_REGISTRY:
                errors.append(f"{record.evidence_id}: unknown linked evidence {linked_id}")
            if linked_id == record.evidence_id:
                errors.append(f"{record.evidence_id}: self-reference is not allowed")

    for name, evidence_id in KPI_EVIDENCE_IDS.items():
        if evidence_id not in EVIDENCE_REGISTRY:
            errors.append(f"KPI {name}: unknown evidence {evidence_id}")
    for code, evidence_id in PATTERN_EVIDENCE_IDS.items():
        if evidence_id not in EVIDENCE_REGISTRY:
            errors.append(f"pattern {code}: unknown evidence {evidence_id}")
    for code, evidence_id in ALERT_EVIDENCE_IDS.items():
        if evidence_id not in EVIDENCE_REGISTRY:
            errors.append(f"alert {code}: unknown evidence {evidence_id}")
    if PERSONAL_RESPONSE_EVIDENCE_ID not in EVIDENCE_REGISTRY:
        errors.append("personal response evidence is unregistered")

    return tuple(errors)


_REGISTRY_ERRORS = validate_registry()
if _REGISTRY_ERRORS:
    raise RuntimeError("Invalid diabetes evidence registry: " + "; ".join(_REGISTRY_ERRORS))
