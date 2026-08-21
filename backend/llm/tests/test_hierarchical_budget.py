import pytest

from llm.budget import (
    BudgetConfigurationError,
    BudgetExceeded,
    InMemoryBudgetLedger,
)
from llm.hierarchical_budget import (
    BudgetThreshold,
    HierarchicalBudgetController,
    HierarchicalBudgetPolicy,
    derive_opaque_budget_operation_key,
)

KEY_MATERIAL = b"frug8b-synthetic-key-material-32bytes-plus"


def _policy() -> HierarchicalBudgetPolicy:
    return HierarchicalBudgetPolicy(
        global_budget=BudgetThreshold(100, 80),
        provider_budgets={
            "groq": BudgetThreshold(90, 70),
            "qwen": BudgetThreshold(100, 80),
        },
        workload_budgets={
            ("groq", "conversation"): BudgetThreshold(70, 50),
            ("qwen", "conversation"): BudgetThreshold(100, 80),
        },
        max_single_reservation_microusd=60,
    )


def _key(reference: str) -> str:
    return derive_opaque_budget_operation_key(
        key_material=KEY_MATERIAL,
        operation_reference=reference,
    )


def test_hierarchical_budget_is_atomic_when_workload_limit_blocks():
    ledger = InMemoryBudgetLedger()
    controller = HierarchicalBudgetController(policy=_policy(), ledger=ledger)

    controller.authorize(
        provider="groq",
        workload="conversation",
        month_key="2026-08",
        reserved_microusd=40,
        idempotency_key=_key("request-1"),
    )

    with pytest.raises(BudgetExceeded, match="workload"):
        controller.authorize(
            provider="groq",
            workload="conversation",
            month_key="2026-08",
            reserved_microusd=40,
            idempotency_key=_key("request-2"),
        )

    assert ledger.committed_microusd("finops:global", "2026-08") == 40
    assert ledger.committed_microusd("finops:provider:groq", "2026-08") == 40
    assert ledger.committed_microusd(
        "finops:workload:groq:conversation", "2026-08"
    ) == 40


def test_hierarchical_budget_returns_soft_threshold_signal_without_blocking():
    ledger = InMemoryBudgetLedger()
    controller = HierarchicalBudgetController(policy=_policy(), ledger=ledger)

    controller.authorize(
        provider="groq",
        workload="conversation",
        month_key="2026-08",
        reserved_microusd=40,
        idempotency_key=_key("request-1"),
    )
    second = controller.authorize(
        provider="groq",
        workload="conversation",
        month_key="2026-08",
        reserved_microusd=15,
        idempotency_key=_key("request-2"),
    )

    assert second.soft_alert_subject_keys == (
        "finops:workload:groq:conversation",
    )
    assert ledger.committed_microusd("finops:global", "2026-08") == 55


def test_hierarchical_bundle_retry_is_idempotent_across_all_scopes():
    ledger = InMemoryBudgetLedger()
    controller = HierarchicalBudgetController(policy=_policy(), ledger=ledger)
    key = _key("request-1")

    first = controller.authorize(
        provider="groq",
        workload="conversation",
        month_key="2026-08",
        reserved_microusd=40,
        idempotency_key=key,
    )
    duplicate = controller.authorize(
        provider="groq",
        workload="conversation",
        month_key="2026-08",
        reserved_microusd=40,
        idempotency_key=key,
    )

    assert tuple(item.reservation_id for item in duplicate.reservations) == tuple(
        item.reservation_id for item in first.reservations
    )
    assert ledger.committed_microusd("finops:global", "2026-08") == 40

    controller.settle(first, 25)
    assert ledger.committed_microusd("finops:global", "2026-08") == 25
    assert ledger.committed_microusd("finops:provider:groq", "2026-08") == 25
    assert ledger.committed_microusd(
        "finops:workload:groq:conversation", "2026-08"
    ) == 25


def test_hierarchical_budget_fails_closed_on_unknown_workload_or_noncanonical_month():
    controller = HierarchicalBudgetController(
        policy=_policy(),
        ledger=InMemoryBudgetLedger(),
    )

    with pytest.raises(BudgetConfigurationError, match="not explicitly configured"):
        controller.authorize(
            provider="groq",
            workload="summary",
            month_key="2026-08",
            reserved_microusd=10,
            idempotency_key=_key("request-1"),
        )

    with pytest.raises(BudgetConfigurationError, match="YYYY-MM"):
        controller.authorize(
            provider="groq",
            workload="conversation",
            month_key="2026-8",
            reserved_microusd=10,
            idempotency_key=_key("request-2"),
        )


def test_runtime_hierarchy_rejects_raw_idempotency_reference_and_derivation_hides_it():
    controller = HierarchicalBudgetController(
        policy=_policy(),
        ledger=InMemoryBudgetLedger(),
    )

    with pytest.raises(BudgetConfigurationError, match="opaque HMAC"):
        controller.authorize(
            provider="groq",
            workload="conversation",
            month_key="2026-08",
            reserved_microusd=10,
            idempotency_key="patient@example.test:request-123",
        )

    opaque = _key("patient@example.test:request-123")
    assert opaque.startswith("hmac256:")
    assert "patient@example.test" not in opaque
