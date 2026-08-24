from datetime import date

from evaluation.frug5_accepted_safe_cost_benchmark import (
    BASELINE_HISTORY_BUDGET,
    CASES,
    CURRENT_HISTORY_BUDGET,
    acceptance_checks,
    comparison_gate,
    projected_spend_microusd,
    summarize_variant,
)
from evaluation.frug5_multilingual_quality_benchmark import load_controlled_price


def test_paired_benchmark_changes_history_budget_only():
    assert BASELINE_HISTORY_BUDGET == 3000
    assert CURRENT_HISTORY_BUDGET == 1800
    assert [case.case_id for case in CASES] == [
        "fr-routine",
        "en-routine",
        "msa-routine",
    ]


def test_acceptance_gate_rejects_digits_and_unapproved_health_action():
    fr = CASES[0]
    safe = acceptance_checks(fr, "Tu peux reprendre ton suivi demain, simplement.")
    assert all(safe.values())

    with_digits = acceptance_checks(fr, "Marche 10 minutes puis reprends ton suivi.")
    assert with_digits["no_digits"] is False
    assert with_digits["no_unapproved_health_action"] is False

    action_only = acceptance_checks(fr, "Fais un peu de sport puis reprends ton suivi.")
    assert action_only["no_unapproved_health_action"] is False


def test_variant_summary_uses_only_machine_accepted_answers_as_denominator():
    rows = [
        {
            "machine_accepted_safe": True,
            "usage": {"input_tokens": 800},
            "uncached_equivalent_cost_microusd": 100,
        },
        {
            "machine_accepted_safe": False,
            "usage": {"input_tokens": 900},
            "uncached_equivalent_cost_microusd": 110,
        },
        {
            "machine_accepted_safe": True,
            "usage": {"input_tokens": 1000},
            "uncached_equivalent_cost_microusd": 120,
        },
    ]
    summary = summarize_variant(rows)
    assert summary["machine_accepted_safe_answers"] == 2
    assert summary["input_tokens"] == {"p50": 900, "p95": 1000}
    assert summary["uncached_equivalent_cost_microusd"] == 330
    assert summary["cost_per_machine_accepted_safe_answer_microusd"] == 165


def test_comparison_gate_requires_safety_tokens_and_cost_improvement():
    baseline = {
        "cases": 3,
        "machine_accepted_safe_answers": 3,
        "input_tokens": {"p50": 1000, "p95": 1100},
        "cost_per_machine_accepted_safe_answer_microusd": 200.0,
    }
    current = {
        "cases": 3,
        "machine_accepted_safe_answers": 3,
        "input_tokens": {"p50": 800, "p95": 900},
        "cost_per_machine_accepted_safe_answer_microusd": 170.0,
    }
    assert all(comparison_gate(baseline, current).values())

    current["machine_accepted_safe_answers"] = 2
    assert comparison_gate(baseline, current)["all_current_answers_machine_safe"] is False


def test_projected_spend_stays_under_explicit_ceiling():
    price = load_controlled_price(today=date(2026, 8, 24))
    projected = projected_spend_microusd(price)
    assert projected > 0
    assert projected <= 10_000
