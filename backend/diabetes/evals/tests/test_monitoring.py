from diabetes.evals.monitoring import (
    MONITORING_CASES,
    as_eval_cases,
    evaluate_monitoring_corpus,
    monitoring_evaluation_summary,
)


def test_monitoring_eval_corpus_has_required_adversarial_dimensions():
    dimensions = {case.dimension for case in MONITORING_CASES}

    assert {
        "PARAPHRASE",
        "SCRIPT",
        "CODE_SWITCH",
        "BYPASS",
        "FALSE_POSITIVE",
        "MISSING_DATA",
        "HISTORY_CONTRADICTION",
        "TREATMENT_TRAP",
    } <= dimensions


def test_monitoring_eval_cases_are_structurally_valid_and_unique():
    mapped = as_eval_cases()

    assert len(mapped) == len(MONITORING_CASES)
    assert len({case.case_id for case in mapped}) == len(mapped)


def test_monitoring_hard_gate_requires_one_hundred_percent_pass_rate():
    summary = monitoring_evaluation_summary()

    assert summary["hard_total"] == len(MONITORING_CASES)
    assert summary["ratio"] == 1.0
    assert summary["complete"] is True
    assert summary["hard_failures"] == ()


def test_monitoring_observations_are_machine_readable_and_explain_failures():
    observations = evaluate_monitoring_corpus()

    assert len(observations) == len(MONITORING_CASES)
    assert all(obs.passed for obs in observations)
    assert all(obs.reason == "ok" for obs in observations)


def test_monitoring_hard_corpus_keeps_provenance_and_safety_constraints():
    observations = evaluate_monitoring_corpus()

    assert all(obs.reason != "missing_evidence_refs" for obs in observations)
    assert all(obs.reason != "missing_limitations" for obs in observations)
    assert all(obs.reason != "treatment_change_not_forbidden" for obs in observations)
    assert all(obs.reason != "insulin_dose_not_forbidden" for obs in observations)
