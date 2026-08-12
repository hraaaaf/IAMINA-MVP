"""Deterministic assembler for ``consultation-brief.v1``.

The assembler is intentionally read-only. It consumes synchronized non-demo
Journal glucose rows plus already-persisted, evidence-governed Clinical Twin
observations and emits the certified consultation-brief contract. It does not
refresh clinical state, call a model, infer diagnosis/causality, or modify
patient data.
"""

from __future__ import annotations

from datetime import datetime

from django.db.models import Avg, Q
from django.db.models.functions import Coalesce

from core.contracts.truth import TruthKind
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationBriefEnvelope,
    ConsultationChangeKind,
    ConsultationComparisonBasis,
    ConsultationEvidenceDensity,
    ConsultationEvidenceItem,
    ConsultationNextStep,
    ConsultationReviewCheckpoint,
)

SOURCE_ADAPTER_VERSION = "consultation-source-adapter.v1"
LOG_ENTRY_SOURCE = "diabetes.log-entry"
RECORDED_STATS_SOURCE = "diabetes.log-entry.sql-average"
RECORDED_STATS_EVIDENCE_ID = "rule.metric.recorded-glucose-stats.v1"
CLINICAL_TWIN_SOURCE = "diabetes.clinical-observation-state"

_EVIDENCE_DENSITY = {
    ClinicalObservationState.EVIDENCE_LIMITED: ConsultationEvidenceDensity.LIMITED,
    ClinicalObservationState.EVIDENCE_MODERATE: ConsultationEvidenceDensity.MODERATE,
    ClinicalObservationState.EVIDENCE_STRONG: ConsultationEvidenceDensity.STRONG,
}


def _is_timezone_aware(value: object) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _validate_inputs(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
    review_checkpoint: ConsultationReviewCheckpoint | None,
) -> None:
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")
    if not _is_timezone_aware(window_start) or not _is_timezone_aware(window_end):
        raise ValueError("consultation assembly window must be timezone-aware")
    if window_start >= window_end:
        raise ValueError("consultation assembly window_start must precede window_end")
    if review_checkpoint is not None and not isinstance(
        review_checkpoint,
        ConsultationReviewCheckpoint,
    ):
        raise ValueError("review_checkpoint must be a ConsultationReviewCheckpoint")
    if review_checkpoint is not None:
        if review_checkpoint.reviewed_at >= window_end:
            raise ValueError("review checkpoint must precede the consultation window end")
        if review_checkpoint.reviewed_at != window_start:
            raise ValueError(
                "since-review consultation window_start must equal checkpoint reviewed_at"
            )


def _eligible_logs(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
):
    return (
        LogEntry.objects.annotate(
            consultation_effective_at=Coalesce("logged_at", "created_at")
        )
        .filter(
            patient_id=patient_id,
            consultation_effective_at__gte=window_start,
            consultation_effective_at__lte=window_end,
        )
        .exclude(source="demo")
    )


def _latest_glucose_items(logs) -> tuple[ConsultationEvidenceItem, ...]:
    latest = logs.order_by("-consultation_effective_at", "-id").first()
    if latest is None:
        return ()

    effective_at = latest.logged_at or latest.created_at
    common = {
        "truth_kind": TruthKind.OBSERVED_FACT,
        "source": LOG_ENTRY_SOURCE,
        "source_version": SOURCE_ADAPTER_VERSION,
        "allowed_next_step": ConsultationNextStep.MONITOR,
    }
    return (
        ConsultationEvidenceItem(
            key="recorded_glucose.latest_mg_dl",
            value=float(latest.blood_sugar),
            unit="mg/dL",
            limitations=("recorded_value_not_diagnosis_or_target_assessment",),
            **common,
        ),
        ConsultationEvidenceItem(
            key="recorded_glucose.latest_at",
            value=effective_at.isoformat(),
            limitations=("timestamp_of_recorded_value",),
            **common,
        ),
        ConsultationEvidenceItem(
            key="recorded_glucose.latest_capture_source",
            value=latest.source,
            limitations=(
                "capture_source_is_provenance_not_modality_sufficiency",
            ),
            **common,
        ),
    )


def _average_glucose_item(logs) -> ConsultationEvidenceItem | None:
    average = logs.aggregate(value=Avg("blood_sugar"))["value"]
    if average is None:
        return None
    return ConsultationEvidenceItem(
        key="recorded_glucose.average_mg_dl",
        value=round(float(average), 1),
        unit="mg/dL",
        truth_kind=TruthKind.DETERMINISTIC_DERIVATION,
        source=RECORDED_STATS_SOURCE,
        source_version=SOURCE_ADAPTER_VERSION,
        evidence_id=RECORDED_STATS_EVIDENCE_ID,
        limitations=(
            "descriptive_average_of_recorded_rows_only",
            "not_cgm_time_weighted_and_not_target_assessment",
        ),
        allowed_next_step=ConsultationNextStep.MONITOR,
    )


def _observation_change_kind(
    observation: ClinicalObservationState,
    checkpoint: ConsultationReviewCheckpoint | None,
) -> ConsultationChangeKind:
    if checkpoint is None:
        return ConsultationChangeKind.CURRENT_STATE

    reviewed_at = checkpoint.reviewed_at
    if (
        observation.status == ClinicalObservationState.STATUS_INACTIVE
        and observation.status_changed_at > reviewed_at
    ):
        return ConsultationChangeKind.RESOLVED_SINCE_REVIEW
    if observation.first_seen_at > reviewed_at:
        return ConsultationChangeKind.NEW_SINCE_REVIEW
    if (
        observation.status == ClinicalObservationState.STATUS_ACTIVE
        and observation.status_changed_at <= reviewed_at
        and observation.last_seen_at > reviewed_at
    ):
        return ConsultationChangeKind.PERSISTING_SINCE_REVIEW
    return ConsultationChangeKind.UNKNOWN


def _clinical_twin_items(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
    review_checkpoint: ConsultationReviewCheckpoint | None,
) -> tuple[ConsultationEvidenceItem, ...]:
    observations = (
        ClinicalObservationState.objects.filter(
            patient_id=patient_id,
            first_seen_at__lte=window_end,
            last_refreshed_at__lte=window_end,
        )
        .filter(
            Q(status=ClinicalObservationState.STATUS_ACTIVE)
            | Q(
                status=ClinicalObservationState.STATUS_INACTIVE,
                status_changed_at__gte=window_start,
                status_changed_at__lte=window_end,
            )
        )
        .order_by("observation_key")
    )

    items: list[ConsultationEvidenceItem] = []
    for observation in observations:
        change_kind = _observation_change_kind(observation, review_checkpoint)
        limitations = [
            "observational_association_only",
            "evidence_density_is_repeatability_not_probability",
            "no_causality_diagnosis_or_treatment_inference",
        ]
        if (
            review_checkpoint is not None
            and change_kind is ConsultationChangeKind.UNKNOWN
        ):
            limitations.append(
                "since_review_change_not_inferred_from_incomplete_transition_history"
            )

        items.append(
            ConsultationEvidenceItem(
                key=f"clinical_twin.{observation.observation_key}.status",
                value=observation.status,
                truth_kind=TruthKind.DETERMINISTIC_DERIVATION,
                source=CLINICAL_TWIN_SOURCE,
                source_version=SOURCE_ADAPTER_VERSION,
                change_kind=change_kind,
                evidence_id=observation.evidence_id,
                evidence_window_days=observation.evidence_window_days,
                evidence_density=_EVIDENCE_DENSITY[observation.evidence_strength],
                limitations=tuple(limitations),
                allowed_next_step=(
                    ConsultationNextStep.PREPARE_CLINICIAN_DISCUSSION
                    if observation.status == ClinicalObservationState.STATUS_ACTIVE
                    else ConsultationNextStep.MONITOR
                ),
            )
        )
    return tuple(items)


def assemble_consultation_brief(
    *,
    patient_id: int,
    window_start: datetime,
    window_end: datetime,
    review_checkpoint: ConsultationReviewCheckpoint | None = None,
) -> ConsultationBriefEnvelope:
    """Assemble a read-only evidence-qualified clinician review dossier.

    ``CURRENT_SNAPSHOT`` is used when no explicit checkpoint exists. A supplied
    checkpoint unlocks only the bounded transition semantics that can be proven
    from the persisted Clinical Twin fields; ambiguous change remains ``UNKNOWN``.
    """

    _validate_inputs(
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
        review_checkpoint=review_checkpoint,
    )

    logs = _eligible_logs(
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
    )
    latest_items = _latest_glucose_items(logs)
    average = _average_glucose_item(logs)
    clinical_twin = _clinical_twin_items(
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
        review_checkpoint=review_checkpoint,
    )

    items = latest_items
    if average is not None:
        items += (average,)
    items += clinical_twin

    missing_data: list[str] = []
    limitations = [
        "consultation_review_support_only",
        "no_model_authored_contract_fields",
    ]

    if not latest_items:
        missing_data.append("no_synchronized_non_demo_glucose_in_window")
    if not clinical_twin:
        missing_data.append("no_eligible_clinical_twin_observations")
    if review_checkpoint is None:
        missing_data.append("no_authoritative_review_checkpoint")
        limitations.append("since_review_comparison_unavailable")

    return ConsultationBriefEnvelope(
        window_start=window_start,
        window_end=window_end,
        comparison_basis=(
            ConsultationComparisonBasis.SINCE_REVIEW_CHECKPOINT
            if review_checkpoint is not None
            else ConsultationComparisonBasis.CURRENT_SNAPSHOT
        ),
        review_checkpoint=review_checkpoint,
        items=items,
        missing_data=tuple(missing_data),
        limitations=tuple(limitations),
    )
