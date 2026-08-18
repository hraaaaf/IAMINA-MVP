from datetime import date, timedelta

import pytest

from llm.budget import BudgetController, BudgetExceeded, BudgetPolicy, InMemoryBudgetLedger
from llm.cost_authorization import authorize_metered_call
from llm.pricing import MeteredPrice, PricingRegistry, PricingUnavailable


def _price(*, due_offset_days: int = 30) -> MeteredPrice:
    today = date(2026, 8, 18)
    return MeteredPrice(
        provider="provider-a",
        model="audio-model-a",
        modality="stt",
        unit="second",
        currency="USD",
        price_microusd=6_000,
        units_per_price=60,
        evidence_reference="controlled-metered-fixture",
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


def test_metered_price_uses_exact_rational_billing_ratio():
    price = _price()

    assert price.worst_case_microusd(quantity=10) == 1_000
    assert price.worst_case_microusd(quantity=61) == 6_100


def test_metered_registry_requires_exact_current_modality_and_unit():
    registry = PricingRegistry((_price(),))

    resolved = registry.resolve_metered(
        provider="provider-a",
        model="audio-model-a",
        modality="stt",
        unit="second",
        today=date(2026, 8, 18),
    )
    assert resolved == _price()

    with pytest.raises(PricingUnavailable):
        registry.resolve_metered(
            provider="provider-a",
            model="audio-model-a",
            modality="vision",
            unit="image",
            today=date(2026, 8, 18),
        )

    with pytest.raises(PricingUnavailable, match="stale"):
        PricingRegistry((_price(due_offset_days=-1),)).resolve_metered(
            provider="provider-a",
            model="audio-model-a",
            modality="stt",
            unit="second",
            today=date(2026, 8, 18),
        )


def test_metered_authorization_reserves_before_paid_operation():
    controller = _controller()

    reservation = authorize_metered_call(
        controller=controller,
        pricing=PricingRegistry((_price(),)),
        provider="provider-a",
        model="audio-model-a",
        modality="stt",
        unit="second",
        quantity=10,
        subject_key="patient-budget-key",
        month_key="2026-08",
        today=date(2026, 8, 18),
    )

    assert reservation.reserved_microusd == 1_000
    assert controller.ledger.committed_microusd("patient-budget-key", "2026-08") == 1_000


def test_metered_authorization_obeys_single_and_monthly_caps():
    with pytest.raises(BudgetExceeded):
        authorize_metered_call(
            controller=_controller(single=999),
            pricing=PricingRegistry((_price(),)),
            provider="provider-a",
            model="audio-model-a",
            modality="stt",
            unit="second",
            quantity=10,
            subject_key="patient-budget-key",
            month_key="2026-08",
            today=date(2026, 8, 18),
        )

    controller = _controller(monthly=1_500, single=1_000)
    kwargs = {
        "controller": controller,
        "pricing": PricingRegistry((_price(),)),
        "provider": "provider-a",
        "model": "audio-model-a",
        "modality": "stt",
        "unit": "second",
        "quantity": 10,
        "subject_key": "patient-budget-key",
        "month_key": "2026-08",
        "today": date(2026, 8, 18),
    }
    authorize_metered_call(**kwargs)
    with pytest.raises(BudgetExceeded):
        authorize_metered_call(**kwargs)
