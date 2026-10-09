"""V1-02 first-slice regressions: patient scope, provenance and fail-closed output."""

from dataclasses import replace
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.services.clinical.companion_pattern_intelligence import (
    project_personal_pattern_intelligence,
)
from diabetes.services.clinical.patient_intelligence_envelope import (
    ENVELOPE_VERSION,
    build_patient_intelligence_envelope,
)

pytestmark = pytest.mark.django_db


def _patient(name: str):
    return get_user_model().objects.create_user(username=name)


def _governed_observation(patient, *, key="context:stress"):
    now = timezone.now()
    recorded_context = {
        "context:stress": {"source_field": "stressed", "recorded_value": "yes"},
        "context:activity": {"source_field": "exercised", "recorded_value": "yes"},
    }
    return ClinicalObservationState.objects.create(
        patient=patient,
        observation_key=key,
        kind=ClinicalObservationState.KIND_CONTEXT,
        status=ClinicalObservationState.STATUS_ACTIVE,
        first_seen_at=now - timedelta(days=20),
        last_seen_at=now - timedelta(days=1),
        status_changed_at=now - timedelta(hours=12),
        recurrence_count=1,
        evidence_strength=ClinicalObservationState.EVIDENCE_MODERATE,
        previous_evidence_strength="",
        evidence_strength_trend=ClinicalObservationState.TREND_INITIAL,
        observations=6,
        distinct_days=4,
        observation_median_glucose_mg_dl=165.0,
        window_median_glucose_mg_dl=125.0,
        baseline_delta_mg_dl=40.0,
        evidence_window_days=90,
        evidence_id=ClinicalObservationState.APPROVED_EVIDENCE_ID,
        producer=ClinicalObservationState.APPROVED_PRODUCER,
        context_modifiers=recorded_context[key],
        last_evidence_fingerprint="a" * 64,
    )


def test_empty_patient_is_insufficient_not_a_negative_clinical_finding():
    own = _patient("v1-02-empty")
    other = _patient("v1-02-other-only")
    _governed_observation(other)

    result = build_patient_intelligence_envelope(patient_id=own.id)

    assert result.patient_id == own.id
    assert result.status == "insufficient_data"
    assert result.observations == ()
    assert "no_eligible_governed_patterns" in result.missing_data
    assert "absence_of_pattern_is_not_evidence_of_absence_of_clinical_issue" in (
        result.limitations
    )
    assert result.llm_egress_authorized is False


def test_patient_scoped_read_only_and_existing_evidence_only():
    own = _patient("v1-02-scoped")
    other = _patient("v1-02-scoped-other")
    row = _governed_observation(own)
    _governed_observation(other, key="context:activity")
    before_refresh = row.last_refreshed_at

    result = build_patient_intelligence_envelope(patient_id=own.id)

    assert result.source_version == ENVELOPE_VERSION
    assert result.patient_id == own.id
    assert result.status == "ready"
    assert result.missing_data == ()
    assert len(result.observations) == 1
    item = result.observations[0]
    assert item.observation_key == "context:stress"
    assert item.eligibility == "governed_clinical_twin_pattern"
    assert item.authority == "descriptive_only"
    assert item.evidence_window_days == 90
    assert item.provenance.evidence_id == row.evidence_id
    assert item.provenance.producer == row.producer
    assert item.provenance.clinical_authority == "governed_rule"
    assert item.uncertainty.evidence_density == "moderate"
    assert "previous_baseline_relative_delta_not_available" in (
        item.uncertainty.missing_data
    )
    assert item.first_observed_at == row.first_seen_at
    assert item.last_observed_at == row.last_seen_at
    assert result.llm_egress_authorized is False
    assert "not_authorized_for_llm_egress" in result.limitations
    assert not hasattr(item, "treatment_recommendation")
    assert not hasattr(item, "clinical_risk_score")
    row.refresh_from_db()
    assert row.last_refreshed_at == before_refresh


@pytest.mark.parametrize("patient_id", [0, -1, True, "1", None])
def test_invalid_subject_rejected_before_database(patient_id):
    with patch(
        "diabetes.services.clinical.patient_intelligence_envelope."
        "project_personal_pattern_intelligence"
    ) as upstream:
        with pytest.raises(ValueError, match="patient_id"):
            build_patient_intelligence_envelope(patient_id=patient_id)
        upstream.assert_not_called()


def test_corrupt_recorded_context_fails_closed():
    own = _patient("v1-02-corrupt")
    row = _governed_observation(own)
    row.context_modifiers = {"source_field": "stressed", "recorded_value": "no"}
    row.save(update_fields=["context_modifiers"])

    with pytest.raises(ValueError, match="recorded context"):
        build_patient_intelligence_envelope(patient_id=own.id)


@pytest.mark.parametrize("alteration", [
    {"evidence_density": "strong"},
    {"producer": "other.producer"},
    {"source_version": "unreviewed.v2"},
])
def test_upstream_provenance_or_version_mismatch_rejected(alteration):
    own = _patient("v1-02-alter-" + next(iter(alteration)))
    _governed_observation(own)
    genuine = project_personal_pattern_intelligence(patient_id=own.id)
    forged = replace(
        genuine, patterns=(replace(genuine.patterns[0], **alteration),)
    )

    with patch(
        "diabetes.services.clinical.patient_intelligence_envelope."
        "project_personal_pattern_intelligence",
        return_value=forged,
    ):
        with pytest.raises(ValueError):
            build_patient_intelligence_envelope(patient_id=own.id)


@pytest.mark.parametrize("status", ["ready", "unreviewed_status"])
def test_missing_or_unknown_upstream_status_rejected(status):
    own = _patient("v1-02-status-" + status)
    empty = project_personal_pattern_intelligence(patient_id=own.id)
    forged = replace(empty, status=status)

    with patch(
        "diabetes.services.clinical.patient_intelligence_envelope."
        "project_personal_pattern_intelligence",
        return_value=forged,
    ):
        with pytest.raises(ValueError):
            build_patient_intelligence_envelope(patient_id=own.id)


def test_forged_registry_summary_is_rejected():
    own = _patient("v1-02-registry-spoof")
    _governed_observation(own)
    result = project_personal_pattern_intelligence(patient_id=own.id)
    original = result.patterns[0]
    fake_provenance = replace(
        original.evidence_context.provenance,
        rule_summary="unreviewed medical claim",
    )
    forged_context = replace(
        original.evidence_context,
        provenance=fake_provenance,
    )
    fake_pattern = replace(original, evidence_context=forged_context)
    with patch(
        "diabetes.services.clinical.patient_intelligence_envelope."
        "project_personal_pattern_intelligence",
        return_value=replace(result, patterns=(fake_pattern,)),
    ):
        with pytest.raises(ValueError, match="governed registry"):
            build_patient_intelligence_envelope(patient_id=own.id)
