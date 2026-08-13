"""Deterministic assembler for the certified ``consultation-brief.v1`` contract.

P2-COMPANION-5 is patient consultation preparation, not autonomous medical
reasoning. The assembler is read-only: it consumes synchronized non-demo glucose
rows plus already-governed Companion projections and emits only the bounded
review-support contract certified in PR #143.

Since-review semantics are authorized only by P2-COMPANION-1's persisted,
server-captured CompanionReviewAnchor. Caller-supplied checkpoint objects are not
accepted as authority. Clinical Twin material state is consumed through the
certified P2-COMPANION-2/3 projection so its validation and uncertainty cannot be
silently bypassed.
"""

from __future__ import annotations

from datetime import datetime

from django.db.models import Avg
from django.db.models.functions import Coalesce

from core.contracts.truth import TruthKind
from diabetes.models.companion_review import CompanionReviewAnchor
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.companion_change import (
    compare_since_last_companion_review,
)
from diabetes.services.clinical.companion_pattern_intelligence import (
    project_personal_pattern_intelligence,
)
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationBriefEnvelope,
    ConsultationChangeKind,
    ConsultationComparisonBasis,
    ConsultationEvidenceDensity,
    ConsultationEvidenceItem,
    ConsultationNextStep,
    ConsultationReviewCheckpoint,
)

SOURCE_ADAPTER_VERSION = "consultation-companion-assembler.v1"
LOG_ENTRY_SOURCE = "diabetes.log-entry"
RECORDED_STATS_SOURCE = "diabetes.log-entry.sql-average"
RECORDED_STATS_EVIDENCE_ID = "rule.metric.recorded-glucose-stats.v1"
COMPANION_REVIEW_SOURCE = CompanionReviewAnchor.SOURCE_EXPLICIT_REVIEW

_EVIDENCE_DENSITY = {
    "limited": ConsultationEvidenceDensity.LIMITED,
    "moderate": ConsultationEvidenceDensity.MODERATE,
    "strong": ConsultationEvidenceDensity.STRONG,
}
_CHANGE_KIND = {
    "new": ConsultationChangeKind.NEW_SINCE_REVIEW,
    "persisting": ConsultationChangeKind.PERSISTING_SINCE_REVIEW,
    "improving": ConsultationChangeKind.IMPROVING_SINCE_REVIEW,
    "resolved": ConsultationChangeKind.RESOLVED_SINCE_REVIEW,
    "unknown": ConsultationChangeKind.UNKNOWN,
}


def _is_timezone_aware(value: object) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _validate_inputs(*, patient_id: int, window_start: datetime, window_end: datetime) -> None:
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")
    if not _is_timezone_aware(window_start) or not _is_timezone_aware(window_end):
        raise ValueError("consultation assembly window must be timezone-aware")
    if window_start >= window_end:
        raise ValueError("consultation assembly window_start must precede window_end")


def _consultation_density(value: str) -> ConsultationEvidenceDensity:
    try:
        return _EVIDENCE_DENSITY[value]
    except KeyError as exc:
        raise ValueError("companion item has unapproved evidence density") from exc


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _eligible_logs(*, patient_id: int, window_start: datetime, window_end: datetime):
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
            limitations=("capture_source_is_provenance_not_modality_sufficiency",),
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


def _clinical_twin_items(
    *, patient_id: int, window_start: datetime, window_end: datetime
) -> tuple[ConsultationEvidenceItem, ...]:
    """Project material Twin state only through certified Companion P2-2/3."""

    result = project_personal_pattern_intelligence(patient_id=patient_id)
    items: list[ConsultationEvidenceItem] = []
    for pattern in result.patterns:
        # P2-COMPANION-2 is a current-state projection, not a historical snapshot.
        # Never leak evidence/state that is known to post-date the requested dossier.
        if pattern.first_observed_at > window_end or pattern.last_observed_at > window_end:
            continue
        if pattern.state_changed_at > window_end:
            continue
        if pattern.current_state == "resolved" and pattern.state_changed_at < window_start:
            continue

        context = pattern.evidence_context
        if context.provenance.evidence_id != pattern.evidence_id:
            raise ValueError("pattern evidence envelope does not match evidence ID")
        if context.provenance.producer != pattern.producer:
            raise ValueError("pattern evidence envelope does not match producer")
        if context.uncertainty.evidence_density != pattern.evidence_density:
            raise ValueError("pattern evidence envelope does not match evidence density")

        items.append(
            ConsultationEvidenceItem(
                key=f"clinical_twin.{pattern.observation_key}.status",
                value=("active" if pattern.current_state == "active" else "inactive"),
                truth_kind=TruthKind.DETERMINISTIC_DERIVATION,
                source=pattern.producer,
                source_version=pattern.source_version,
                evidence_id=pattern.evidence_id,
                evidence_window_days=pattern.evidence_window_days,
                evidence_density=_consultation_density(pattern.evidence_density),
                missing_data=context.uncertainty.missing_data,
                limitations=_dedupe(
                    pattern.limitations + context.uncertainty.limitations
                ),
                # Current observation state alone does not create discussion authority.
                allowed_next_step=ConsultationNextStep.MONITOR,
            )
        )
    return tuple(items)


def _companion_change_items(
    *, patient_id: int, window_start: datetime, window_end: datetime
):
    result = compare_since_last_companion_review(patient_id=patient_id)
    if result.status != "ready":
        return None, (), result.missing_data

    assert result.anchor_captured_at is not None
    if not (window_start <= result.anchor_captured_at < window_end):
        return None, (), ("no_explicit_companion_review_anchor_inside_requested_window",)

    checkpoint = ConsultationReviewCheckpoint(
        reviewed_at=result.anchor_captured_at,
        source=COMPANION_REVIEW_SOURCE,
    )
    items: list[ConsultationEvidenceItem] = []
    for change in result.changes:
        try:
            change_kind = _CHANGE_KIND[change.change_kind]
        except KeyError as exc:
            raise ValueError("companion change contains unapproved consultation vocabulary") from exc

        context = change.evidence_context
        if context.provenance.evidence_id != change.evidence_id:
            raise ValueError("change evidence envelope does not match evidence ID")
        if context.provenance.producer != change.producer:
            raise ValueError("change evidence envelope does not match producer")
        if context.uncertainty.evidence_density != change.evidence_strength:
            raise ValueError("change evidence envelope does not match evidence density")

        items.append(
            ConsultationEvidenceItem(
                key=f"companion_change.{change.observation_key}",
                value=change.change_kind,
                truth_kind=TruthKind.DETERMINISTIC_DERIVATION,
                source=change.producer,
                source_version=change.source_version,
                change_kind=change_kind,
                evidence_id=change.evidence_id,
                evidence_density=_consultation_density(change.evidence_strength),
                missing_data=context.uncertainty.missing_data,
                limitations=_dedupe(
                    change.limitations + context.uncertainty.limitations
                ),
                # Missing evidence may justify collecting context. Every other
                # longitudinal state remains MONITOR unless another certified
                # upstream engine already grants stronger action authority.
                allowed_next_step=(
                    ConsultationNextStep.COLLECT_MISSING_DATA
                    if change.change_kind == "unknown"
                    else ConsultationNextStep.MONITOR
                ),
            )
        )
    return checkpoint, tuple(items), ()


def assemble_consultation_brief(
    *, patient_id: int, window_start: datetime, window_end: datetime
) -> ConsultationBriefEnvelope:
    """Assemble one deterministic patient consultation-preparation dossier.

    The function accepts no caller-provided checkpoint, diagnosis, action, free text
    or model output. When an authoritative Companion review anchor exists inside the
    requested dossier window, bounded P2-COMPANION-1 since-review semantics are
    projected into the certified contract. Otherwise the brief remains a truthful
    current snapshot.
    """

    _validate_inputs(
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
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
    )
    checkpoint, change_items, change_missing = _companion_change_items(
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
    )

    items = latest_items
    if average is not None:
        items += (average,)
    items += clinical_twin + change_items

    missing_data = list(change_missing)
    limitations = [
        "patient_consultation_preparation_only",
        "clinician_remains_medical_decision_authority",
        "no_model_authored_contract_fields",
        "no_diagnosis_prescription_dose_or_treatment_change_authority",
    ]
    if not latest_items:
        missing_data.append("no_synchronized_non_demo_glucose_in_window")
    if not clinical_twin:
        missing_data.append("no_eligible_clinical_twin_observations")

    comparison_basis = (
        ConsultationComparisonBasis.SINCE_REVIEW_CHECKPOINT
        if checkpoint is not None
        else ConsultationComparisonBasis.CURRENT_SNAPSHOT
    )
    return ConsultationBriefEnvelope(
        window_start=window_start,
        window_end=window_end,
        comparison_basis=comparison_basis,
        review_checkpoint=checkpoint,
        items=items,
        missing_data=tuple(dict.fromkeys(missing_data)),
        limitations=tuple(limitations),
    )
