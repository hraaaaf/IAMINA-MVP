from evaluation.decision import decide_provider
from evaluation.scoring import BenchmarkScore, DimensionScores


def _score(provider, modality, total, *, disqualifications=()):
    return BenchmarkScore(
        provider=provider,
        modality=modality,
        dimensions=DimensionScores(
            quality=total,
            safety=max(total, 80),
            latency=total,
            cost=total,
            privacy=max(total, 80),
            availability=total,
        ),
        disqualifications=disqualifications,
    )


def test_decision_is_modality_specific_and_ranked():
    decision = decide_provider(
        "text",
        (
            _score("provider-a", "text", 88),
            _score("provider-b", "text", 92),
            _score("provider-c", "vision", 99),
        ),
    )
    assert decision.selected_provider == "provider-b"
    assert decision.ranked_providers == ("provider-b", "provider-a")


def test_disqualified_provider_cannot_win_on_quality():
    decision = decide_provider(
        "vision",
        (
            _score(
                "provider-unsafe",
                "vision",
                100,
                disqualifications=("no_retention_not_confirmed",),
            ),
            _score("provider-safe", "vision", 85),
        ),
    )
    assert decision.selected_provider == "provider-safe"
    assert decision.rejected == {
        "provider-unsafe": ("no_retention_not_confirmed",)
    }


def test_no_eligible_provider_fails_closed():
    decision = decide_provider(
        "stt",
        (_score("provider-a", "stt", 100, disqualifications=("evidence_stale",)),),
    )
    assert decision.selected_provider is None
