"""Aggregate benchmark readiness without exposing credentials or inventing scores."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


class ValidatableManifest(Protocol):
    provider: str
    model: str

    def validate(self, *, today: date) -> None: ...


@dataclass(frozen=True, slots=True)
class ReadinessItem:
    provider: str
    model: str
    ready: bool
    reason: str | None


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    modality: str
    items: tuple[ReadinessItem, ...]

    @property
    def all_ready(self) -> bool:
        return bool(self.items) and all(item.ready for item in self.items)


def build_readiness_report(
    modality: str,
    manifests: tuple[ValidatableManifest, ...],
    *,
    today: date,
) -> ReadinessReport:
    items: list[ReadinessItem] = []
    for manifest in manifests:
        try:
            manifest.validate(today=today)
        except ValueError as exc:
            items.append(
                ReadinessItem(
                    provider=manifest.provider,
                    model=manifest.model,
                    ready=False,
                    reason=str(exc),
                )
            )
        else:
            items.append(
                ReadinessItem(
                    provider=manifest.provider,
                    model=manifest.model,
                    ready=True,
                    reason=None,
                )
            )
    return ReadinessReport(modality=modality, items=tuple(items))
