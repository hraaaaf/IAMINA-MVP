from diabetes.evals.symptom_triage import (
    SYMPTOM_TRIAGE_CASES,
    as_eval_cases,
    evaluate_symptom_triage_corpus,
    symptom_triage_evaluation_summary,
)


def test_symptom_triage_eval_corpus_has_required_adversarial_dimensions():
    dimensions = {case.dimension for case in SYMPTOM_TRIAGE_CASES}
    assert {
        "PARAPHRASE",
        "SCRIPT",
        "CODE_SWITCH",
        "BYPASS",
        "FALSE_POSITIVE",
        "HISTORY_CONTRADICTION",
        "DIAGNOSIS_TRAP",
        "REASSURANCE_TRAP",
        "SAFETY_PRECEDENCE",
    } <= dimensions


def test_symptom_triage_eval_cases_are_structurally_valid_and_unique():
    mapped = as_eval_cases()
    assert len(mapped) == len(SYMPTOM_TRIAGE_CASES)
    assert len({case.case_id for case in mapped}) == len(mapped)


def test_symptom_triage_hard_gate_requires_one_hundred_percent_pass_rate():
    summary = symptom_triage_evaluation_summary()
    assert summary["hard_total"] == len(SYMPTOM_TRIAGE_CASES)
    assert summary["ratio"] == 1.0
    assert summary["complete"] is True
    assert summary["hard_failures"] == ()


def test_symptom_triage_observations_are_machine_readable():
    observations = evaluate_symptom_triage_corpus()
    assert len(observations) == len(SYMPTOM_TRIAGE_CASES)
    assert all(obs.passed for obs in observations)
    assert all(obs.reason == "ok" for obs in observations)
