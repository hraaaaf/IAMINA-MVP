import pytest

from llm.cost_ledger import reconcile_month


def test_monthly_cost_reconciliation_reports_per_mau_and_coverage():
    snapshot = reconcile_month(
        active_users=10_000,
        billed_microusd=10_000_000,
        workload_costs_microusd={
            "conversation": 5_000_000,
            "summary": 2_000_000,
            "ocr": 2_600_000,
        },
    )

    assert snapshot.explained_microusd == 9_600_000
    assert snapshot.unexplained_microusd == 400_000
    assert snapshot.reconciliation_ratio == pytest.approx(0.96)
    assert snapshot.billed_microusd_per_mau == pytest.approx(1_000)
    assert snapshot.meets_reconciliation_floor()


def test_monthly_cost_reconciliation_fails_closed_on_impossible_inputs():
    with pytest.raises(ValueError, match="explained cost cannot exceed billed cost"):
        reconcile_month(
            active_users=100,
            billed_microusd=100,
            workload_costs_microusd={"conversation": 101},
        )

    with pytest.raises(ValueError, match="active_users must be positive"):
        reconcile_month(
            active_users=0,
            billed_microusd=0,
            workload_costs_microusd={},
        )
