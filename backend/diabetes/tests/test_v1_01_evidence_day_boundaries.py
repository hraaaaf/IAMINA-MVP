"""CAL-09/10 — characterize UTC evidence-day boundaries before clinical policy.

These tests establish CURRENT technical behavior, not approval of UTC as the
patient's clinical day. No patient timezone authority exists in the current
BasePatientProfile or DiabetesProfile schemas (as audited 2026-10-09).
"""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.contracts.governed_longitudinal import GovernedLongitudinalContract
from diabetes.contracts.multi_source_fusion import (
    FusionPopulation,
    GovernedGlucoseFusionContract,
)
from diabetes.models import LogEntry
from diabetes.services.clinical.governed_longitudinal import (
    compute_governed_longitudinal_intelligence,
)
from diabetes.services.clinical.paired_meal_response import (
    compute_paired_meal_response,
)
from diabetes.services.clinical.personal_response import compute_personal_response
from diabetes.services.import_identity import make_import_client_uuid


class EvidenceDayBoundaryCharacterizationTests(TestCase):
    """A valid UTC day boundary can be one calendar day in UTC+01."""

    def setUp(self):
        self.patient = User.objects.create_user(username="v1-01-utc-day-boundary")
        self.foreign_patient = User.objects.create_user(
            username="v1-01-utc-day-boundary-foreign"
        )
        ten_days_ago = timezone.now().astimezone(dt.UTC).date() - dt.timedelta(days=10)
        midnight = dt.datetime.combine(ten_days_ago, dt.time.min, tzinfo=dt.UTC)
        self.before = midnight + dt.timedelta(hours=23, minutes=50)
        self.after = midnight + dt.timedelta(days=1, minutes=5)
        self.plus_one = dt.timezone(dt.timedelta(hours=1))
        self.assertNotEqual(self.before.date(), self.after.date())
        self.assertEqual(
            self.before.astimezone(self.plus_one).date(),
            self.after.astimezone(self.plus_one).date(),
        )

    def _reading(
        self,
        at: dt.datetime,
        *,
        glucose: int,
        source: str = "manual",
        patient=None,
        **kwargs,
    ) -> LogEntry:
        actual_patient = patient or self.patient
        extras = {}
        if source == "import":
            extras["client_uuid"] = make_import_client_uuid(
                actual_patient.id, at, glucose
            )
        return LogEntry.objects.create(
            patient=actual_patient,
            source=source,
            logged_at=at,
            blood_sugar=glucose,
            **extras,
            **kwargs,
        )

    def _meal_pair(self, pre_at: dt.datetime, *, base: int) -> None:
        episode = uuid4()
        self._reading(
            pre_at,
            glucose=base,
            meal_episode_id=episode,
            glycemic_context="pre_meal",
            meal_type="lunch",
        )
        self._reading(
            pre_at + dt.timedelta(minutes=3),
            glucose=base + 30,
            meal_episode_id=episode,
            glycemic_context="post_meal",
            meal_type="lunch",
        )

    def test_personal_response_counts_utc_days_not_utc_plus_one_days(self):
        times = (
            self.before,
            self.before + dt.timedelta(minutes=4),
            self.after,
        )
        for index, at in enumerate(times):
            self._reading(at, glucose=130 + index * 10, stressed="yes")
        # Three observations across two UTC dates, but one UTC+01 date.
        result = compute_personal_response(patient_id=self.patient.id)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.distinct_days, 2)
        pattern = next(x for x in result.patterns if x.key == "context:stress")
        self.assertEqual(pattern.distinct_days, 2)
        self.assertEqual(pattern.confidence, "limited")
        self.assertEqual(len({t.astimezone(self.plus_one).date() for t in times}), 1)

    def test_paired_meal_density_uses_utc_day_of_explicit_pre_measurement(self):
        starts = (
            self.before,
            self.before + dt.timedelta(minutes=5),
            self.after,
        )
        for index, at in enumerate(starts):
            self._meal_pair(at, base=110 + index * 10)
        # Same short, explicitly linked episodes; only evidence-day changes.
        result = compute_paired_meal_response(patient_id=self.patient.id)
        self.assertEqual(result.complete_pair_count, 3)
        self.assertEqual(len(result.patterns), 1)
        self.assertEqual(result.patterns[0].distinct_days, 2)
        self.assertEqual(result.patterns[0].evidence_density, "limited")
        self.assertEqual(
            len({t.astimezone(self.plus_one).date() for t in starts}), 1
        )

    def test_explicit_episode_days_apart_is_not_capped_by_a_clinical_window(self):
        episode = uuid4()
        self._reading(
            self.before,
            glucose=110,
            meal_episode_id=episode,
            glycemic_context="pre_meal",
            meal_type="lunch",
        )
        self._reading(
            self.before + dt.timedelta(days=2, minutes=15),
            glucose=160,
            meal_episode_id=episode,
            glycemic_context="post_meal",
            meal_type="lunch",
        )
        result = compute_paired_meal_response(patient_id=self.patient.id)
        self.assertEqual(result.complete_pair_count, 1)
        self.assertEqual(result.pairs[0].elapsed_minutes, 2 * 1440 + 15)
        self.assertIn(
            "pre_post_delta_is_descriptive_not_causal", result.limitations
        )
        # Characterization only: an episode limit requires clinical/product
        # approval, not an invented 1–2h hard cutoff.

    def test_governed_longitudinal_counts_utc_days_per_population(self):
        times = (
            self.before,
            self.before + dt.timedelta(minutes=4),
            self.after,
        )
        for index, at in enumerate(times):
            self._reading(at, glucose=100 + index * 10, source="manual")
            self._reading(at, glucose=140 + index * 10, source="import")
        # Unrelated patient must never affect either day count.
        self._reading(self.after, glucose=450, patient=self.foreign_patient)
        contract = GovernedLongitudinalContract(
            fusion_contract=GovernedGlucoseFusionContract.journal_with(
                FusionPopulation.IMPORT
            )
        )
        result = compute_governed_longitudinal_intelligence(
            patient_id=self.patient.id,
            window_start=self.before - dt.timedelta(minutes=1),
            window_end=self.after + dt.timedelta(minutes=1),
            contract=contract,
        )
        self.assertEqual(result.status, "ready")
        by_population = {x.population: x for x in result.populations}
        for population in (FusionPopulation.JOURNAL, FusionPopulation.IMPORT):
            self.assertEqual(by_population[population].fact_count, 3)
            self.assertEqual(by_population[population].distinct_days, 2)
            self.assertTrue(by_population[population].sufficient)
        self.assertEqual(len(result.facts), 6)
        self.assertEqual(
            len({t.astimezone(self.plus_one).date() for t in times}), 1
        )

    def test_future_logged_at_cannot_promote_personal_evidence_to_ready(self):
        """The current evidence window may not include a later calendar day."""
        for index, at in enumerate(
            (self.before, self.before + dt.timedelta(minutes=4))
        ):
            self._reading(at, glucose=130 + index * 10, stressed="yes")
        # Without an upper bound, this future journal reading made two UTC
        # days and promoted a three-observation stress pattern to ready.
        self._reading(
            timezone.now() + dt.timedelta(days=2),
            glucose=180,
            stressed="yes",
        )

        result = compute_personal_response(patient_id=self.patient.id)

        self.assertEqual(result.total_readings, 2)
        self.assertEqual(result.distinct_days, 1)
        self.assertEqual(result.status, "insufficient_data")
        self.assertIsNone(result.window_median_glucose_mg_dl)
        self.assertEqual(result.patterns, ())

    def test_future_created_at_fallback_cannot_promote_personal_evidence(self):
        """Rows without logged_at must also use a closed historical window."""
        for index, at in enumerate(
            (self.before, self.before + dt.timedelta(minutes=4))
        ):
            self._reading(at, glucose=135 + index * 10, stressed="yes")
        fallback = LogEntry.objects.create(
            patient=self.patient,
            source="manual",
            logged_at=None,
            blood_sugar=190,
            stressed="yes",
        )
        # Simulate a corrupt/imported legacy created_at without implying
        # that a public write API accepts arbitrary future timestamps.
        LogEntry.objects.filter(pk=fallback.pk).update(
            created_at=timezone.now() + dt.timedelta(days=2)
        )

        result = compute_personal_response(patient_id=self.patient.id)

        self.assertEqual(result.total_readings, 2)
        self.assertEqual(result.distinct_days, 1)
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.patterns, ())

    def test_future_explicit_pair_remains_outside_paired_meal_window(self):
        """The paired-meal engine already bounds both sides at current now."""
        future = timezone.now() + dt.timedelta(days=2)
        self._meal_pair(future, base=140)

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.explicit_episode_count, 0)
        self.assertEqual(result.complete_pair_count, 0)
        self.assertEqual(result.patterns, ())
