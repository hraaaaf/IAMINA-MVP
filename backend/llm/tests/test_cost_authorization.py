from datetime import date, timedelta

import pytest

from llm.budget import BudgetController, BudgetExceeded, BudgetPolicy, InMemoryBudgetLedger
from llm.cost_authorization import authorize_text_call
from llm.pricing import PricingRegistry, PricingUnavailable, TextTokenPrice


def _price(*, due_offset_days: int = 30) -> TextTokenPrice:
    today = date(2026, 8, 18)
    return TextTokenPrice(
        provider="provider-a",
        model="model-a",
        currency="USD",
        input_microusd_per_million=1_000_000,
        cached_input_microusd_per_million=250_000,
        output_microusd_per_million=2_000_000,
        evidence_reference="controlled-pricing-fixture",
        verified_on=today,
        review_due_on=today + timedelta(days=due_offset_days),
    )


def _controller(*, monthly: int = 10_000, single: int = 5_000) -> BudgetController:
    return BudgetController(
        BudgetPolicy(
            monthly_limit_microusd=monthly,
            max_single_reservation_microusd=single,
        ),
        InMemoryBudgetLedger(),
    )


def test_authorization_reserves_uncached_worst_case_cost():
    controller = _controller()
    reservation = authorize_text_call(
        controller=controller,
        pricing=PricingRegistry((_price(),)),
        provider="provider-a",
        model="model-a",
        subject_key="patient-budget-key",
        month_key="2026-08",
        max_input_tokens=1_000,
        max_output_tokens=500,
        today=date(2026, 8, 18),
    )

    assert reservation.reserved_microusd == 2_000
    assert controller.ledger.committed_microusd("patient-budget-key", "2026-08") == 2_000


def test_authorization_rejects_missing_or_stale_pricing_before_budget_mutation():
    controller = _controller()

    with pytest.raises(PricingUnavailable):
        authorize_text_call(
            controller=controller,
            pricing=PricingRegistry(()),
            provider="provider-a",
            model="model-a",
            subject_key="patient-budget-key",
            month_key="2026-08",
            max_input_tokens=1_000,
            max_output_tokens=500,
            today=date(2026, 8, 18),
        )

    with pytest.raises(PricingUnavailable, match="stale"):
        authorize_text_call(
            controller=controller,
            pricing=PricingRegistry((_price(due_offset_days=-1),)),
            provider="provider-a",
            model="model-a",
            subject_key="patient-budget-key",
            month_key="2026-08",
            max_input_tokens=1_000,
            max_output_tokens=500,
            today=date(2026, 8, 18),
        )

    assert controller.ledger.committed_microusd("patient-budget-key", "2026-08") == 0


def test_authorization_respects_single_call_and_monthly_ceiling():
    with pytest.raises(BudgetExceeded):
        authorize_text_call(
            controller=_controller(single=1_999),
            pricing=PricingRegistry((_price(),)),
            provider="provider-a",
            model="model-a",
            subject_key="patient-budget-key",
            month_key="2026-08",
            max_input_tokens=1_000,
            max_output_tokens=500,
            today=date(2026, 8, 18),
        )

    controller = _controller(monthly=3_000, single=2_000)
    pricing = PricingRegistry((_price(),))
    authorize_text_call(
        controller=controller,
        pricing=pricing,
        provider="provider-a",
        model="model-a",
        subject_key="patient-budget-key",
        month_key="2026-08",
        max_input_tokens=1_000,
        max_output_tokens=500,
        today=date(2026, 8, 18),
    )
    with pytest.raises(BudgetExceeded):
        authorize_text_call(
            controller=controller,
            pricing=pricing,
            provider="provider-a",
            model="model-a",
            subject_key="patient-budget-key",
            month_key="2026-08",
            max_input_tokens=1_000,
            max_output_tokens=500,
            today=date(2026, 8, 18),
        )
