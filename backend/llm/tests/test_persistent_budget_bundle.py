from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from llm.budget import BudgetExceeded
from llm.hierarchical_budget import (
    BudgetThreshold,
    HierarchicalBudgetController,
    HierarchicalBudgetPolicy,
    derive_opaque_budget_operation_key,
)
from llm.persistent_budget import PersistentBudgetLedger

KEY_MATERIAL = b"frug8b-postgres-key-material-32bytes-plus"
MONTH = "2026-08"


def _policy() -> HierarchicalBudgetPolicy:
    return HierarchicalBudgetPolicy(
        global_budget=BudgetThreshold(100, 80),
        provider_budgets={
            "groq": BudgetThreshold(100, 80),
            "qwen": BudgetThreshold(100, 80),
        },
        workload_budgets={
            ("groq", "conversation"): BudgetThreshold(100, 80),
            ("qwen", "conversation"): BudgetThreshold(100, 80),
        },
        max_single_reservation_microusd=60,
    )


def _key(reference: str) -> str:
    return derive_opaque_budget_operation_key(
        key_material=KEY_MATERIAL,
        operation_reference=reference,
    )


@pytest.mark.django_db(transaction=True)
def test_persistent_bundle_retry_does_not_duplicate_any_dimension():
    ledger = PersistentBudgetLedger()
    controller = HierarchicalBudgetController(policy=_policy(), ledger=ledger)
    key = _key("request-1")

    first = controller.authorize(
        provider="groq",
        workload="conversation",
        month_key=MONTH,
        reserved_microusd=40,
        idempotency_key=key,
    )
    duplicate = controller.authorize(
        provider="groq",
        workload="conversation",
        month_key=MONTH,
        reserved_microusd=40,
        idempotency_key=key,
    )

    assert tuple(item.reservation_id for item in duplicate.reservations) == tuple(
        item.reservation_id for item in first.reservations
    )
    assert ledger.committed_microusd("finops:global", MONTH) == 40
    assert ledger.committed_microusd("finops:provider:groq", MONTH) == 40
    assert ledger.committed_microusd("finops:workload:groq:conversation", MONTH) == 40

    controller.settle(first, 25)
    assert ledger.committed_microusd("finops:global", MONTH) == 25
    assert ledger.committed_microusd("finops:provider:groq", MONTH) == 25
    assert ledger.committed_microusd("finops:workload:groq:conversation", MONTH) == 25


@pytest.mark.django_db(transaction=True)
def test_concurrent_cross_provider_bundles_cannot_cross_global_hard_budget():
    if connection.vendor != "postgresql":
        pytest.skip("row-lock global concurrency proof requires PostgreSQL")

    barrier = Barrier(2)

    def authorize(provider: str) -> str:
        close_old_connections()
        try:
            controller = HierarchicalBudgetController(
                policy=_policy(),
                ledger=PersistentBudgetLedger(),
            )
            barrier.wait()
            controller.authorize(
                provider=provider,
                workload="conversation",
                month_key=MONTH,
                reserved_microusd=60,
                idempotency_key=_key(f"{provider}-request"),
            )
            return f"{provider}:authorized"
        except BudgetExceeded:
            return f"{provider}:blocked"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(authorize, ("groq", "qwen")))

    assert sum(item.endswith(":authorized") for item in outcomes) == 1
    assert sum(item.endswith(":blocked") for item in outcomes) == 1

    ledger = PersistentBudgetLedger()
    assert ledger.committed_microusd("finops:global", MONTH) == 60
    provider_total = sum(
        ledger.committed_microusd(f"finops:provider:{provider}", MONTH)
        for provider in ("groq", "qwen")
    )
    workload_total = sum(
        ledger.committed_microusd(
            f"finops:workload:{provider}:conversation",
            MONTH,
        )
        for provider in ("groq", "qwen")
    )
    assert provider_total == 60
    assert workload_total == 60
