from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from diabetes.models import AfterVisitAnchor, ProactiveInsightState
from diabetes.services.clinical.companion_overview import build_companion_overview

pytestmark = pytest.mark.django_db


def _patient(username: str):
    return get_user_model().objects.create_user(username=username, password="x")


def test_empty_overview_is_truthful_and_read_only():
    patient = _patient("overview-empty")
    before_proactive = ProactiveInsightState.objects.count()

    result = build_companion_overview(patient_id=patient.id)

    assert result.pattern_status == "no_governed_patterns"
    assert result.review_status == "insufficient_anchor"
    assert result.patterns == ()
    assert result.changes_since_review == ()
    assert result.after_visit.status == "no_recorded_visit"
    assert result.after_visit.anchor_id is None
    assert ProactiveInsightState.objects.count() == before_proactive


def test_after_visit_summary_is_patient_scoped_and_non_mutating():
    patient = _patient("overview-owner")
    other = _patient("overview-other")
    occurred_at = timezone.now() - timedelta(days=1)
    other_anchor = AfterVisitAnchor.objects.create(
        patient=other,
        occurred_at=occurred_at - timedelta(days=1),
        source=AfterVisitAnchor.SOURCE_PATIENT_RECORDED,
    )
    own_anchor = AfterVisitAnchor.objects.create(
        patient=patient,
        occurred_at=occurred_at,
        source=AfterVisitAnchor.SOURCE_CLINICIAN_RECORDED,
    )

    result = build_companion_overview(patient_id=patient.id)

    assert result.after_visit.status == "recorded"
    assert result.after_visit.anchor_id == own_anchor.id
    assert result.after_visit.anchor_id != other_anchor.id
    assert result.after_visit.fact_count == 0
    assert result.after_visit.latest_fact_at is None
    assert AfterVisitAnchor.objects.count() == 2


def test_invalid_patient_identity_fails_closed():
    with pytest.raises(ValueError, match="positive integer"):
        build_companion_overview(patient_id=0)
