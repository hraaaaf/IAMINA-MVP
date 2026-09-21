from diabetes.evals.food import (
    FOOD_CASES,
    as_eval_cases,
    evaluate_food_corpus,
    food_evaluation_summary,
)


def test_food_eval_corpus_has_required_adversarial_dimensions():
    dimensions = {case.dimension for case in FOOD_CASES}

    assert {
        "PARAPHRASE",
        "NEGATION",
        "CODE_SWITCH",
        "SCRIPT",
        "BYPASS",
        "FALSE_POSITIVE",
        "TYPO_ABBREVIATION",
        "MISSING_DATA",
        "HISTORY_CONTRADICTION",
    } <= dimensions


def test_food_eval_cases_are_structurally_valid_and_unique():
    mapped = as_eval_cases()

    assert len(mapped) == len(FOOD_CASES)
    assert len({case.case_id for case in mapped}) == len(mapped)


def test_food_hard_gate_requires_one_hundred_percent_pass_rate():
    summary = food_evaluation_summary()

    assert summary["hard_total"] == len(FOOD_CASES)
    assert summary["ratio"] == 1.0
    assert summary["complete"] is True
    assert summary["hard_failures"] == ()


def test_food_observations_are_machine_readable_and_explain_failures():
    observations = evaluate_food_corpus()

    assert len(observations) == len(FOOD_CASES)
    assert all(obs.passed for obs in observations)
    assert all(obs.reason == "ok" for obs in observations)


def test_food_hard_corpus_keeps_structural_provenance_complete():
    observations = evaluate_food_corpus()

    assert all(obs.reason != "missing_evidence_refs" for obs in observations)
    assert all(obs.reason != "missing_limitations" for obs in observations)
