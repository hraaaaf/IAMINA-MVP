"""Governed multi-source glucose fusion for V2-C.

This service intentionally performs a provenance-preserving union, not a silent
normalization into one anonymous population. It does not infer causality,
clinical equivalence, treatment response, or cross-source duplicate identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.db.models import F, Q
from django.utils import timezone

from core.contracts.clinical_fact import CanonicalClinicalFact
from diabetes.contracts import log_entry as log_input
from diabetes.contracts.multi_source_fusion import (
    FusionPopulation,
    GovernedGlucoseFusionContract,
)
from diabetes.models import CGMReadingRecord, LogEntry
from diabetes.services.canonical_facts import from_cgm_reading, from_log_entry


class FusionInputError(ValueError):
    """Raised when the requested fusion window or subject is unsafe."""


@dataclass(frozen=True, slots=True)
class GovernedFusionFact:
    population: FusionPopulation
    observed_at: datetime
    fact: CanonicalClinicalFact


@dataclass(frozen=True, slots=True)
class FusionPopulationSummary:
    population: FusionPopulation
    included_count: int
    excluded_count: int
    exclusion_reason: str | None = None


@dataclass(frozen=True, slots=True)
class GovernedGlucoseFusion:
    contract_id: str
    patient_id: int
    window_start: datetime
    window_end: datetime
    requested_populations: tuple[FusionPopulation, ...]
    facts: tuple[GovernedFusionFact, ...]
    population_summaries: tuple[FusionPopulationSummary, ...]
    limitations: tuple[str, ...]


_LIMITATIONS = (
    "provenance_preserved_per_fact",
    "cross_source_duplicates_preserved_not_deduplicated",
    "legacy_logentry_cgm_rows_excluded",
    "cgm_requires_valid_session_linkage",
    "fusion_is_descriptive_not_causal_or_treatment_authority",
)


def _validate_window(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
) -> None:
    if type(patient_id) is not int or patient_id <= 0:
        raise FusionInputError("patient_id must be a positive integer")
    if window_start is None or window_end is None or window_end <= window_start:
        raise FusionInputError("window_start must be earlier than window_end")
    if not timezone.is_aware(window_start) or not timezone.is_aware(window_end):
        raise FusionInputError("fusion window must be timezone-aware")


def _event_at(entry: LogEntry) -> datetime:
    return entry.logged_at or entry.created_at


def _journal_facts(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
) -> tuple[GovernedFusionFact, ...]:
    rows = (
        LogEntry.objects.filter(
            patient_id=patient_id,
            source__in=log_input.JOURNAL_LONGITUDINAL_SOURCE_VALUES,
        )
        .filter(
            Q(logged_at__gte=window_start, logged_at__lte=window_end)
            | Q(
                logged_at__isnull=True,
                created_at__gte=window_start,
                created_at__lte=window_end,
            )
        )
        .order_by("logged_at", "created_at", "id")
    )
    return tuple(
        GovernedFusionFact(
            population=FusionPopulation.JOURNAL,
            observed_at=_event_at(row),
            fact=from_log_entry(row),
        )
        for row in rows
    )


def _import_facts(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
) -> tuple[GovernedFusionFact, ...]:
    rows = (
        LogEntry.objects.filter(patient_id=patient_id, source="import")
        .filter(
            Q(logged_at__gte=window_start, logged_at__lte=window_end)
            | Q(
                logged_at__isnull=True,
                created_at__gte=window_start,
                created_at__lte=window_end,
            )
        )
        .order_by("logged_at", "created_at", "id")
    )
    return tuple(
        GovernedFusionFact(
            population=FusionPopulation.IMPORT,
            observed_at=_event_at(row),
            fact=from_log_entry(row),
        )
        for row in rows
    )


def _valid_cgm_queryset(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
):
    return (
        CGMReadingRecord.objects.filter(
            patient_id=patient_id,
            session__isnull=False,
            session__patient_id=patient_id,
            recorded_at__gte=window_start,
            recorded_at__lte=window_end,
            source=F("session__source"),
        )
        .filter(recorded_at__gte=F("session__started_at"))
        .filter(
            Q(session__ended_at__isnull=True)
            | Q(recorded_at__lte=F("session__ended_at"))
        )
        .order_by("recorded_at", "id")
    )


def _cgm_facts(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
) -> tuple[tuple[GovernedFusionFact, ...], int]:
    candidates = CGMReadingRecord.objects.filter(
        patient_id=patient_id,
        recorded_at__gte=window_start,
        recorded_at__lte=window_end,
    )
    valid_rows = list(
        _valid_cgm_queryset(
            patient_id=patient_id,
            window_start=window_start,
            window_end=window_end,
        )
    )
    valid_ids = {row.id for row in valid_rows}
    excluded_count = candidates.exclude(id__in=valid_ids).count()

    return (
        tuple(
            GovernedFusionFact(
                population=FusionPopulation.CGM,
                observed_at=row.recorded_at,
                fact=from_cgm_reading(row),
            )
            for row in valid_rows
        ),
        excluded_count,
    )


def fuse_governed_glucose_sources(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
    contract: GovernedGlucoseFusionContract,
) -> GovernedGlucoseFusion:
    """Return an explicit, patient-scoped, provenance-preserving source union.

    No source population is added implicitly. Legacy LogEntry(source="cgm")
    rows are counted as excluded rather than treated as equivalent to normalized
    CGM transport records.
    """
    if not isinstance(contract, GovernedGlucoseFusionContract):
        raise FusionInputError("an explicit governed fusion contract is required")
    _validate_window(
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
    )

    facts: list[GovernedFusionFact] = []
    summaries: list[FusionPopulationSummary] = []

    if FusionPopulation.JOURNAL in contract.requested_populations:
        journal = _journal_facts(
            patient_id=patient_id,
            window_start=window_start,
            window_end=window_end,
        )
        facts.extend(journal)
        legacy_cgm_count = (
            LogEntry.objects.filter(patient_id=patient_id, source="cgm")
            .filter(
                Q(logged_at__gte=window_start, logged_at__lte=window_end)
                | Q(
                    logged_at__isnull=True,
                    created_at__gte=window_start,
                    created_at__lte=window_end,
                )
            )
            .count()
        )
        summaries.append(
            FusionPopulationSummary(
                population=FusionPopulation.JOURNAL,
                included_count=len(journal),
                excluded_count=legacy_cgm_count,
                exclusion_reason=(
                    "legacy_logentry_cgm_not_authorized"
                    if legacy_cgm_count
                    else None
                ),
            )
        )

    if FusionPopulation.IMPORT in contract.requested_populations:
        imported = _import_facts(
            patient_id=patient_id,
            window_start=window_start,
            window_end=window_end,
        )
        facts.extend(imported)
        summaries.append(
            FusionPopulationSummary(
                population=FusionPopulation.IMPORT,
                included_count=len(imported),
                excluded_count=0,
            )
        )

    if FusionPopulation.CGM in contract.requested_populations:
        cgm, excluded_cgm = _cgm_facts(
            patient_id=patient_id,
            window_start=window_start,
            window_end=window_end,
        )
        facts.extend(cgm)
        summaries.append(
            FusionPopulationSummary(
                population=FusionPopulation.CGM,
                included_count=len(cgm),
                excluded_count=excluded_cgm,
                exclusion_reason=(
                    "missing_or_invalid_sensor_session_linkage"
                    if excluded_cgm
                    else None
                ),
            )
        )

    facts.sort(
        key=lambda item: (
            item.observed_at,
            item.population.value,
            item.fact.source_ref,
        )
    )
    summaries.sort(key=lambda item: item.population.value)

    return GovernedGlucoseFusion(
        contract_id=contract.contract_id,
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
        requested_populations=tuple(
            sorted(contract.requested_populations, key=lambda item: item.value)
        ),
        facts=tuple(facts),
        population_summaries=tuple(summaries),
        limitations=_LIMITATIONS,
    )
