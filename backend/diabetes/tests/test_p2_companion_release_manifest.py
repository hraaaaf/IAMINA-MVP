REQUIRED_RELEASE_TESTS = (
    "test_p2_companion_smart_suggestions.py",
    "test_p2_companion_consultation_companion.py",
    "test_p2_companion_after_visit_continuity_contract.py",
    "test_p2_companion_after_visit_runtime.py",
    "test_p2_companion_evidence_uncertainty.py",
    "test_p2_companion_change_since_review.py",
    "test_p2_companion_personal_patterns.py",
    "test_p2_companion_overview.py",
    "test_p2_companion_overview_api.py",
    "test_clinical_semantics_hardening.py",
    "test_clinical_shield.py",
    "test_advice_filter.py",
)


def test_companion_release_regression_manifest_is_complete() -> None:
    path_type = __import__("pathlib").Path
    tests_dir = path_type(__file__).resolve().parent
    missing = [name for name in REQUIRED_RELEASE_TESTS if not (tests_dir / name).is_file()]
    assert missing == [], f"missing required release regression tests: {missing}"
