"""V1-02: explicit V2-C/V2-D source evidence is never silently merged."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from diabetes.contracts.governed_longitudinal import GovernedLongitudinalContract
from diabetes.contracts.multi_source_fusion import (
    FusionPopulation,
    GovernedGlucoseFusionContract,
)
from diabetes.models import CGMReadingRecord, CGMSensorSession, LogEntry
from diabetes.services.clinical.governed_longitudinal import (
    compute_governed_longitudinal_intelligence,
)
from diabetes.services.clinical.patient_intelligence_envelope import (
    GovernedSourceRequest,
    build_patient_intelligence_envelope,
)
from diabetes.services.import_identity import make_import_client_uuid

pytestmark = pytest.mark.django_db

START = datetime(2026, 9, 1, tzinfo=UTC)
END = datetime(2026, 9, 5, tzinfo=UTC)


def _contract():
    return GovernedLongitudinalContract(
        fusion_contract=GovernedGlucoseFusionContract.journal_with(
            FusionPopulation.IMPORT
        )
    )


def _request():
    return GovernedSourceRequest(
        window_start=START,
        window_end=END,
        contract=_contract(),
    )


def _seed(patient, *, source, when, glucose):
    extra = {}
    if source == "import":
        extra["client_uuid"] = make_import_client_uuid(patient.id, when, glucose)
    return LogEntry.objects.create(
        patient=patient,
        source=source,
        logged_at=when,
        blood_sugar=glucose,
        **extra,
    )


def test_no_source_request_never_queries_fusion():
    patient = get_user_model().objects.create_user(username="v1-02-no-fusion")
    with patch(
        "diabetes.services.clinical.patient_intelligence_envelope."
        "compute_governed_longitudinal_intelligence"
    ) as fusion:
        result = build_patient_intelligence_envelope(patient_id=patient.id)
        fusion.assert_not_called()

    assert result.status == "insufficient_data"
    assert result.longitudinal_sources is None


def test_source_separation_reuses_governed_authority_and_patient_scope():
    patient = get_user_model().objects.create_user(username="v1-02-fusion")
    other = get_user_model().objects.create_user(username="v1-02-fusion-other")
    own = []
    for i, glucose in enumerate((110, 120, 130)):
        day = START + timedelta(days=i // 2, hours=i)
        own.append(_seed(patient, source="manual", when=day, glucose=glucose))
        own.append(
            _seed(
                patient, source="import",
                when=day + timedelta(minutes=10),
                glucose=glucose + 5,
            )
        )
    foreign = _seed(
        other, source="manual", when=START + timedelta(hours=3), glucose=250
    )
    request = _request()

    result = build_patient_intelligence_envelope(
        patient_id=patient.id, source_request=request
    )

    assert result.status == "ready"
    assert result.observations == ()
    assert result.llm_egress_authorized is False
    sources = result.longitudinal_sources
    assert sources is not None
    assert sources.status == "ready"
    assert sources.contract_id == request.contract.contract_id
    assert sources.window_start == START
    assert sources.window_end == END
    assert tuple(x.population for x in sources.populations) == (
        FusionPopulation.IMPORT, FusionPopulation.JOURNAL,
    )
    medians = {x.population: x.median_glucose_mg_dl for x in sources.populations}
    assert medians == {
        FusionPopulation.JOURNAL: 120.0,
        FusionPopulation.IMPORT: 125.0,
    }
    refs = {
        item.population: set(item.source_refs)
        for item in sources.populations
    }
    assert refs[FusionPopulation.JOURNAL] == {
        f"log_entry:{row.id}" for row in own if row.source == "manual"
    }
    assert refs[FusionPopulation.IMPORT] == {
        f"log_entry:{row.id}" for row in own if row.source == "import"
    }
    assert f"log_entry:{foreign.id}" not in set().union(*refs.values())
    assert "population_boundaries_preserved" in sources.limitations


def test_insufficient_import_suppresses_its_median_without_inventing_readiness():
    patient = get_user_model().objects.create_user(username="v1-02-insufficient")
    for i, glucose in enumerate((110, 120, 130)):
        _seed(
            patient,
            source="manual",
            when=START + timedelta(days=i // 2, hours=i),
            glucose=glucose,
        )
    _seed(patient, source="import", when=START, glucose=145)

    result = build_patient_intelligence_envelope(
        patient_id=patient.id, source_request=_request()
    )

    assert result.status == "insufficient_data"
    sources = result.longitudinal_sources
    assert sources is not None
    assert sources.status == "insufficient_data"
    by_source = {x.population: x for x in sources.populations}
    assert by_source[FusionPopulation.JOURNAL].median_glucose_mg_dl == 120.0
    assert by_source[FusionPopulation.IMPORT].fact_count == 1
    assert by_source[FusionPopulation.IMPORT].median_glucose_mg_dl is None
    assert sources.missing_data == ("insufficient_import_evidence",)


@pytest.mark.parametrize("invalid", [object(), {}, "journal", 0])
def test_implicit_or_malformed_source_requests_fail_closed(invalid):
    patient = get_user_model().objects.create_user(username="v1-02-bad-source-" + str(type(invalid)))
    with patch(
        "diabetes.services.clinical.patient_intelligence_envelope."
        "compute_governed_longitudinal_intelligence"
    ) as fusion:
        with pytest.raises(ValueError, match="source_request"):
            build_patient_intelligence_envelope(
                patient_id=patient.id, source_request=invalid
            )
        fusion.assert_not_called()


def test_explicit_request_requires_governed_contract():
    patient = get_user_model().objects.create_user(username="v1-02-no-contract")
    request = GovernedSourceRequest(
        window_start=START, window_end=END, contract=None
    )
    with pytest.raises(ValueError, match="contract"):
        build_patient_intelligence_envelope(
            patient_id=patient.id, source_request=request
        )


def test_forged_cross_patient_fact_rejected_even_from_governed_producer():
    patient = get_user_model().objects.create_user(username="v1-02-fake-patient")
    _seed(patient, source="manual", when=START, glucose=120)
    genuine = compute_governed_longitudinal_intelligence(
        patient_id=patient.id,
        window_start=START,
        window_end=END,
        contract=_contract(),
    )
    original = genuine.facts[0]
    forged = replace(
        genuine,
        facts=(
            replace(
                original,
                fact=replace(original.fact, subject_ref="patient:999999"),
            ),
        ),
    )
    with patch(
        "diabetes.services.clinical.patient_intelligence_envelope."
        "compute_governed_longitudinal_intelligence",
        return_value=forged,
    ):
        with pytest.raises(ValueError, match="cross-patient"):
            build_patient_intelligence_envelope(
                patient_id=patient.id, source_request=_request()
            )


def test_forged_longitudinal_status_rejected():
    patient = get_user_model().objects.create_user(username="v1-02-fake-ready")
    _seed(patient, source="manual", when=START, glucose=120)
    genuine = compute_governed_longitudinal_intelligence(
        patient_id=patient.id,
        window_start=START,
        window_end=END,
        contract=_contract(),
    )
    forged = replace(genuine, status="ready")
    with patch(
        "diabetes.services.clinical.patient_intelligence_envelope."
        "compute_governed_longitudinal_intelligence",
        return_value=forged,
    ):
        with pytest.raises(ValueError, match="sufficiency"):
            build_patient_intelligence_envelope(
                patient_id=patient.id, source_request=_request()
            )


def test_unverified_import_legacy_cgm_and_wrong_session_are_excluded():
    patient = get_user_model().objects.create_user(username="v1-02-untrusted")
    other = get_user_model().objects.create_user(username="v1-02-wrong-session")
    manual = _seed(patient, source="manual", when=START, glucose=120)
    # Untrusted historical import lacks server-generated identity.
    _seed(patient, source="import", when=START, glucose=130)
    # Legacy LogEntry(cgm) is not an authorized normalized sensor reading.
    _seed(patient, source="cgm", when=START, glucose=160)
    session = CGMSensorSession.objects.create(
        patient=other,
        source="linx",
        session_key="v1-02-foreign-session",
        started_at=START,
        ended_at=END,
        expected_interval_minutes=5,
        timezone_name="UTC",
        end_reason=CGMSensorSession.EndReason.REPLACED,
    )
    CGMReadingRecord.objects.create(
        patient=patient,
        source="linx",
        session=session,
        recorded_at=START + timedelta(hours=1),
        glucose_mg_dl=170,
        dedupe_key="v1-02-cross-patient-session",
    )
    contract = GovernedLongitudinalContract(
        fusion_contract=GovernedGlucoseFusionContract.journal_with(
            FusionPopulation.IMPORT, FusionPopulation.CGM
        )
    )
    result = build_patient_intelligence_envelope(
        patient_id=patient.id,
        source_request=GovernedSourceRequest(
            window_start=START,
            window_end=END,
            contract=contract,
        ),
    )

    assert result.status == "insufficient_data"
    sources = result.longitudinal_sources
    assert sources is not None
    by_source = {item.population: item for item in sources.populations}
    assert by_source[FusionPopulation.JOURNAL].source_refs == (
        f"log_entry:{manual.id}",
    )
    assert by_source[FusionPopulation.IMPORT].fact_count == 0
    assert by_source[FusionPopulation.CGM].fact_count == 0
    assert all(item.median_glucose_mg_dl is None for item in sources.populations)
    assert set(sources.missing_data) == {
        "insufficient_journal_evidence",
        "insufficient_import_evidence",
        "insufficient_cgm_evidence",
    }
    assert "cgm_requires_valid_session_linkage" in sources.limitations


def test_source_window_must_be_explicit_and_time_zone_aware():
    patient = get_user_model().objects.create_user(username="v1-02-naive")
    bad = GovernedSourceRequest(
        window_start=datetime(2026, 9, 1),
        window_end=END,
        contract=_contract(),
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        build_patient_intelligence_envelope(
            patient_id=patient.id, source_request=bad
        )
