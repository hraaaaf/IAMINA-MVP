"""Fail-closed bridge from verified pricing to AI budget reservation.

This module performs no provider/network call. It only authorizes worst-case
spend reservations after resolving exact current controlled price records.
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


def authorize_metered_call(
    *,
    controller: BudgetController,
    pricing: PricingRegistry,
    provider: str,
    model: str,
    modality: str,
    unit: str,
    quantity: int,
    subject_key: str,
    month_key: str,
    today: date,
) -> BudgetReservation:
    """Reserve worst-case media/metered spend before any paid provider call."""
    price = pricing.resolve_metered(
        provider=provider,
        model=model,
        modality=modality,
        unit=unit,
        today=today,
    )
    reserved_microusd = price.worst_case_microusd(quantity=quantity)
    if reserved_microusd <= 0:
        raise ValueError("paid metered authorization requires a positive reservation")
    return controller.authorize(
        subject_key=subject_key,
        month_key=month_key,
        reserved_microusd=reserved_microusd,
    )
