"""Deterministic P2-COMPANION-6 after-visit continuity runtime."""

from __future__ import annotations

from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import transaction

from diabetes.models.after_visit import AfterVisitAnchor, AfterVisitFactRecord
from diabetes.services.clinical.after_visit_continuity_contract import (
    AfterVisitChangeKind,
    AfterVisitContinuityEnvelope,
    AfterVisitFact,
    AfterVisitFactKind,
    AfterVisitNextStep,
    VisitAnchor,
)

_ALLOWED_ANCHOR_SOURCES = {
    AfterVisitAnchor.SOURCE_PATIENT_RECORDED,
    AfterVisitAnchor.SOURCE_CLINICIAN_RECORDED,
}


def _require_aware(value: datetime, *, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@transaction.atomic
def record_after_visit_anchor(*, patient_id: int, occurred_at: datetime, source: str) -> AfterVisitAnchor:
    """Persist one explicit consultation occurrence under the shared patient lock."""

    _require_aware(occurred_at, field_name="occurred_at")
    if source not in _ALLOWED_ANCHOR_SOURCES:
        raise ValueError("unsupported after-visit anchor source")

    get_user_model().objects.select_for_update().only("pk").get(pk=patient_id)
    return AfterVisitAnchor.objects.create(
        patient_id=patient_id,
        occurred_at=occurred_at,
        source=source,
    )


@transaction.atomic
def record_after_visit_fact(
    *,
    patient_id: int,
    anchor_id: int,
    key: str,
    value: str | int | float | bool,
    fact_kind: AfterVisitFactKind,
    source: str,
    recorded_at: datetime,
    evidence_id: str | None = None,
) -> AfterVisitFactRecord:
    """Persist one explicit structured fact; no clinical interpretation occurs here."""

    _require_aware(recorded_at, field_name="recorded_at")
    if not key.strip() or not source.strip():
        raise ValueError("fact key and source are required")

    get_user_model().objects.select_for_update().only("pk").get(pk=patient_id)
    anchor = AfterVisitAnchor.objects.select_for_update().get(
        pk=anchor_id,
        patient_id=patient_id,
    )
    if recorded_at < anchor.occurred_at:
        raise ValueError("after-visit fact cannot predate consultation anchor")
    if fact_kind is AfterVisitFactKind.GOVERNED_DERIVATION and not evidence_id:
        raise ValueError("governed derivation requires evidence_id")

    return AfterVisitFactRecord.objects.create(
        anchor=anchor,
        key=key,
        value=value,
        fact_kind=fact_kind.value,
        source=source,
        recorded_at=recorded_at,
        evidence_id=evidence_id or "",
    )


def assemble_after_visit_continuity(
    *, patient_id: int, anchor_id: int, window_end: datetime
) -> AfterVisitContinuityEnvelope:
    """Project persisted facts into the certified bounded contract."""

    _require_aware(window_end, field_name="window_end")
    anchor = AfterVisitAnchor.objects.get(pk=anchor_id, patient_id=patient_id)
    if window_end <= anchor.occurred_at:
        raise ValueError("window_end must follow visit anchor")

    projected: list[AfterVisitFact] = []
    for row in anchor.facts.filter(recorded_at__lte=window_end).order_by("recorded_at", "id"):
        kind = AfterVisitFactKind(row.fact_kind)
        next_step = (
            AfterVisitNextStep.PREPARE_CLINICIAN_DISCUSSION
            if kind is AfterVisitFactKind.CLINICIAN_RECORDED
            else AfterVisitNextStep.FOLLOW_UP_RECORD
        )
        projected.append(
            AfterVisitFact(
                key=row.key,
                value=row.value,
                fact_kind=kind,
                source=row.source,
                recorded_at=row.recorded_at,
                change_kind=AfterVisitChangeKind.CURRENT_STATE,
                allowed_next_step=next_step,
                evidence_id=row.evidence_id or None,
                limitations=(
                    "recorded_fact_only",
                    "temporal_association_is_not_treatment_efficacy",
                ),
            )
        )

    return AfterVisitContinuityEnvelope(
        visit_anchor=VisitAnchor(occurred_at=anchor.occurred_at, source=anchor.source),
        window_end=window_end,
        facts=tuple(projected),
        missing_data=() if projected else ("no_after_visit_facts_recorded",),
    )


__all__ = [
    "assemble_after_visit_continuity",
    "record_after_visit_anchor",
    "record_after_visit_fact",
]
