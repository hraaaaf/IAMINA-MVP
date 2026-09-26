"""Governed descriptive longitudinal intelligence over V2-C fusion output.

V2-D does not infer causality, treatment response, targets, predictions or
therapeutic recommendations. It reports source-separated longitudinal evidence
only when every explicitly requested population satisfies the product sufficiency
contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Literal

from diabetes.contracts.governed_longitudinal import GovernedLongitudinalContract
from diabetes.contracts.multi_source_fusion import FusionPopulation
from diabetes.services.clinical.multi_source_fusion import (
    GovernedFusionFact,
    fuse_governed_glucose_sources,
)

LongitudinalStatus = Literal["ready", "insufficient_data"]


@dataclass(frozen=True, slots=True)
class LongitudinalPopulationEvidence:
    population: FusionPopulation
    fact_count: int
    distinct_days: int
    median_glucose_mg_dl: float | None
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    source_refs: tuple[str, ...]
    sufficient: bool


@dataclass(frozen=True, slots=True)
class GovernedLongitudinalResult:
    contract_id: str
    fusion_contract_id: str
    patient_id: int
    window_start: datetime
    window_end: datetime
    status: LongitudinalStatus
    populations: tuple[LongitudinalPopulationEvidence, ...]
    facts: tuple[GovernedFusionFact, ...]
    limitations: tuple[str, ...]


_LIMITATIONS = (
    "population_boundaries_preserved",
    "source_refs_preserved_for_every_fact",
    "sufficiency_is_product_evidence_not_clinical_significance",
    "cross_source_comparison_is_descriptive_not_causal",
    "no_clinical_target_prediction_treatment_response_or_dose_authority",
)


def _population_evidence(
    population: FusionPopulation,
    facts: tuple[GovernedFusionFact, ...],
    *,
    minimum_facts: int,
    minimum_days: int,
) -> LongitudinalPopulationEvidence:
    selected = tuple(item for item in facts if item.population is population)
    ordered = tuple(sorted(selected, key=lambda item: (item.observed_at, item.fact.source_ref)))
    distinct_days = len({item.observed_at.date() for item in ordered})
    sufficient = len(ordered) >= minimum_facts and distinct_days >= minimum_days
    return LongitudinalPopulationEvidence(
        population=population,
        fact_count=len(ordered),
        distinct_days=distinct_days,
        median_glucose_mg_dl=(
            round(float(median(float(item.fact.value) for item in ordered)), 1)
            if ordered
            else None
        ),
        first_observed_at=ordered[0].observed_at if ordered else None,
        last_observed_at=ordered[-1].observed_at if ordered else None,
        source_refs=tuple(item.fact.source_ref for item in ordered),
        sufficient=sufficient,
    )


def compute_governed_longitudinal_intelligence(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
    contract: GovernedLongitudinalContract,
) -> GovernedLongitudinalResult:
    """Return source-separated longitudinal evidence under an explicit V2-D contract."""
    if not isinstance(contract, GovernedLongitudinalContract):
        raise TypeError("contract must be GovernedLongitudinalContract")

    fusion = fuse_governed_glucose_sources(
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
        contract=contract.fusion_contract,
    )
    populations = tuple(
        _population_evidence(
            population,
            fusion.facts,
            minimum_facts=contract.minimum_facts_per_population,
            minimum_days=contract.minimum_distinct_days_per_population,
        )
        for population in sorted(
            fusion.requested_populations,
            key=lambda item: item.value,
        )
    )
    status: LongitudinalStatus = (
        "ready" if populations and all(item.sufficient for item in populations)
        else "insufficient_data"
    )
    return GovernedLongitudinalResult(
        contract_id=contract.contract_id,
        fusion_contract_id=fusion.contract_id,
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
        status=status,
        populations=populations,
        facts=fusion.facts,
        limitations=_LIMITATIONS + fusion.limitations,
    )
