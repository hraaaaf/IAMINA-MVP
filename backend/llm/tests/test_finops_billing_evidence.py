import pytest

from llm.cost_ledger import BillingEvidence
from llm.finops_audit import build_finops_audit_report


def _report(*, billing_evidence=None, explained=950):
    return build_finops_audit_report(
        events=[],
        baseline_dimensions={},
        active_users=10,
        billed_microusd=1_000,
        workload_costs_microusd={"conversation": explained},
        billing_evidence=billing_evidence,
    )


def test_full_reconciliation_cannot_certify_without_billing_evidence():
    report = _report(explained=1_000)

    assert report["reconciliation"]["ratio"] == 1.0
    assert report["reconciliation"]["meets_floor"] is False


def test_valid_billing_evidence_can_certify_reconciliation_floor():
    evidence = BillingEvidence(
        provider="groq",
        billing_period="2026-08",
        source_kind="dashboard_export",
        reference="groq-usage-2026-08",
    )

    report = _report(billing_evidence=evidence, explained=950)

    assert report["reconciliation"]["ratio"] == 0.95
    assert report["reconciliation"]["meets_floor"] is True


def test_invalid_billing_evidence_fails_closed():
    evidence = BillingEvidence(
        provider="groq",
        billing_period="2026-08",
        source_kind="screenshot",
        reference="unqualified-proof",
    )

    with pytest.raises(ValueError, match="unsupported billing evidence kind"):
        _report(billing_evidence=evidence)
