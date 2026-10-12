"""CAL-09/10: characterize clinical-day ambiguity without choosing a policy.

This is an intentionally descriptive regression: the producer currently groups
paired-meal observations by pre_at.date().  A patient's timezone authority must
be specified and independently approved before this can change.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from diabetes.services.clinical.paired_meal_response import (
    PairedMealEpisode,
    _patterns,
)


def _episodes(offset: timezone) -> tuple[PairedMealEpisode, ...]:
    # Same five *instants*, spanning only two UTC days but three calendar
    # dates in UTC+01. No patient data and no proposed clinical threshold.
    moments_utc = (
        datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 10, 23, 40, tzinfo=timezone.utc),
        datetime(2026, 10, 11, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 11, 23, 40, tzinfo=timezone.utc),
        datetime(2026, 10, 11, 23, 45, tzinfo=timezone.utc),
    )
    return tuple(
        PairedMealEpisode(
            episode_id=UUID(int=index + 1),
            meal_type="lunch",
            pre_at=moment.astimezone(offset),
            post_at=(moment + timedelta(minutes=10)).astimezone(offset),
            pre_glucose_mg_dl=120.0,
            post_glucose_mg_dl=135.0,
            delta_mg_dl=15.0,
            elapsed_minutes=10.0,
        )
        for index, moment in enumerate(moments_utc)
    )


def test_clinical_day_density_depends_on_timezone_policy_not_glucose():
    """A timezone-free policy cannot legitimately certify day sufficiency."""
    utc_pairs = _episodes(timezone.utc)
    plus_one_pairs = _episodes(timezone(timedelta(hours=1)))

    assert [p.pre_at.timestamp() for p in utc_pairs] == [
        p.pre_at.timestamp() for p in plus_one_pairs
    ]
    assert len({p.pre_at.date() for p in utc_pairs}) == 2
    assert len({p.pre_at.date() for p in plus_one_pairs}) == 3

    # Characterization of the *existing* implementation, not an endorsement.
    assert _patterns(utc_pairs) == ()
    local_patterns = _patterns(plus_one_pairs)
    assert len(local_patterns) == 1
    assert local_patterns[0].pairs == 5
    assert local_patterns[0].distinct_days == 3
    assert local_patterns[0].median_delta_mg_dl == 15.0


def test_elapsed_minutes_are_timezone_independent_for_same_instant_pair():
    """The observed ten-minute delta must not become a new meal cutoff."""
    utc = _episodes(timezone.utc)
    plus_one = _episodes(timezone(timedelta(hours=1)))
    assert [p.elapsed_minutes for p in utc] == [
        p.elapsed_minutes for p in plus_one
    ] == [10.0] * 5
    assert [p.delta_mg_dl for p in utc] == [
        p.delta_mg_dl for p in plus_one
    ] == [15.0] * 5
