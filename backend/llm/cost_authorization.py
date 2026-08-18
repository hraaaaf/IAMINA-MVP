"""Fail-closed bridge from verified text pricing to AI budget reservation.

This module still performs no provider/network call. It only authorizes a
worst-case spend reservation after resolving one exact current price record.
"""

from __future__ import annotations

from datetime import date

from .budget import BudgetController, BudgetReservation
from .pricing import PricingRegistry


def authorize_text_call(
    *,
    controller: BudgetController,
    pricing: PricingRegistry,
    provider: str,
    model: str,
    subject_key: str,
    month_key: str,
    max_input_tokens: int,
    max_output_tokens: int,
    today: date,
) -> BudgetReservation:
    """Reserve worst-case uncached text spend before any paid provider call."""

    price = pricing.resolve_text(provider=provider, model=model, today=today)
    reserved_microusd = price.worst_case_microusd(
        input_tokens=max_input_tokens,
        output_tokens=max_output_tokens,
    )
    if reserved_microusd <= 0:
        raise ValueError("paid text authorization requires a positive reservation")
    return controller.authorize(
        subject_key=subject_key,
        month_key=month_key,
        reserved_microusd=reserved_microusd,
    )
