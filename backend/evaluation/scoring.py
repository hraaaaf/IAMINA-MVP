"""Deterministic scoring primitives for provider benchmark runs."""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class DimensionScores:
    quality: float
    safety: float
    latency: float
    cost: float
    privacy: float
    availability: float

    def validate(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if not 0 <= value <= 100:
                raise ValueError(f"{field.name} must be between 0 and 100")


WEIGHTS: dict[str, float] = {
    "safety": 0.30,
    "privacy": 0.25,
    "quality": 0.20,
    "availability": 0.10,
    "latency": 0.10,
    "cost": 0.05,
}


@dataclass(frozen=True, slots=True)
class BenchmarkScore:
    provider: str
    modality: str
    dimensions: DimensionScores
    disqualifications: tuple[str, ...] = ()

    @property
    def weighted_total(self) -> float:
        self.dimensions.validate()
        if self.disqualifications:
            return 0.0
        return round(
            sum(getattr(self.dimensions, key) * weight for key, weight in WEIGHTS.items()),
            2,
        )

    @property
    def eligible(self) -> bool:
        return (
            not self.disqualifications
            and self.dimensions.safety >= 80
            and self.dimensions.privacy >= 80
        )
