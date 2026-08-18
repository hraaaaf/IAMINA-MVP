"""Controlled, expiring AI price registry contract.

No provider price is embedded here. Runtime or benchmark wiring must load
verified price records from controlled configuration and reject stale or
incomplete records before estimating/reserving spend.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


class PricingUnavailable(RuntimeError):
    """Raised when a current controlled price cannot be resolved."""


@dataclass(frozen=True, slots=True)
class TextTokenPrice:
    provider: str
    model: str
    currency: str
    input_microusd_per_million: int
    cached_input_microusd_per_million: int | None
    output_microusd_per_million: int
    evidence_reference: str
    verified_on: date
    review_due_on: date

    def validate(self, *, today: date) -> None:
        required = {
            "provider": self.provider,
            "model": self.model,
            "currency": self.currency,
            "evidence_reference": self.evidence_reference,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError("missing pricing fields: " + ", ".join(missing))
        if self.currency != "USD":
            raise ValueError("text pricing registry currently requires USD")
        if self.input_microusd_per_million < 0 or self.output_microusd_per_million < 0:
            raise ValueError("token prices cannot be negative")
        if (
            self.cached_input_microusd_per_million is not None
            and self.cached_input_microusd_per_million < 0
        ):
            raise ValueError("cached token price cannot be negative")
        if self.verified_on > today:
            raise ValueError("pricing verification date is in the future")
        if self.review_due_on < today:
            raise PricingUnavailable("pricing evidence is stale")

    def worst_case_microusd(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
    ) -> int:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts cannot be negative")
        input_cost = (
            input_tokens * self.input_microusd_per_million + 999_999
        ) // 1_000_000
        output_cost = (
            output_tokens * self.output_microusd_per_million + 999_999
        ) // 1_000_000
        return input_cost + output_cost


class PricingRegistry:
    def __init__(self, prices: tuple[TextTokenPrice, ...]) -> None:
        self._prices = prices

    def resolve_text(
        self,
        *,
        provider: str,
        model: str,
        today: date,
    ) -> TextTokenPrice:
        matches = tuple(
            price
            for price in self._prices
            if price.provider == provider and price.model == model
        )
        if len(matches) != 1:
            raise PricingUnavailable(
                "exactly one controlled price record is required for provider/model"
            )
        price = matches[0]
        price.validate(today=today)
        return price
