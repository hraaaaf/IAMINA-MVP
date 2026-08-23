import pytest

from llm.cost_ledger import BillingEvidence, reconcile_month


def _billing_evidence() -> BillingEvidence:
    return BillingEvidence(
        provider="groq",
        billing_period="2026-08",
        source_kind="dashboard_export",
        reference="controlled-dashboard-export-sha256",
    )


def test_monthly_cost_reconciliation_reports_per_mau_workloads_and_coverage():
    snapshot = reconcile_month(
        active_users=10_000,
        billed_microusd=10_000_000,
        workload_costs_microusd={
            "conversation": 5_000_000,
            "summary": 2_000_000,
            "ocr": 2_600_000,
        },
        billing_evidence=_billing_evidence(),
    )

    assert snapshot.explained_microusd == 9_600_000
    assert snapshot.unexplained_microusd == 400_000
    assert snapshot.reconciliation_ratio == pytest.approx(0.96)
    assert snapshot.billed_microusd_per_mau == pytest.approx(1_000)
    assert snapshot.costs_by_workload_microusd == {
        "conversation": 5_000_000,
        "ocr": 2_600_000,
        "summary": 2_000_000,
    }
    assert snapshot.reconciliation_status() == "reconciled"
    assert snapshot.meets_reconciliation_floor()


def test_mathematical_coverage_without_billing_proof_cannot_certify_frug0():
    snapshot = reconcile_month(
        active_users=100,
        billed_microusd=1_000,
        workload_costs_microusd={"conversation": 1_000},
    )

    assert snapshot.reconciliation_ratio == 1.0
    assert snapshot.reconciliation_status() == "unresolved_without_billing_evidence"
    assert not snapshot.meets_reconciliation_floor()


def test_explicit_zero_bill_can_reconcile_only_with_traceable_billing_evidence():
    snapshot = reconcile_month(
        active_users=25,
        billed_microusd=0,
        workload_costs_microusd={},
        billing_evidence=BillingEvidence(
            provider="groq",
            billing_period="2026-08",
            source_kind="provider_statement",
            reference="zero-bill-statement-sha256",
        ),
    )

    assert snapshot.reconciliation_ratio == 1.0
    assert snapshot.billed_microusd_per_mau == 0.0
    assert snapshot.meets_reconciliation_floor()


def test_billing_evidence_fails_closed_when_not_traceable():
    with pytest.raises(ValueError, match="billing_period must be YYYY-MM"):
        reconcile_month(
            active_users=100,
            billed_microusd=100,
            workload_costs_microusd={"conversation": 100},
            billing_evidence=BillingEvidence(
                provider="groq",
                billing_period="2026-13",
                source_kind="invoice",
                reference="invoice-reference",
            ),
        )

    with pytest.raises(ValueError, match="unsupported billing evidence kind"):
        reconcile_month(
            active_users=100,
            billed_microusd=100,
            workload_costs_microusd={"conversation": 100},
            billing_evidence=BillingEvidence(
                provider="groq",
                billing_period="2026-08",
                source_kind="assumption",
                reference="not-provider-proof",
            ),
        )


def test_monthly_cost_reconciliation_fails_closed_on_impossible_inputs():
    with pytest.raises(ValueError, match="explained cost cannot exceed billed cost"):
        reconcile_month(
            active_users=100,
            billed_microusd=100,
            workload_costs_microusd={"conversation": 101},
            billing_evidence=_billing_evidence(),
        )

    with pytest.raises(ValueError, match="active_users must be positive"):
        reconcile_month(
            active_users=0,
            billed_microusd=0,
            workload_costs_microusd={},
            billing_evidence=_billing_evidence(),
        )
