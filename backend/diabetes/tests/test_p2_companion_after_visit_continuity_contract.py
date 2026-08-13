from datetime import UTC, datetime, timedelta

import pytest

from diabetes.services.clinical.after_visit_continuity_contract import (
    AfterVisitChangeKind,
    AfterVisitContinuityEnvelope,
    AfterVisitFact,
    AfterVisitFactKind,
    AfterVisitNextStep,
    VisitAnchor,
)


def _at(hour: int) -> datetime:
    return datetime(2026, 8, 13, hour, tzinfo=UTC)


def test_explicit_visit_anchor_and_recorded_fact_are_allowed() -> None:
    anchor = VisitAnchor(occurred_at=_at(9), source="patient_confirmed_visit")
    fact = AfterVisitFact(
        key="follow_up.symptom_note_present",
        value=True,
        fact_kind=AfterVisitFactKind.PATIENT_RECORDED,
        source="patient_follow_up_record",
        recorded_at=_at(10),
        allowed_next_step=AfterVisitNextStep.FOLLOW_UP_RECORD,
    )

    envelope = AfterVisitContinuityEnvelope(
        visit_anchor=anchor,
        window_end=_at(11),
        facts=(fact,),
    )

    assert envelope.facts == (fact,)
    assert "temporal_association_is_not_treatment_efficacy" in envelope.limitations


def test_governed_derivation_requires_evidence_id() -> None:
    with pytest.raises(ValueError, match="requires evidence_id"):
        AfterVisitFact(
            key="interval.pattern_state",
            value="persisting",
            fact_kind=AfterVisitFactKind.GOVERNED_DERIVATION,
            source="diabetes.personal_response.v1",
            recorded_at=_at(10),
        )


def test_unknown_change_can_only_collect_missing_data() -> None:
    fact = AfterVisitFact(
        key="interval.pattern_state",
        value="unknown",
        fact_kind=AfterVisitFactKind.GOVERNED_DERIVATION,
        source="diabetes.personal_response.v1",
        evidence_id="rule.personal-response.repetition.v1",
        recorded_at=_at(10),
        change_kind=AfterVisitChangeKind.UNKNOWN,
        allowed_next_step=AfterVisitNextStep.COLLECT_MISSING_DATA,
        missing_data=("insufficient_post_visit_evidence",),
    )
    assert fact.allowed_next_step is AfterVisitNextStep.COLLECT_MISSING_DATA


@pytest.mark.parametrize(
    "next_step",
    [
        AfterVisitNextStep.MONITOR,
        AfterVisitNextStep.FOLLOW_UP_RECORD,
        AfterVisitNextStep.PREPARE_CLINICIAN_DISCUSSION,
    ],
)
def test_unknown_change_rejects_other_actions(next_step: AfterVisitNextStep) -> None:
    with pytest.raises(ValueError, match="only collect missing data"):
        AfterVisitFact(
            key="interval.pattern_state",
            value="unknown",
            fact_kind=AfterVisitFactKind.GOVERNED_DERIVATION,
            source="diabetes.personal_response.v1",
            evidence_id="rule.personal-response.repetition.v1",
            recorded_at=_at(10),
            change_kind=AfterVisitChangeKind.UNKNOWN,
            allowed_next_step=next_step,
            missing_data=("insufficient_post_visit_evidence",),
        )


def test_clinician_discussion_requires_explicit_clinician_recorded_fact() -> None:
    with pytest.raises(ValueError, match="explicit clinician-recorded fact"):
        AfterVisitFact(
            key="interval.pattern_state",
            value="persisting",
            fact_kind=AfterVisitFactKind.GOVERNED_DERIVATION,
            source="diabetes.personal_response.v1",
            evidence_id="rule.personal-response.repetition.v1",
            recorded_at=_at(10),
            allowed_next_step=AfterVisitNextStep.PREPARE_CLINICIAN_DISCUSSION,
        )


def test_fact_outside_visit_window_fails_closed() -> None:
    anchor = VisitAnchor(occurred_at=_at(9), source="patient_confirmed_visit")
    fact = AfterVisitFact(
        key="follow_up.recorded",
        value=True,
        fact_kind=AfterVisitFactKind.PATIENT_RECORDED,
        source="patient_follow_up_record",
        recorded_at=_at(8),
    )

    with pytest.raises(ValueError, match="outside continuity window"):
        AfterVisitContinuityEnvelope(
            visit_anchor=anchor,
            window_end=_at(11),
            facts=(fact,),
        )


def test_naive_timestamps_fail_closed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        VisitAnchor(
            occurred_at=datetime(2026, 8, 13, 9),
            source="patient_confirmed_visit",
        )


def test_window_end_must_follow_visit() -> None:
    anchor = VisitAnchor(occurred_at=_at(9), source="patient_confirmed_visit")
    with pytest.raises(ValueError, match="must follow visit anchor"):
        AfterVisitContinuityEnvelope(
            visit_anchor=anchor,
            window_end=anchor.occurred_at - timedelta(seconds=1),
            facts=(),
        )
