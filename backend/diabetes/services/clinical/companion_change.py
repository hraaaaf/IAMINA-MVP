"""Deterministic change-since-review engine for the patient companion.

The engine compares current governed Clinical Twin state with a server-captured
CompanionReviewAnchor. It never infers review history from app activity, accepts
no caller-supplied timestamp, and does not diagnose, infer causality, or judge a
treatment response.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from django.contrib.auth import get_user_model
from django.db import transaction

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.companion_review import (
    CompanionReviewAnchor,
    CompanionReviewObservationSnapshot,
)
from diabetes.services.clinical.companion_evidence_uncertainty import (
    CompanionEvidenceContext,
    build_companion_evidence_context,
)

ChangeKind = Literal["new", "persisting", "improving", "resolved", "unknown"]
ComparisonStatus = Literal["ready", "insufficient_anchor"]

ENGINE_VERSION = "companion-change-since-review.v1"

_COMMON_LIMITATIONS = (
    "observational_association_only",
    "evidence_density_is_repeatability_not_probability",
    "no_diagnosis_causality_or_treatment_response_inference",
)


@dataclass(frozen=True, slots=True)
class CompanionChangeItem:
    observation_key: str
    change_kind: ChangeKind
    evidence_id: str
    producer: str
    evidence_strength: str
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    baseline_delta_at_review_mg_dl: float | None
    baseline_delta_now_mg_dl: float | None
    limitations: tuple[str, ...]
    missing_data: tuple[str, ...]
    evidence_context: CompanionEvidenceContext
    source_version: str = ENGINE_VERSION


@dataclass(frozen=True, slots=True)
class CompanionChangeResult:
    status: ComparisonStatus
    anchor_id: int | None
    anchor_captured_at: datetime | None
    changes: tuple[CompanionChangeItem, ...]
    missing_data: tuple[str, ...]
    limitations: tuple[str, ...]
    source_version: str = ENGINE_VERSION


def _validate_patient_id(patient_id: int) -> None:
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")


def _validate_current_observation(observation: ClinicalObservationState) -> None:
    if observation.truth_kind != ClinicalObservationState.DETERMINISTIC_TRUTH_KIND:
        raise ValueError("current observation has unapproved truth kind")
    if observation.producer != ClinicalObservationState.APPROVED_PRODUCER:
        raise ValueError("current observation has unapproved producer")
    if observation.evidence_id != ClinicalObservationState.APPROVED_EVIDENCE_ID:
        raise ValueError("current observation has unapproved evidence ID")
    if observation.status not in {
        ClinicalObservationState.STATUS_ACTIVE,
        ClinicalObservationState.STATUS_INACTIVE,
    }:
        raise ValueError("current observation has unapproved status")
    if observation.evidence_strength not in {
        ClinicalObservationState.EVIDENCE_LIMITED,
        ClinicalObservationState.EVIDENCE_MODERATE,
        ClinicalObservationState.EVIDENCE_STRONG,
    }:
        raise ValueError("current observation has unapproved evidence density")


def _validate_snapshot(snapshot: CompanionReviewObservationSnapshot) -> None:
    if snapshot.truth_kind != snapshot.DETERMINISTIC_TRUTH_KIND:
        raise ValueError("review snapshot has unapproved truth kind")
    if snapshot.producer != snapshot.APPROVED_PRODUCER:
        raise ValueError("review snapshot has unapproved producer")
    if snapshot.evidence_id != snapshot.APPROVED_EVIDENCE_ID:
        raise ValueError("review snapshot has unapproved evidence ID")
    if snapshot.status not in {snapshot.STATUS_ACTIVE, snapshot.STATUS_INACTIVE}:
        raise ValueError("review snapshot has unapproved status")
    if snapshot.evidence_strength not in {
        snapshot.EVIDENCE_LIMITED,
        snapshot.EVIDENCE_MODERATE,
        snapshot.EVIDENCE_STRONG,
    }:
        raise ValueError("review snapshot has unapproved evidence density")


@transaction.atomic
def capture_companion_review_anchor(*, patient_id: int) -> CompanionReviewAnchor:
    """Capture an immutable, server-timestamped checkpoint of governed observations.

    The patient row lock is shared with canonical Clinical Twin refresh/erasure so
    the snapshot cannot interleave with a write that changes its source truth.
    """

    _validate_patient_id(patient_id)
    get_user_model().objects.select_for_update().only("pk").get(pk=patient_id)

    observations = list(
        ClinicalObservationState.objects.filter(patient_id=patient_id).order_by(
            "observation_key"
        )
    )
    for observation in observations:
        _validate_current_observation(observation)

    anchor = CompanionReviewAnchor.objects.create(patient_id=patient_id)
    CompanionReviewObservationSnapshot.objects.bulk_create(
        [
            CompanionReviewObservationSnapshot(
                anchor=anchor,
                observation_key=observation.observation_key,
                truth_kind=observation.truth_kind,
                status=observation.status,
                first_seen_at=observation.first_seen_at,
                last_seen_at=observation.last_seen_at,
                status_changed_at=observation.status_changed_at,
                last_refreshed_at=observation.last_refreshed_at,
                recurrence_count=observation.recurrence_count,
                evidence_strength=observation.evidence_strength,
                baseline_delta_mg_dl=observation.baseline_delta_mg_dl,
                observation_median_glucose_mg_dl=(
                    observation.observation_median_glucose_mg_dl
                ),
                window_median_glucose_mg_dl=observation.window_median_glucose_mg_dl,
                evidence_window_days=observation.evidence_window_days,
                evidence_id=observation.evidence_id,
                producer=observation.producer,
                evidence_fingerprint=observation.last_evidence_fingerprint,
            )
            for observation in observations
        ]
    )
    return anchor


def _build_change_item(
    *,
    observation_key: str,
    change_kind: ChangeKind,
    evidence_id: str,
    producer: str,
    evidence_strength: str,
    first_seen_at: datetime | None,
    last_seen_at: datetime | None,
    baseline_delta_at_review_mg_dl: float | None,
    baseline_delta_now_mg_dl: float | None,
    limitations: tuple[str, ...],
    missing_data: tuple[str, ...] = (),
) -> CompanionChangeItem:
    evidence_context = build_companion_evidence_context(
        evidence_id=evidence_id,
        producer=producer,
        evidence_density=evidence_strength,
        evidence_density_trend=None,
        missing_data=missing_data,
        limitations=limitations,
    )
    return _build_change_item(
        observation_key=observation_key,
        change_kind=change_kind,
        evidence_id=evidence_id,
        producer=producer,
        evidence_strength=evidence_strength,
        first_seen_at=first_seen_at,
        last_seen_at=last_seen_at,
        baseline_delta_at_review_mg_dl=baseline_delta_at_review_mg_dl,
        baseline_delta_now_mg_dl=baseline_delta_now_mg_dl,
        limitations=limitations,
        missing_data=missing_data,
        evidence_context=evidence_context,
    )


def _unknown_item(
    *,
    key: str,
    previous: CompanionReviewObservationSnapshot | None,
    current: ClinicalObservationState | None,
    reason: str,
) -> CompanionChangeItem:
    source = current or previous
    assert source is not None
    limitations = _COMMON_LIMITATIONS + (reason,)
    return _build_change_item(
        observation_key=key,
        change_kind="unknown",
        evidence_id=source.evidence_id,
        producer=source.producer,
        evidence_strength=source.evidence_strength,
        first_seen_at=getattr(current, "first_seen_at", None)
        or getattr(previous, "first_seen_at", None),
        last_seen_at=getattr(current, "last_seen_at", None)
        or getattr(previous, "last_seen_at", None),
        baseline_delta_at_review_mg_dl=(
            float(previous.baseline_delta_mg_dl) if previous is not None else None
        ),
        baseline_delta_now_mg_dl=(
            float(current.baseline_delta_mg_dl) if current is not None else None
        ),
        limitations=limitations,
        missing_data=(reason,),
    )


def _classify_change(
    *,
    anchor: CompanionReviewAnchor,
    previous: CompanionReviewObservationSnapshot | None,
    current: ClinicalObservationState | None,
) -> CompanionChangeItem | None:
    key = (
        current.observation_key
        if current is not None
        else previous.observation_key  # type: ignore[union-attr]
    )

    if previous is None:
        assert current is not None
        if current.first_seen_at <= anchor.captured_at:
            return _unknown_item(
                key=key,
                previous=None,
                current=current,
                reason="anchor_missing_state_that_predates_review",
            )
        if current.status == ClinicalObservationState.STATUS_ACTIVE:
            change_kind: ChangeKind = "new"
            extra = ("first_observed_after_explicit_companion_review",)
        elif current.status_changed_at > anchor.captured_at:
            change_kind = "resolved"
            extra = ("first_observed_and_resolved_after_explicit_companion_review",)
        else:
            return _unknown_item(
                key=key,
                previous=None,
                current=current,
                reason="post_review_transition_not_provable",
            )
        return _build_change_item(
            observation_key=key,
            change_kind=change_kind,
            evidence_id=current.evidence_id,
            producer=current.producer,
            evidence_strength=current.evidence_strength,
            first_seen_at=current.first_seen_at,
            last_seen_at=current.last_seen_at,
            baseline_delta_at_review_mg_dl=None,
            baseline_delta_now_mg_dl=float(current.baseline_delta_mg_dl),
            limitations=_COMMON_LIMITATIONS + extra,
        )

    if current is None:
        return _unknown_item(
            key=key,
            previous=previous,
            current=None,
            reason="current_governed_state_missing_cannot_infer_resolution",
        )

    if previous.status == previous.STATUS_INACTIVE:
        if current.status == ClinicalObservationState.STATUS_INACTIVE:
            return None
        if (
            current.status_changed_at > anchor.captured_at
            and current.last_seen_at > anchor.captured_at
        ):
            return _build_change_item(
                observation_key=key,
                change_kind="new",
                evidence_id=current.evidence_id,
                producer=current.producer,
                evidence_strength=current.evidence_strength,
                first_seen_at=current.first_seen_at,
                last_seen_at=current.last_seen_at,
                baseline_delta_at_review_mg_dl=float(previous.baseline_delta_mg_dl),
                baseline_delta_now_mg_dl=float(current.baseline_delta_mg_dl),
                limitations=_COMMON_LIMITATIONS + ("reactivated_after_review",),
            )
        return _unknown_item(
            key=key,
            previous=previous,
            current=current,
            reason="reactivation_after_review_not_provable",
        )

    if current.status == ClinicalObservationState.STATUS_INACTIVE:
        if (
            current.status_changed_at > anchor.captured_at
            and current.last_refreshed_at > anchor.captured_at
        ):
            return _build_change_item(
                observation_key=key,
                change_kind="resolved",
                evidence_id=current.evidence_id,
                producer=current.producer,
                evidence_strength=current.evidence_strength,
                first_seen_at=current.first_seen_at,
                last_seen_at=current.last_seen_at,
                baseline_delta_at_review_mg_dl=float(previous.baseline_delta_mg_dl),
                baseline_delta_now_mg_dl=float(current.baseline_delta_mg_dl),
                limitations=_COMMON_LIMITATIONS + (
                    "resolved_by_governed_clinical_twin_lifecycle",
                ),
            )
        return _unknown_item(
            key=key,
            previous=previous,
            current=current,
            reason="resolution_after_review_not_provable",
        )

    if (
        current.last_refreshed_at <= anchor.captured_at
        or current.last_seen_at <= anchor.captured_at
    ):
        return _unknown_item(
            key=key,
            previous=previous,
            current=current,
            reason="no_eligible_post_review_evidence",
        )

    previous_delta = float(previous.baseline_delta_mg_dl)
    current_delta = float(current.baseline_delta_mg_dl)
    if abs(current_delta) < abs(previous_delta):
        change_kind = "improving"
        extra = (
            "descriptive_delta_moved_toward_personal_window_baseline",
            "improving_does_not_mean_treatment_response_or_clinical_outcome",
        )
    else:
        change_kind = "persisting"
        extra = ("eligible_observation_remains_active_after_review",)

    return _build_change_item(
        observation_key=key,
        change_kind=change_kind,
        evidence_id=current.evidence_id,
        producer=current.producer,
        evidence_strength=current.evidence_strength,
        first_seen_at=current.first_seen_at,
        last_seen_at=current.last_seen_at,
        baseline_delta_at_review_mg_dl=previous_delta,
        baseline_delta_now_mg_dl=current_delta,
        limitations=_COMMON_LIMITATIONS + extra,
    )


@transaction.atomic
def compare_since_last_companion_review(*, patient_id: int) -> CompanionChangeResult:
    """Compare current governed observations with the latest explicit review anchor."""

    _validate_patient_id(patient_id)
    get_user_model().objects.select_for_update().only("pk").get(pk=patient_id)

    anchor = (
        CompanionReviewAnchor.objects.filter(patient_id=patient_id)
        .prefetch_related("observation_snapshots")
        .first()
    )
    if anchor is None:
        return CompanionChangeResult(
            status="insufficient_anchor",
            anchor_id=None,
            anchor_captured_at=None,
            changes=(),
            missing_data=("no_explicit_companion_review_anchor",),
            limitations=(
                "change_since_review_unavailable_without_server_captured_anchor",
            ),
        )

    if anchor.source != CompanionReviewAnchor.SOURCE_EXPLICIT_REVIEW:
        raise ValueError("review anchor has unapproved source")
    if anchor.snapshot_version != CompanionReviewAnchor.SNAPSHOT_VERSION:
        raise ValueError("review anchor has unapproved snapshot version")

    previous_by_key = {
        snapshot.observation_key: snapshot
        for snapshot in anchor.observation_snapshots.all()
    }
    for snapshot in previous_by_key.values():
        _validate_snapshot(snapshot)

    current_by_key = {
        observation.observation_key: observation
        for observation in ClinicalObservationState.objects.filter(
            patient_id=patient_id
        ).order_by("observation_key")
    }
    for observation in current_by_key.values():
        _validate_current_observation(observation)

    changes: list[CompanionChangeItem] = []
    for key in sorted(set(previous_by_key) | set(current_by_key)):
        change = _classify_change(
            anchor=anchor,
            previous=previous_by_key.get(key),
            current=current_by_key.get(key),
        )
        if change is not None:
            changes.append(change)

    return CompanionChangeResult(
        status="ready",
        anchor_id=anchor.id,
        anchor_captured_at=anchor.captured_at,
        changes=tuple(changes),
        missing_data=(),
        limitations=(
            "comparison_is_descriptive_and_patient_baseline_relative",
            "review_anchor_means_explicit_companion_review_not_clinician_consultation",
            "no_diagnosis_causality_treatment_response_or_future_prediction",
        ),
    )
