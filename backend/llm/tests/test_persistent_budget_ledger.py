from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from llm.budget import BudgetAccountingError, BudgetExceeded
from llm.persistent_budget import PersistentBudgetLedger

SUBJECT = "opaque-frug8-subject"
MONTH = "2026-08"


@pytest.mark.django_db(transaction=True)
def test_persistent_ledger_survives_new_instances_and_deduplicates_reservation():
    first = PersistentBudgetLedger()
    reservation = first.reserve_if_within(
        subject_key=SUBJECT,
        month_key=MONTH,
        amount_microusd=40,
        monthly_limit_microusd=100,
        idempotency_key="request-1",
    )

    second = PersistentBudgetLedger()
    duplicate = second.reserve_if_within(
        subject_key=SUBJECT,
        month_key=MONTH,
        amount_microusd=40,
        monthly_limit_microusd=100,
        idempotency_key="request-1",
    )

    assert duplicate.reservation_id == reservation.reservation_id
    assert second.committed_microusd(SUBJECT, MONTH) == 40

    second.settle(reservation.reservation_id, 25)
    assert first.committed_microusd(SUBJECT, MONTH) == 25


@pytest.mark.django_db(transaction=True)
def test_idempotency_key_cannot_be_reused_for_a_different_amount():
    ledger = PersistentBudgetLedger()
    ledger.reserve_if_within(
        subject_key=SUBJECT,
        month_key=MONTH,
        amount_microusd=40,
        monthly_limit_microusd=100,
        idempotency_key="request-1",
    )

    with pytest.raises(BudgetAccountingError, match="different amount"):
        ledger.reserve_if_within(
            subject_key=SUBJECT,
            month_key=MONTH,
            amount_microusd=30,
            monthly_limit_microusd=100,
            idempotency_key="request-1",
        )

    assert ledger.committed_microusd(SUBJECT, MONTH) == 40


@pytest.mark.django_db(transaction=True)
def test_persistent_cancel_releases_reserved_capacity():
    ledger = PersistentBudgetLedger()
    reservation = ledger.reserve_if_within(
        subject_key=SUBJECT,
        month_key=MONTH,
        amount_microusd=60,
        monthly_limit_microusd=100,
        idempotency_key="cancel-me",
    )

    ledger.cancel(reservation.reservation_id)

    follow_up = ledger.reserve_if_within(
        subject_key=SUBJECT,
        month_key=MONTH,
        amount_microusd=100,
        monthly_limit_microusd=100,
        idempotency_key="after-cancel",
    )
    assert follow_up.reserved_microusd == 100
    assert ledger.committed_microusd(SUBJECT, MONTH) == 100


@pytest.mark.django_db(transaction=True)
def test_persistent_ledger_blocks_over_budget_without_partial_write():
    ledger = PersistentBudgetLedger()
    ledger.reserve_if_within(
        subject_key=SUBJECT,
        month_key=MONTH,
        amount_microusd=80,
        monthly_limit_microusd=100,
        idempotency_key="first",
    )

    with pytest.raises(BudgetExceeded):
        ledger.reserve_if_within(
            subject_key=SUBJECT,
            month_key=MONTH,
            amount_microusd=30,
            monthly_limit_microusd=100,
            idempotency_key="second",
        )

    assert ledger.committed_microusd(SUBJECT, MONTH) == 80


@pytest.mark.django_db(transaction=True)
def test_concurrent_postgresql_reservations_cannot_cross_hard_budget():
    if connection.vendor != "postgresql":
        pytest.skip("row-lock concurrency proof requires PostgreSQL")

    barrier = Barrier(2)

    def reserve_once(key: str) -> str:
        close_old_connections()
        try:
            ledger = PersistentBudgetLedger()
            barrier.wait()
            ledger.reserve_if_within(
                subject_key=SUBJECT,
                month_key=MONTH,
                amount_microusd=60,
                monthly_limit_microusd=100,
                idempotency_key=key,
            )
            return "authorized"
        except BudgetExceeded:
            return "blocked"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(reserve_once, ("worker-a", "worker-b")))

    assert outcomes == ["authorized", "blocked"]
    assert PersistentBudgetLedger().committed_microusd(SUBJECT, MONTH) == 60
