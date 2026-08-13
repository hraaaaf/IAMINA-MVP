from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Receipt:
    actor: str
    at: datetime
    items: tuple[str, ...]
    status: str


def validate_receipt(value: Receipt) -> None:
    if not value.actor.strip():
        raise ValueError("actor")
    if value.at.tzinfo is None or value.at.utcoffset() is None:
        raise ValueError("at")
    if not value.items or any(not item.strip() for item in value.items):
        raise ValueError("items")
    if len(set(value.items)) != len(value.items):
        raise ValueError("items")
    if not value.status.strip():
        raise ValueError("status")
