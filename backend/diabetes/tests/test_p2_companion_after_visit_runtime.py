from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from diabetes.models import AfterVisitAnchor, AfterVisitFactRecord
from diabetes.services.clinical.after_visit_continuity import (
    assemble_after_visit_continuity,
    record_after_visit_anchor,
    record_after_visit_fact,
)
from diabetes.services.clinical.after_visit_continuity_contract import (
    AfterVisitFactKind,
    AfterVisitNextStep,
)

pytestmark = pytest.mark.django_db


def _patient(username: str = "after-visit-user"):
    return get_user_model().objects.create_user(username=username, password="x")


def test_consultation_must_be_explicit_and_patient_scoped():
    patient = _patient()
    occurred_at = timezone.now() - timedelta(days=2)

    anchor = record_after_visit_anchor(
        patient_id=patient.id,
        occurred_at=occurred_at,
        source=AfterVisitAnchor.SOURCE_PATIENT_RECORDED,
    )

    assert anchor.patient_id == patient.id
    assert anchor.occurred_at == occurred_at
    assert AfterVisitAnchor.objects.count() == 1


def test_runtime_records_structured_fact_and_projects_without_efficacy_claim():
    patient = _patient()
    occurred_at = timezone.now() - timedelta(days=2)
    recorded_at = occurred_at + timedelta(hours=1)
    anchor = record_after_visit_anchor(
        patient_id=patient.id,
        occurred_at=occurred_at,
        source=AfterVisitAnchor.SOURCE_CLINICIAN_RECORDED,
    )

    record_after_visit_fact(
        patient_id=patient.id,
        anchor_id=anchor.id,
        key="follow_up_plan_recorded",
        value=True,
        fact_kind=AfterVisitFactKind.CLINICIAN_RECORDED,
        source="clinician.explicit-record.v1",
        recorded_at=recorded_at,
    )
    envelope = assemble_after_visit_continuity(
        patient_id=patient.id,
        anchor_id=anchor.id,
        window_end=recorded_at + timedelta(days=1),
    )

    assert len(envelope.facts) == 1
    assert envelope.facts[0].allowed_next_step is AfterVisitNextStep.PREPARE_CLINICIAN_DISCUSSION
    assert "temporal_association_is_not_treatment_efficacy" in envelope.facts[0].limitations
    assert "no_diagnosis_prescription_dose_or_treatment_change_authority" in envelope.limitations


def test_governed_fact_requires_evidence_id():
    patient = _patient()
    occurred_at = timezone.now() - timedelta(days=1)
    anchor = record_after_visit_anchor(
        patient_id=patient.id,
        occurred_at=occurred_at,
        source=AfterVisitAnchor.SOURCE_PATIENT_RECORDED,
    )

    with pytest.raises(ValueError, match="requires evidence_id"):
        record_after_visit_fact(
            patient_id=patient.id,
            anchor_id=anchor.id,
            key="descriptive_change",
            value="changed",
            fact_kind=AfterVisitFactKind.GOVERNED_DERIVATION,
            source="governed.test.v1",
            recorded_at=occurred_at + timedelta(hours=1),
        )

    assert AfterVisitFactRecord.objects.count() == 0


def test_fact_cannot_predate_explicit_visit():
    patient = _patient()
    occurred_at = timezone.now() - timedelta(days=1)
    anchor = record_after_visit_anchor(
        patient_id=patient.id,
        occurred_at=occurred_at,
        source=AfterVisitAnchor.SOURCE_PATIENT_RECORDED,
    )

    with pytest.raises(ValueError, match="cannot predate"):
        record_after_visit_fact(
            patient_id=patient.id,
            anchor_id=anchor.id,
            key="symptom_note",
            value="none",
            fact_kind=AfterVisitFactKind.PATIENT_RECORDED,
            source="patient.explicit-record.v1",
            recorded_at=occurred_at - timedelta(seconds=1),
        )


def test_empty_interval_is_truthful_missing_data_not_false_resolution():
    patient = _patient()
    occurred_at = timezone.now() - timedelta(days=1)
    anchor = record_after_visit_anchor(
        patient_id=patient.id,
        occurred_at=occurred_at,
        source=AfterVisitAnchor.SOURCE_PATIENT_RECORDED,
    )

    envelope = assemble_after_visit_continuity(
        patient_id=patient.id,
        anchor_id=anchor.id,
        window_end=occurred_at + timedelta(days=1),
    )

    assert envelope.facts == ()
    assert envelope.missing_data == ("no_after_visit_facts_recorded",)


def test_account_deletion_cascades_after_visit_patient_records():
    patient = _patient()
    occurred_at = timezone.now() - timedelta(days=1)
    anchor = record_after_visit_anchor(
        patient_id=patient.id,
        occurred_at=occurred_at,
        source=AfterVisitAnchor.SOURCE_PATIENT_RECORDED,
    )
    record_after_visit_fact(
        patient_id=patient.id,
        anchor_id=anchor.id,
        key="patient_note_recorded",
        value=True,
        fact_kind=AfterVisitFactKind.PATIENT_RECORDED,
        source="patient.explicit-record.v1",
        recorded_at=occurred_at + timedelta(minutes=1),
    )

    patient.delete()

    assert AfterVisitAnchor.objects.count() == 0
    assert AfterVisitFactRecord.objects.count() == 0
