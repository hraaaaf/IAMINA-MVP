from datetime import date, timedelta

import pytest

from llm.base import BaseLLMProvider, LLMResponse
from llm.budget import BudgetController, BudgetExceeded, BudgetPolicy, InMemoryBudgetLedger
from llm.cost_authorization import authorize_metered_call, authorize_text_call
from llm.pipeline import LLMPipeline, LLMPipelineModeBlocked
from llm.pricing import MeteredPrice, PricingRegistry, PricingUnavailable, TextTokenPrice

TODAY = date(2026, 8, 19)


class CountingProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.complete_calls = 0
        self.stream_calls = 0
        self.think_calls = 0

    @property
    def model_name(self) -> str:
        return "synthetic-counting-provider"

    def complete(self, system: str, user: str) -> LLMResponse:
        self.complete_calls += 1
        return LLMResponse(text="ok", model=self.model_name)

    def stream(self, system: str, user: str):
        self.stream_calls += 1
        yield "blocked"

    def think(self, system: str, user: str) -> tuple[str, str]:
        self.think_calls += 1
        return ("blocked", "blocked")


def _controller(monthly: int = 10_000) -> BudgetController:
    return BudgetController(
        BudgetPolicy(
            monthly_limit_microusd=monthly,
            max_single_reservation_microusd=monthly,
        ),
        InMemoryBudgetLedger(),
    )


def test_stale_price_blocks_before_synthetic_provider_invocation():
    provider = CountingProvider()
    pricing = PricingRegistry(
        (
            TextTokenPrice(
                provider="synthetic",
                model="cheap-text",
                currency="USD",
                input_microusd_per_million=100_000,
                cached_input_microusd_per_million=None,
                output_microusd_per_million=400_000,
                evidence_reference="expired-test-price",
                verified_on=TODAY - timedelta(days=10),
                review_due_on=TODAY - timedelta(days=1),
            ),
        )
    )

    with pytest.raises(PricingUnavailable, match="stale"):
        authorize_text_call(
            controller=_controller(),
            pricing=pricing,
            provider="synthetic",
            model="cheap-text",
            subject_key="synthetic-user",
            month_key="2026-08",
            max_input_tokens=800,
            max_output_tokens=160,
            today=TODAY,
        )

    assert provider.complete_calls == 0


def test_mixed_modality_budget_blocks_before_second_paid_operation():
    provider = CountingProvider()
    due = TODAY + timedelta(days=30)
    pricing = PricingRegistry(
        (
            TextTokenPrice(
                provider="synthetic",
                model="cheap-text",
                currency="USD",
                input_microusd_per_million=1_000_000,
                cached_input_microusd_per_million=None,
                output_microusd_per_million=1_000_000,
                evidence_reference="controlled-text-price",
                verified_on=TODAY,
                review_due_on=due,
            ),
            MeteredPrice(
                provider="synthetic",
                model="vision",
                modality="vision",
                unit="image",
                currency="USD",
                price_microusd=8_000,
                units_per_price=1,
                evidence_reference="controlled-vision-price",
                verified_on=TODAY,
                review_due_on=due,
            ),
        )
    )
    controller = _controller(monthly=10_000)

    text_reservation = authorize_text_call(
        controller=controller,
        pricing=pricing,
        provider="synthetic",
        model="cheap-text",
        subject_key="synthetic-user",
        month_key="2026-08",
        max_input_tokens=1_000,
        max_output_tokens=1_000,
        today=TODAY,
    )
    provider.complete("system", "user")
    controller.settle(text_reservation, actual_microusd=2_000)

    with pytest.raises(BudgetExceeded, match="monthly budget"):
        authorize_metered_call(
            controller=controller,
            pricing=pricing,
            provider="synthetic",
            model="vision",
            modality="vision",
            unit="image",
            quantity=2,
            subject_key="synthetic-user",
            month_key="2026-08",
            today=TODAY,
        )

    assert provider.complete_calls == 1
    assert controller.ledger.committed_microusd("synthetic-user", "2026-08") == 2_000


def test_pipeline_bypass_modes_remain_blocked_in_rollout_smoke():
    provider = CountingProvider()
    pipeline = LLMPipeline(provider)

    with pytest.raises(LLMPipelineModeBlocked):
        list(pipeline.stream("system", "user"))
    with pytest.raises(LLMPipelineModeBlocked):
        pipeline.think("system", "user")

    assert provider.stream_calls == 0
    assert provider.think_calls == 0
