import pytest

from llm.budget import (
    BudgetAccountingError,
    BudgetController,
    BudgetExceeded,
    BudgetPolicy,
    InMemoryBudgetLedger,
)


def _controller() -> BudgetController:
    return BudgetController(
        BudgetPolicy(
            monthly_limit_microusd=100,
            max_single_reservation_microusd=60,
        ),
        InMemoryBudgetLedger(),
    )


def test_budget_reservation_blocks_before_monthly_limit_is_crossed():
    controller = _controller()
    first = controller.authorize(
        subject_key="opaque-subject",
        month_key="2026-08",
        reserved_microusd=40,
    )
    second = controller.authorize(
        subject_key="opaque-subject",
        month_key="2026-08",
        reserved_microusd=40,
    )

    with pytest.raises(BudgetExceeded):
        controller.authorize(
            subject_key="opaque-subject",
            month_key="2026-08",
            reserved_microusd=30,
        )

    controller.settle(first, 30)
    controller.settle(second, 35)
    assert controller.ledger.committed_microusd("opaque-subject", "2026-08") == 65


def test_settlement_refund_releases_unused_reservation_capacity():
    controller = _controller()
    reservation = controller.authorize(
        subject_key="opaque-subject",
        month_key="2026-08",
        reserved_microusd=60,
    )
    controller.settle(reservation, 20)

    follow_up = controller.authorize(
        subject_key="opaque-subject",
        month_key="2026-08",
        reserved_microusd=60,
    )
    assert follow_up.reserved_microusd == 60
    assert controller.ledger.committed_microusd("opaque-subject", "2026-08") == 80


def test_actual_cost_above_reservation_fails_closed():
    controller = _controller()
    reservation = controller.authorize(
        subject_key="opaque-subject",
        month_key="2026-08",
        reserved_microusd=40,
    )

    with pytest.raises(BudgetAccountingError):
        controller.settle(reservation, 41)

    assert controller.ledger.committed_microusd("opaque-subject", "2026-08") == 40


def test_cancelled_reservation_releases_capacity():
    controller = _controller()
    reservation = controller.authorize(
        subject_key="opaque-subject",
        month_key="2026-08",
        reserved_microusd=60,
    )
    controller.cancel(reservation)

    next_reservation = controller.authorize(
        subject_key="opaque-subject",
        month_key="2026-08",
        reserved_microusd=60,
    )
    assert next_reservation.reserved_microusd == 60


def test_single_call_ceiling_is_enforced():
    controller = _controller()
    with pytest.raises(BudgetExceeded):
        controller.authorize(
            subject_key="opaque-subject",
            month_key="2026-08",
            reserved_microusd=61,
        )
