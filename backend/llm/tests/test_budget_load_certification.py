from datetime import date, timedelta

import pytest

from llm.budget import BudgetController, BudgetExceeded, BudgetPolicy, InMemoryBudgetLedger
from llm.cost_authorization import authorize_metered_call, authorize_text_call
from llm.pricing import MeteredPrice, PricingRegistry, TextTokenPrice

TODAY = date(2026, 8, 18)
SUBJECT = "synthetic-budget-subject"
MONTH = "2026-08"


def _registry() -> PricingRegistry:
    due = TODAY + timedelta(days=30)
    return PricingRegistry(
        (
            TextTokenPrice(
                provider="text-provider",
                model="cheap-text",
                currency="USD",
                input_microusd_per_million=100_000,
                cached_input_microusd_per_million=None,
                output_microusd_per_million=400_000,
                evidence_reference="synthetic-controlled-text-price",
                verified_on=TODAY,
                review_due_on=due,
            ),
            MeteredPrice(
                provider="stt-provider",
                model="cheap-stt",
                modality="stt",
                unit="second",
                currency="USD",
                price_microusd=3_000,
                units_per_price=60,
                evidence_reference="synthetic-controlled-stt-price",
                verified_on=TODAY,
                review_due_on=due,
            ),
            MeteredPrice(
                provider="vision-provider",
                model="cheap-vision",
                modality="vision",
                unit="image",
                currency="USD",
                price_microusd=2_000,
                units_per_price=1,
                evidence_reference="synthetic-controlled-vision-price",
                verified_on=TODAY,
                review_due_on=due,
            ),
        )
    )


def _controller(*, monthly: int = 250_000, single: int = 50_000) -> BudgetController:
    return BudgetController(
        BudgetPolicy(
            monthly_limit_microusd=monthly,
            max_single_reservation_microusd=single,
        ),
        InMemoryBudgetLedger(),
    )


def test_mixed_load_cannot_cross_monthly_budget_silently():
    controller = _controller(monthly=20_000, single=10_000)
    pricing = _registry()

    # 10 text calls: 800 input + 160 output => 144 micro-USD each.
    for _ in range(10):
        authorize_text_call(
            controller=controller,
            pricing=pricing,
            provider="text-provider",
            model="cheap-text",
            subject_key=SUBJECT,
            month_key=MONTH,
            max_input_tokens=800,
            max_output_tokens=160,
            today=TODAY,
        )

    # 120 seconds STT = 6,000 micro-USD.
    authorize_metered_call(
        controller=controller,
        pricing=pricing,
        provider="stt-provider",
        model="cheap-stt",
        modality="stt",
        unit="second",
        quantity=120,
        subject_key=SUBJECT,
        month_key=MONTH,
        today=TODAY,
    )

    # Five images = 10,000 micro-USD. Total committed = 17,440.
    for _ in range(5):
        authorize_metered_call(
            controller=controller,
            pricing=pricing,
            provider="vision-provider",
            model="cheap-vision",
            modality="vision",
            unit="image",
            quantity=1,
            subject_key=SUBJECT,
            month_key=MONTH,
            today=TODAY,
        )

    assert controller.ledger.committed_microusd(SUBJECT, MONTH) == 17_440

    before = controller.ledger.committed_microusd(SUBJECT, MONTH)
    with pytest.raises(BudgetExceeded, match="monthly budget"):
        authorize_metered_call(
            controller=controller,
            pricing=pricing,
            provider="vision-provider",
            model="cheap-vision",
            modality="vision",
            unit="image",
            quantity=2,
            subject_key=SUBJECT,
            month_key=MONTH,
            today=TODAY,
        )
    assert controller.ledger.committed_microusd(SUBJECT, MONTH) == before


def test_settlement_releases_unused_reservation_capacity():
    controller = _controller(monthly=10_000, single=10_000)
    pricing = _registry()
    reservation = authorize_metered_call(
        controller=controller,
        pricing=pricing,
        provider="stt-provider",
        model="cheap-stt",
        modality="stt",
        unit="second",
        quantity=120,
        subject_key=SUBJECT,
        month_key=MONTH,
        today=TODAY,
    )
    assert reservation.reserved_microusd == 6_000

    controller.settle(reservation, actual_microusd=3_000)
    assert controller.ledger.committed_microusd(SUBJECT, MONTH) == 3_000

    second = authorize_metered_call(
        controller=controller,
        pricing=pricing,
        provider="stt-provider",
        model="cheap-stt",
        modality="stt",
        unit="second",
        quantity=120,
        subject_key=SUBJECT,
        month_key=MONTH,
        today=TODAY,
    )
    assert second.reserved_microusd == 6_000
    assert controller.ledger.committed_microusd(SUBJECT, MONTH) == 9_000


def test_budget_isolated_by_subject_and_month():
    controller = _controller(monthly=2_000, single=2_000)
    pricing = _registry()

    for subject, month in (("a", MONTH), ("b", MONTH), ("a", "2026-09")):
        authorize_metered_call(
            controller=controller,
            pricing=pricing,
            provider="vision-provider",
            model="cheap-vision",
            modality="vision",
            unit="image",
            quantity=1,
            subject_key=subject,
            month_key=month,
            today=TODAY,
        )

    assert controller.ledger.committed_microusd("a", MONTH) == 2_000
    assert controller.ledger.committed_microusd("b", MONTH) == 2_000
    assert controller.ledger.committed_microusd("a", "2026-09") == 2_000
