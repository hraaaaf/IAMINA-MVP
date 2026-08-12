"""Governed evidence + uncertainty envelope for material companion observations.

This module does not create clinical truth. It projects an already-approved
runtime evidence rule into a reusable, auditable companion envelope so later
surfaces can explain why an observation exists, how much repeatable evidence is
present, what is missing, and which limitations remain.
"""

from __future__ import annotations

from dataclasses import dataclass

from diabetes.services.clinical.evidence_registry import (
    ClinicalAuthority,
    EvidenceMaturity,
    FinalityStatus,
    RecordKind,
    get_evidence,
)

SOURCE_VERSION = "companion-evidence-uncertainty.v1"

_ALLOWED_EVIDENCE_DENSITIES = {"limited", "moderate", "strong"}
_ALLOWED_EVIDENCE_DENSITY_TRENDS = {
    "initial",
    "stable",
    "strengthening",
    "weakening",
}

# Material companion observations must be explicitly admitted here. A product
# rule being governed elsewhere does not automatically make it companion truth.
_APPROVED_COMPANION_RULE_PRODUCERS = {
    "rule.personal-response.repetition.v1": "diabetes.personal_response.v1",
}


@dataclass(frozen=True, slots=True)
class CompanionSupportingEvidence:
    evidence_id: str
    evidence_maturity: str
    finality_status: str
    source_organization: str
    source_title: str
    identifier: str
    reviewed_at: str
    supersession_state: str
    limitations: str


@dataclass(frozen=True, slots=True)
class CompanionEvidenceProvenance:
    evidence_id: str
    producer: str
    topic: str
    rule_summary: str
    evidence_maturity: str
    clinical_authority: str
    finality_status: str
    reviewed_at: str
    population: tuple[str, ...]
    modality: tuple[str, ...]
    supporting_evidence: tuple[CompanionSupportingEvidence, ...]


@dataclass(frozen=True, slots=True)
class CompanionUncertainty:
    evidence_density: str
    evidence_density_trend: str | None
    missing_data: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompanionEvidenceContext:
    provenance: CompanionEvidenceProvenance
    uncertainty: CompanionUncertainty
    source_version: str = SOURCE_VERSION


def _validated_string_tuple(
    values: tuple[str, ...],
    *,
    field: str,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field} must be an immutable tuple")
    if any(type(value) is not str or not value.strip() for value in values):
        raise ValueError(f"{field} must contain non-empty strings only")
    if len(values) != len(set(values)):
        raise ValueError(f"{field} must not contain duplicates")
    return values


def _supporting_evidence(
    evidence_ids: tuple[str, ...],
) -> tuple[CompanionSupportingEvidence, ...]:
    items: list[CompanionSupportingEvidence] = []
    for evidence_id in evidence_ids:
        record = get_evidence(evidence_id)
        if record.kind != RecordKind.SOURCE:
            raise ValueError("supporting evidence must resolve to source records")
        items.append(
            CompanionSupportingEvidence(
                evidence_id=record.evidence_id,
                evidence_maturity=record.evidence_maturity.value,
                finality_status=record.finality_status.value,
                source_organization=record.source_organization,
                source_title=record.source_title,
                identifier=record.identifier,
                reviewed_at=record.reviewed_at,
                supersession_state=record.supersession_state,
                limitations=record.limitations,
            )
        )
    return tuple(items)


def build_companion_evidence_context(
    *,
    evidence_id: str,
    producer: str,
    evidence_density: str,
    evidence_density_trend: str | None,
    missing_data: tuple[str, ...],
    limitations: tuple[str, ...],
) -> CompanionEvidenceContext:
    """Build a fail-closed evidence/uncertainty envelope for a material observation.

    Material companion observations may only use current IAmina product rules that
    have already crossed the evidence registry's ``GOVERNED_RULE`` promotion gate
    and are explicitly registered for a companion producer. External sources remain
    supporting evidence and retain their own maturity; their presence never upgrades
    them to runtime authority.
    """

    if type(evidence_id) is not str or not evidence_id.strip():
        raise ValueError("evidence_id must be a non-empty string")
    if type(producer) is not str or not producer.strip():
        raise ValueError("producer must be a non-empty string")
    if evidence_density not in _ALLOWED_EVIDENCE_DENSITIES:
        raise ValueError("unapproved companion evidence density")
    if (
        evidence_density_trend is not None
        and evidence_density_trend not in _ALLOWED_EVIDENCE_DENSITY_TRENDS
    ):
        raise ValueError("unapproved companion evidence-density trend")

    validated_missing = _validated_string_tuple(missing_data, field="missing_data")
    validated_limitations = _validated_string_tuple(limitations, field="limitations")

    record = get_evidence(evidence_id)
    if record.kind != RecordKind.RULE:
        raise ValueError("material companion observation requires a governed rule")
    if record.evidence_maturity != EvidenceMaturity.INTERNAL_GOVERNED_RULE:
        raise ValueError("material companion observation requires internal governed maturity")
    if record.finality_status != FinalityStatus.VERSIONED_PRODUCT_RULE:
        raise ValueError("material companion observation requires a versioned product rule")
    if record.clinical_authority != ClinicalAuthority.GOVERNED_RULE:
        raise ValueError("material companion observation requires governed runtime authority")
    if record.supersession_state != "current":
        raise ValueError("material companion observation cannot use a superseded rule")

    try:
        approved_producer = _APPROVED_COMPANION_RULE_PRODUCERS[record.evidence_id]
    except KeyError as exc:
        raise ValueError(
            "evidence rule is not registered for material companion observations"
        ) from exc
    if producer != approved_producer:
        raise ValueError("producer is not approved for this companion evidence rule")

    provenance = CompanionEvidenceProvenance(
        evidence_id=record.evidence_id,
        producer=producer,
        topic=record.topic,
        rule_summary=record.claim_or_rule,
        evidence_maturity=record.evidence_maturity.value,
        clinical_authority=record.clinical_authority.value,
        finality_status=record.finality_status.value,
        reviewed_at=record.reviewed_at,
        population=record.population,
        modality=record.modality,
        supporting_evidence=_supporting_evidence(record.supporting_evidence_ids),
    )
    uncertainty = CompanionUncertainty(
        evidence_density=evidence_density,
        evidence_density_trend=evidence_density_trend,
        missing_data=validated_missing,
        limitations=validated_limitations,
    )
    return CompanionEvidenceContext(
        provenance=provenance,
        uncertainty=uncertainty,
    )
