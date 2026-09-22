from diabetes.evals.activity import (
    ACTIVITY_CASES,
    activity_evaluation_summary,
    as_eval_cases,
    evaluate_activity_corpus,
)


def test_activity_eval_corpus_has_required_adversarial_dimensions():
    dimensions = {case.dimension for case in ACTIVITY_CASES}
    assert {
        "PARAPHRASE",
        "SCRIPT",
        "CODE_SWITCH",
        "BYPASS",
        "FALSE_POSITIVE",
        "MISSING_DATA",
        "HISTORY_CONTRADICTION",
        "COMPENSATION_TRAP",
        "TREATMENT_TRAP",
    } <= dimensions


def test_activity_eval_cases_are_structurally_valid_and_unique():
    mapped = as_eval_cases()
    assert len(mapped) == len(ACTIVITY_CASES)
    assert len({case.case_id for case in mapped}) == len(mapped)


def test_activity_hard_gate_requires_one_hundred_percent_pass_rate():
    summary = activity_evaluation_summary()
    assert summary["hard_total"] == len(ACTIVITY_CASES)
    assert summary["ratio"] == 1.0
    assert summary["complete"] is True
    assert summary["hard_failures"] == ()


def test_activity_observations_are_machine_readable_and_explain_failures():
    observations = evaluate_activity_corpus()
    assert len(observations) == len(ACTIVITY_CASES)
    assert all(obs.passed for obs in observations)
    assert all(obs.reason == "ok" for obs in observations)


def test_activity_hard_corpus_keeps_provenance_and_safety_constraints():
    observations = evaluate_activity_corpus()
    forbidden_reasons = {
        "missing_evidence_refs",
        "missing_limitations",
        "causality_not_forbidden",
        "exercise_prescription_not_forbidden",
        "compensatory_activity_not_forbidden",
        "treatment_change_not_forbidden",
        "insulin_dose_not_forbidden",
    }
    assert all(obs.reason not in forbidden_reasons for obs in observations)
