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

from diabetes.services.clinical.companion_evidence_uncertainty import (
    CompanionEvidenceProvenance,
    CompanionUncertainty,
)
from diabetes.services.clinical.companion_pattern_intelligence import (
    SOURCE_VERSION as PATTERN_SOURCE_VERSION,
    project_personal_pattern_intelligence,
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
class PatientIntelligenceEnvelope:
    patient_id: int
    status: EnvelopeStatus
    observations: tuple[PatientIntelligenceObservation, ...]
    missing_data: tuple[str, ...]
    limitations: tuple[str, ...]
    source_version: str = ENVELOPE_VERSION
    llm_egress_authorized: Literal[False] = False


def build_patient_intelligence_envelope(*, patient_id: int) -> PatientIntelligenceEnvelope:
    """Project one patient's *existing* governed observations without any writes.

    An invalid upstream evidence/provenance state fails closed by propagating
    ValueError. Unknown patterns are never silently transformed into insights.
    """

    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")

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

    return PatientIntelligenceEnvelope(
        patient_id=patient_id,
        status="ready" if observations else "insufficient_data",
        observations=tuple(observations),
        missing_data=(
            () if observations else ("no_eligible_governed_patterns",)
        ),
        limitations=_NO_MEDICAL_AUTHORITY + tuple(result.limitations),
    )


__all__ = [
    "ENVELOPE_VERSION",
    "PatientIntelligenceObservation",
    "PatientIntelligenceEnvelope",
    "build_patient_intelligence_envelope",
]
