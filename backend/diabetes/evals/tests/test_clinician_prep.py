from diabetes.evals.clinician_prep import (
    CLINICIAN_PREP_CASES,
    as_eval_cases,
    clinician_prep_evaluation_summary,
    evaluate_clinician_prep_corpus,
)


def test_clinician_prep_eval_corpus_has_required_dimensions():
    dimensions = {case.dimension for case in CLINICIAN_PREP_CASES}
    assert {
        "PARAPHRASE",
        "SCRIPT",
        "CODE_SWITCH",
        "BYPASS",
        "FALSE_POSITIVE",
        "MISSING_DATA",
        "HISTORY_CONTRADICTION",
        "TREATMENT_TRAP",
        "OVERRIDE_TRAP",
    } <= dimensions


def test_clinician_prep_eval_cases_are_structurally_valid_and_unique():
    mapped = as_eval_cases()
    assert len(mapped) == len(CLINICIAN_PREP_CASES)
    assert len({case.case_id for case in mapped}) == len(mapped)


def test_clinician_prep_hard_gate_requires_one_hundred_percent_pass_rate():
    summary = clinician_prep_evaluation_summary()
    assert summary["hard_total"] == len(CLINICIAN_PREP_CASES)
    assert summary["ratio"] == 1.0
    assert summary["complete"] is True
    assert summary["hard_failures"] == ()


def test_clinician_prep_observations_are_machine_readable():
    observations = evaluate_clinician_prep_corpus()
    assert len(observations) == len(CLINICIAN_PREP_CASES)
    assert all(obs.passed for obs in observations)
    assert all(obs.reason == "ok" for obs in observations)
