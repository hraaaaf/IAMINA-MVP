from evaluation.frug2_camera_observed_evidence import (
    build_camera_observed_summary,
    load_camera_observed_evidence,
)


def test_retained_camera_evidence_is_content_free_and_reconciled() -> None:
    evidence = load_camera_observed_evidence()
    assert evidence["traffic"]["patient_data"] is False
    assert evidence["source"]["fixture_content_retained_in_repo"] is False
    assert evidence["aggregate"] == {
        "cases": 5,
        "generic_local_critical_pass_cases": 2,
        "generic_local_critical_fail_cases": 3,
    }


def test_camera_summary_preserves_fail_closed_policy() -> None:
    summary = build_camera_observed_summary()
    assert summary["case_results"]["arabic_typed"]["critical_token_recall"] == 1.0
    assert summary["case_results"]["lab_structured"]["critical_token_recall"] == 1.0
    assert summary["case_results"]["french_handwritten_medical"]["critical_token_recall"] == 0.0
    assert summary["case_results"]["french_handwritten_echo"]["critical_token_recall"] == 0.0
    assert summary["case_results"]["glucometer"]["critical_token_recall"] == 0.0
    policy = summary["policy_conclusion"]
    assert policy["full_arabic_local_primary_qualified"] is False
    assert policy["free_handwriting_generic_local_primary_qualified"] is False
    assert policy["generic_document_ocr_replaces_glucometer_lane"] is False
    assert summary["proof_boundaries"]["production_or_beta_route_mix"] is False
