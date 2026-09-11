from evaluation.p5_1_linguistic_review_benchmark_v6 import CASES
from evaluation.p5_1_linguistic_review_benchmark_v7 import (
    DATASET_ID,
    SYSTEM_PROMPT,
    batch_payload,
    locale_requirement,
    strict_machine_review,
)


def _case(case_id: str):
    return next(case for case in CASES if case.case_id == case_id)


def test_v7_contract_identity_and_targeted_msa_rule():
    assert DATASET_ID == "iamina-p5-1-current-sha-linguistic-review-v7"
    assert "current MSA lane specifically" in SYSTEM_PROMPT
    assert "بسهولة" in SYSTEM_PROMPT
    requirement = locale_requirement(_case("msa"))
    assert "no-pressure/no-blame" in requirement
    assert "بسهولة" in requirement
    assert "easy/easily" in requirement


def test_v7_payload_carries_explicit_msa_constraint():
    payload = batch_payload()
    assert "بسهولة" in payload
    assert "no-pressure/no-blame" in payload


def test_v7_keeps_v6_gate_rejecting_failed_msa_output():
    checks = strict_machine_review(
        _case("msa"),
        "لا تقلق، يمكنك العودة غداً بسهولة.",
    )
    assert checks["current_pilot_neutral_non_patronizing"] is False


def test_v7_accepts_clean_msa_candidate():
    checks = strict_machine_review(
        _case("msa"),
        "لا بأس، يمكنك العودة غداً دون ضغط أو لوم.",
    )
    assert all(checks.values())


def test_v7_does_not_change_clean_darija_candidates():
    candidates = {
        "darija_ma": "ماشي مشكل، غدا رجع بشوية عليك بلا ضغط.",
        "darija_latin": "Ma kayn bass, ghdda rje3 b chwiya bla daght.",
        "code_switch_fr_darija": "Demain, reprends tranquillement, وغدا رجع بشوية عليك.",
    }
    for case_id, reply in candidates.items():
        checks = strict_machine_review(_case(case_id), reply)
        assert all(checks.values()), (case_id, checks)
