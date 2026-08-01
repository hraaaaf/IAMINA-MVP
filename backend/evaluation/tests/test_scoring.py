import pytest

from evaluation.scoring import BenchmarkScore, DimensionScores


def test_weighted_score_is_deterministic():
    score = BenchmarkScore(
        provider="synthetic-provider",
        modality="text",
        dimensions=DimensionScores(
            quality=90,
            safety=100,
            latency=80,
            cost=70,
            privacy=100,
            availability=90,
        ),
    )
    assert score.weighted_total == 93.5
    assert score.eligible is True


def test_disqualification_forces_zero_and_ineligible():
    score = BenchmarkScore(
        provider="synthetic-provider",
        modality="vision",
        dimensions=DimensionScores(100, 100, 100, 100, 100, 100),
        disqualifications=("training_on_patient_data",),
    )
    assert score.weighted_total == 0
    assert score.eligible is False


def test_safety_and_privacy_are_hard_floors():
    score = BenchmarkScore(
        provider="synthetic-provider",
        modality="stt",
        dimensions=DimensionScores(100, 79, 100, 100, 100, 100),
    )
    assert score.eligible is False


def test_invalid_dimension_fails_closed():
    score = BenchmarkScore(
        provider="synthetic-provider",
        modality="text",
        dimensions=DimensionScores(101, 100, 100, 100, 100, 100),
    )
    with pytest.raises(ValueError):
        _ = score.weighted_total
