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


@dataclass(frozen=True, slots=True)
class MeteredPrice:
    """Generic non-text price represented as an exact rational billing unit.

    Examples, supplied only by controlled configuration:
    - audio: price_microusd for units_per_price seconds;
    - OCR: price_microusd for units_per_price pages;
    - vision: price_microusd for units_per_price images;
    - TTS: price_microusd for units_per_price characters.

    Keeping the ratio avoids lossy conversion of provider prices such as
    ``$X / 1000 pages`` or ``$Y / minute`` into source-code floats.
    """

    provider: str
    model: str
    modality: str
    unit: str
    currency: str
    price_microusd: int
    units_per_price: int
    evidence_reference: str
    verified_on: date
    review_due_on: date

    def validate(self, *, today: date) -> None:
        required = {
            "provider": self.provider,
            "model": self.model,
            "modality": self.modality,
            "unit": self.unit,
            "currency": self.currency,
            "evidence_reference": self.evidence_reference,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError("missing metered pricing fields: " + ", ".join(missing))
        if self.currency != "USD":
            raise ValueError("metered pricing registry currently requires USD")
        if self.price_microusd < 0:
            raise ValueError("metered price cannot be negative")
        if self.units_per_price <= 0:
            raise ValueError("units_per_price must be positive")
        if self.verified_on > today:
            raise ValueError("pricing verification date is in the future")
        if self.review_due_on < today:
            raise PricingUnavailable("pricing evidence is stale")

    def worst_case_microusd(self, *, quantity: int) -> int:
        if quantity < 0:
            raise ValueError("metered quantity cannot be negative")
        if quantity == 0 or self.price_microusd == 0:
            return 0
        return (
            quantity * self.price_microusd + self.units_per_price - 1
        ) // self.units_per_price


PriceRecord = TextTokenPrice | MeteredPrice


class PricingRegistry:
    def __init__(self, prices: tuple[PriceRecord, ...]) -> None:
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
            if isinstance(price, TextTokenPrice)
            and price.provider == provider
            and price.model == model
        )
        if len(matches) != 1:
            raise PricingUnavailable(
                "exactly one controlled text price record is required for provider/model"
            )
        price = matches[0]
        price.validate(today=today)
        return price

    def resolve_metered(
        self,
        *,
        provider: str,
        model: str,
        modality: str,
        unit: str,
        today: date,
    ) -> MeteredPrice:
        matches = tuple(
            price
            for price in self._prices
            if isinstance(price, MeteredPrice)
            and price.provider == provider
            and price.model == model
            and price.modality == modality
            and price.unit == unit
        )
        if len(matches) != 1:
            raise PricingUnavailable(
                "exactly one controlled metered price record is required for provider/model/modality/unit"
            )
        price = matches[0]
        price.validate(today=today)
        return price
