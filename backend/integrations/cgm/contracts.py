from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class CGMSource(StrEnum):
    DEXCOM = "dexcom"
    LIBRE = "libre"
    LINX = "linx"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CGMReading:
    timestamp: datetime
    glucose_mg_dl: int
    source: CGMSource
    trend: str | None = None
    device: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderHealth:
    ok: bool
    checked_at: datetime
    detail: str | None = None


class CGMProvider(Protocol):
    """Read-only CGM provider boundary.

    Provider implementations must fail closed on malformed or incomplete
    readings and must never infer clinical meaning from transport data.
    """

    def readings(self, since: datetime) -> list[CGMReading]: ...

    def health(self) -> ProviderHealth: ...
