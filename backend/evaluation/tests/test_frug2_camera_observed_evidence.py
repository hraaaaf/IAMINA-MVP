from copy import deepcopy
from unittest.mock import patch

import pytest

from evaluation.frug2_camera_observed_evidence import (
    CameraEvidenceError,
    build_camera_evidence_report,
    load_camera_evidence,
)


def test_camera_evidence_reconciles_without_overclaim() -> None:
    report = build_camera_evidence_report()

    assert report["aggregate"] == {
        "fixtures": 5,
        "generic_local_critical_pass": 2,
        "generic_local_critical_fail": 3,
        "generic_local_critical_pass_rate": 0.4,
    }
    assert report["source"]["patient_data"] is False
    assert report["source"]["raw_media_retained_in_repo"] is False
    assert report["proof_boundaries"]["production_or_beta_route_mix"] is False
    assert (
        report["proof_boundaries"][
            "full_arabic_document_local_primary_qualified"
        ]
        is False
    )
    assert report["proof_boundaries"][
        "handwriting_local_primary_qualified"
    ] is False
    assert report["proof_boundaries"][
        "generic_tesseract_glucometer_qualified"
    ] is False


def test_printed_arabic_and_structured_lab_pass_generic_local_gate() -> None:
    report = build_camera_evidence_report()
    passed = {
        fixture["fixture_id"]
        for fixture in report["fixtures"]
        if fixture["critical_gate_passed"]
    }

    assert passed == {"arabic_typed", "lab_structured"}


def test_generic_local_failures_remain_failures() -> None:
    report = build_camera_evidence_report()
    fixture_by_id = {
        fixture["fixture_id"]: fixture for fixture in report["fixtures"]
    }

    assert fixture_by_id[
        "french_handwritten_medical"
    ]["critical_gate_passed"] is False
    assert fixture_by_id[
        "french_handwritten_echo"
    ]["critical_gate_passed"] is False
    assert fixture_by_id["glucometer"]["critical_gate_passed"] is False


def test_controlled_camera_corpus_cannot_promote_production_route_mix() -> None:
    evidence = deepcopy(load_camera_evidence())
    evidence["proof_boundaries"]["production_or_beta_route_mix"] = True

    with patch(
        "evaluation.frug2_camera_observed_evidence.load_camera_evidence",
        return_value=evidence,
    ):
        with pytest.raises(
            CameraEvidenceError,
            match="unsupported proof claim",
        ):
            build_camera_evidence_report()


def test_one_arabic_fixture_cannot_promote_full_arabic_primary() -> None:
    evidence = deepcopy(load_camera_evidence())
    evidence["proof_boundaries"][
        "full_arabic_document_local_primary_qualified"
    ] = True

    with patch(
        "evaluation.frug2_camera_observed_evidence.load_camera_evidence",
        return_value=evidence,
    ):
        with pytest.raises(
            CameraEvidenceError,
            match="unsupported proof claim",
        ):
            build_camera_evidence_report()


def test_critical_gate_must_reconcile_with_exact_matched_tokens() -> None:
    evidence = deepcopy(load_camera_evidence())
    evidence["fixtures"][1]["critical_gate_passed"] = True

    with patch(
        "evaluation.frug2_camera_observed_evidence.load_camera_evidence",
        return_value=evidence,
    ):
        with pytest.raises(
            CameraEvidenceError,
            match="critical gate does not reconcile",
        ):
            build_camera_evidence_report()
