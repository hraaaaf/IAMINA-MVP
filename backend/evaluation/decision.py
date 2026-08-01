"""Deterministic provider ranking and cutover gate."""

from __future__ import annotations

from dataclasses import dataclass

from evaluation.scoring import BenchmarkScore


@dataclass(frozen=True, slots=True)
class ProviderDecision:
    modality: str
    selected_provider: str | None
    ranked_providers: tuple[str, ...]
    rejected: dict[str, tuple[str, ...]]


def decide_provider(
    modality: str,
    scores: tuple[BenchmarkScore, ...],
) -> ProviderDecision:
    relevant = tuple(score for score in scores if score.modality == modality)
    rejected: dict[str, tuple[str, ...]] = {}
    eligible: list[BenchmarkScore] = []
    for score in relevant:
        if score.eligible:
            eligible.append(score)
        else:
            reasons = score.disqualifications or ("safety_or_privacy_floor_not_met",)
            rejected[score.provider] = reasons
    ranked = tuple(
        score.provider
        for score in sorted(eligible, key=lambda item: item.weighted_total, reverse=True)
    )
    return ProviderDecision(
        modality=modality,
        selected_provider=ranked[0] if ranked else None,
        ranked_providers=ranked,
        rejected=rejected,
    )
