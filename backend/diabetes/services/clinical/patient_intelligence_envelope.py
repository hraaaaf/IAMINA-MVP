"""Versioned read-only patient intelligence envelope (V1-02 first slice).

The envelope does not compute new clinical facts or promote observations. It
consumes only the governed Clinical Twin companion projection and preserves the
existing release-governed evidence/uncertainty admission decision.

It is an INTERNAL patient-scoped value object, NOT an LLM payload or a new API.
Future Home/Reports/IAmina consumers require separate authorization and egress
gates. In particular, this module must never call a model provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from django.utils import timezone

from diabetes.services.clinical.companion_evidence_uncertainty import (
    CompanionEvidenceProvenance,
    CompanionUncertainty,
    build_companion_evidence_context,
)
from diabetes.services.clinical.companion_pattern_intelligence import (
    SOURCE_VERSION as PATTERN_SOURCE_VERSION,
    project_personal_pattern_intelligence,
)
from diabetes.contracts.governed_longitudinal import GovernedLongitudinalContract
from diabetes.contracts.multi_source_fusion import FusionPopulation
from diabetes.services.clinical.governed_longitudinal import (
    compute_governed_longitudinal_intelligence,
)

ENVELOPE_VERSION = "patient-intelligence-envelope.v1"
EnvelopeStatus = Literal["ready", "insufficient_data"]

_NO_MEDICAL_AUTHORITY = (
    "descriptive_observation_only",
    "no_diagnosis_causality_prediction_urgency_or_treatment_authority",
    "not_authorized_for_llm_egress",
)


@dataclass(frozen=True, slots=True)
class PatientIntelligenceObservation:
    observation_key: str
    current_state: Literal["active", "resolved"]
    markers: tuple[str, ...]
    first_observed_at: datetime
    last_observed_at: datetime
    evidence_density: str
    evidence_window_days: int
    baseline_direction: str
    baseline_movement: str
    provenance: CompanionEvidenceProvenance
    uncertainty: CompanionUncertainty
    producer_version: str
    eligibility: Literal["governed_clinical_twin_pattern"] = (
        "governed_clinical_twin_pattern"
    )
    authority: Literal["descriptive_only"] = "descriptive_only"


@dataclass(frozen=True, slots=True)
class GovernedSourceRequest:
    """Explicit permission to include selected non-Clinical-Twin sources."""

    window_start: datetime
    window_end: datetime
    contract: GovernedLongitudinalContract


@dataclass(frozen=True, slots=True)
class GovernedPopulationEvidence:
    population: FusionPopulation
    sufficient: bool
    fact_count: int
    distinct_days: int
    source_refs: tuple[str, ...]
    median_glucose_mg_dl: float | None


@dataclass(frozen=True, slots=True)
class GovernedSourceEvidence:
    status: Literal["ready", "insufficient_data"]
    contract_id: str
    fusion_contract_id: str
    window_start: datetime
    window_end: datetime
    populations: tuple[GovernedPopulationEvidence, ...]
    missing_data: tuple[str, ...]
    limitations: tuple[str, ...]
    # V2-D sufficiency is descriptive product evidence, never CGM coverage.
    clinical_metrics_authorized: Literal[False] = False


@dataclass(frozen=True, slots=True)
class PatientIntelligenceEnvelope:
    patient_id: int
    status: EnvelopeStatus
    observations: tuple[PatientIntelligenceObservation, ...]
    missing_data: tuple[str, ...]
    limitations: tuple[str, ...]
    source_version: str = ENVELOPE_VERSION
    llm_egress_authorized: Literal[False] = False
    clinical_metrics_authorized: Literal[False] = False
    longitudinal_sources: GovernedSourceEvidence | None = None


def _governed_sources(
    *, patient_id: int, request: GovernedSourceRequest,
) -> GovernedSourceEvidence:
    """Reuse V2-D; never invent CGM eligibility or merge source populations."""

    if not isinstance(request.contract, GovernedLongitudinalContract):
        raise ValueError("explicit governed longitudinal contract required")
    if not isinstance(request.window_start, datetime) or not isinstance(
        request.window_end, datetime
    ):
        raise ValueError("source window must contain datetimes")
    # Validate awareness before comparing: naive-vs-aware raises TypeError.
    if not timezone.is_aware(request.window_start) or not timezone.is_aware(
        request.window_end
    ):
        raise ValueError("source window must be timezone-aware")
    if request.window_end <= request.window_start:
        raise ValueError("source window_start must precede window_end")
    result = compute_governed_longitudinal_intelligence(
        patient_id=patient_id,
        window_start=request.window_start,
        window_end=request.window_end,
        contract=request.contract,
    )
    expected = request.contract.fusion_contract.requested_populations
    actual = tuple(item.population for item in result.populations)
    if (
        result.patient_id != patient_id
        or result.contract_id != request.contract.contract_id
        or result.fusion_contract_id != request.contract.fusion_contract.contract_id
        or result.window_start != request.window_start
        or result.window_end != request.window_end
        or len(actual) != len(expected)
        or set(actual) != expected
        or result.status not in {"ready", "insufficient_data"}
    ):
        raise ValueError("governed longitudinal result violates request contract")

    for fact in result.facts:
        if (
            fact.fact.subject_ref != f"patient:{patient_id}"
            or fact.population not in expected
        ):
            raise ValueError("cross-patient or unrequested source evidence")

    populations: list[GovernedPopulationEvidence] = []
    for item in result.populations:
        related = tuple(
            fact.fact.source_ref for fact in result.facts
            if fact.population == item.population
        )
        if item.fact_count != len(related) or item.source_refs != related:
            raise ValueError("governed source counts/provenance disagree")
        expected_sufficiency = (
            item.fact_count >= request.contract.minimum_facts_per_population
            and item.distinct_days >= request.contract.minimum_distinct_days_per_population
        )
        if (
            item.sufficient != expected_sufficiency
            or item.distinct_days > item.fact_count
            or (item.sufficient and item.median_glucose_mg_dl is None)
        ):
            raise ValueError("governed source sufficiency evidence disagrees")
        populations.append(
            GovernedPopulationEvidence(
                population=item.population,
                sufficient=item.sufficient,
                fact_count=item.fact_count,
                distinct_days=item.distinct_days,
                source_refs=item.source_refs,
                # Descriptive medians must not escape an insufficient population.
                median_glucose_mg_dl=(
                    item.median_glucose_mg_dl if item.sufficient else None
                ),
            )
        )
    if (result.status == "ready") != all(item.sufficient for item in populations):
        raise ValueError("governed source sufficiency and status disagree")

    return GovernedSourceEvidence(
        status=result.status,
        contract_id=result.contract_id,
        fusion_contract_id=result.fusion_contract_id,
        window_start=result.window_start,
        window_end=result.window_end,
        populations=tuple(populations),
        missing_data=tuple(
            f"insufficient_{item.population.value}_evidence"
            for item in populations if not item.sufficient
        ),
        limitations=tuple(result.limitations),
    )


def build_patient_intelligence_envelope(
    *, patient_id: int, source_request: GovernedSourceRequest | None = None,
) -> PatientIntelligenceEnvelope:
    """Project one patient's *existing* governed observations without any writes.

    An invalid upstream evidence/provenance state fails closed by propagating
    ValueError. Unknown patterns are never silently transformed into insights.
    """

    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")
    if source_request is not None and not isinstance(source_request, GovernedSourceRequest):
        raise ValueError("source_request must be an explicit governed request")

    result = project_personal_pattern_intelligence(patient_id=patient_id)
    if result.status not in {"ready", "no_governed_patterns"}:
        raise ValueError("unsupported governed pattern status")
    if (result.status == "ready") != bool(result.patterns):
        raise ValueError("governed pattern status and evidence disagree")

    observations: list[PatientIntelligenceObservation] = []
    for item in result.patterns:
        if item.source_version != PATTERN_SOURCE_VERSION:
            raise ValueError("unknown governed pattern contract version")

        evidence = item.evidence_context
        provenance = evidence.provenance
        uncertainty = evidence.uncertainty
        if (
            provenance.evidence_id != item.evidence_id
            or provenance.producer != item.producer
            or uncertainty.evidence_density != item.evidence_density
            or tuple(uncertainty.limitations) != item.limitations
        ):
            raise ValueError("pattern and approved evidence context disagree")
        if provenance.clinical_authority != "governed_rule":
            raise ValueError("unapproved evidence authority")
        canonical_evidence = build_companion_evidence_context(
            evidence_id=item.evidence_id,
            producer=item.producer,
            evidence_density=item.evidence_density,
            evidence_density_trend=item.evidence_density_trend,
            missing_data=uncertainty.missing_data,
            limitations=item.limitations,
        )
        if evidence != canonical_evidence:
            raise ValueError("companion evidence differs from governed registry")
        if item.first_observed_at > item.last_observed_at:
            raise ValueError("observation timestamps are inconsistent")

        observations.append(
            PatientIntelligenceObservation(
                observation_key=item.observation_key,
                current_state=item.current_state,
                markers=item.markers,
                first_observed_at=item.first_observed_at,
                last_observed_at=item.last_observed_at,
                evidence_density=item.evidence_density,
                evidence_window_days=item.evidence_window_days,
                baseline_direction=item.baseline_direction,
                baseline_movement=item.baseline_movement,
                provenance=provenance,
                uncertainty=uncertainty,
                producer_version=item.source_version,
            )
        )

    sources = (
        _governed_sources(patient_id=patient_id, request=source_request)
        if source_request is not None else None
    )
    return PatientIntelligenceEnvelope(
        patient_id=patient_id,
        status=(
            "ready" if observations or (sources is not None and sources.status == "ready")
            else "insufficient_data"
        ),
        observations=tuple(observations),
        missing_data=(
            () if observations else ("no_eligible_governed_patterns",)
        ),
        limitations=_NO_MEDICAL_AUTHORITY + tuple(result.limitations),
        longitudinal_sources=sources,
    )


__all__ = [
    "ENVELOPE_VERSION",
    "PatientIntelligenceObservation",
    "PatientIntelligenceEnvelope",
    "GovernedSourceRequest",
    "GovernedSourceEvidence",
    "GovernedPopulationEvidence",
    "build_patient_intelligence_envelope",
]
