from __future__ import annotations

import datetime as dt

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from diabetes.contracts.multi_source_fusion import (
    FusionContractError,
    FusionPopulation,
    GovernedGlucoseFusionContract,
)
from diabetes.models import CGMReadingRecord, CGMSensorSession, LogEntry
from diabetes.services.clinical.multi_source_fusion import (
    FusionInputError,
    fuse_governed_glucose_sources,
)


class GovernedGlucoseFusionContractTests(SimpleTestCase):
    def test_requires_journal_plus_explicit_external_population(self):
        with self.assertRaises(FusionContractError):
            GovernedGlucoseFusionContract(
                requested_populations=frozenset({FusionPopulation.JOURNAL})
            )
        with self.assertRaises(FusionContractError):
            GovernedGlucoseFusionContract(
                requested_populations=frozenset({FusionPopulation.CGM})
            )

        contract = GovernedGlucoseFusionContract.journal_with(
            FusionPopulation.CGM,
            FusionPopulation.IMPORT,
        )
        self.assertEqual(
            contract.requested_populations,
            frozenset(
                {
                    FusionPopulation.JOURNAL,
                    FusionPopulation.CGM,
                    FusionPopulation.IMPORT,
                }
            ),
        )

    def test_cross_source_deduplication_cannot_be_enabled_implicitly(self):
        with self.assertRaises(FusionContractError):
            GovernedGlucoseFusionContract(
                requested_populations=frozenset(
                    {FusionPopulation.JOURNAL, FusionPopulation.IMPORT}
                ),
                preserve_cross_source_duplicates=False,
            )


class GovernedMultiSourceFusionTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="v2c-patient")
        self.other_patient = User.objects.create_user(username="v2c-other")
        self.start = dt.datetime(2026, 9, 1, tzinfo=dt.UTC)
        self.end = dt.datetime(2026, 9, 3, tzinfo=dt.UTC)
        self.contract = GovernedGlucoseFusionContract.journal_with(
            FusionPopulation.CGM,
            FusionPopulation.IMPORT,
        )
        self.session = CGMSensorSession.objects.create(
            patient=self.patient,
            source="linx",
            session_key="v2c-session",
            started_at=self.start,
            ended_at=self.end,
            expected_interval_minutes=5,
            timezone_name="UTC",
            end_reason=CGMSensorSession.EndReason.REPLACED,
        )

    def _log(self, *, source: str, when: dt.datetime, glucose: int, patient=None):
        return LogEntry.objects.create(
            patient=patient or self.patient,
            source=source,
            logged_at=when,
            blood_sugar=glucose,
        )

    def test_fusion_preserves_population_and_fact_provenance(self):
        when = self.start + dt.timedelta(hours=1)
        manual = self._log(source="manual", when=when, glucose=126)
        voice = self._log(
            source="voice",
            when=when + dt.timedelta(minutes=5),
            glucose=127,
        )
        imported = self._log(
            source="import",
            when=when + dt.timedelta(minutes=10),
            glucose=128,
        )
        cgm = CGMReadingRecord.objects.create(
            patient=self.patient,
            source="linx",
            session=self.session,
            recorded_at=when + dt.timedelta(minutes=15),
            glucose_mg_dl=129,
            dedupe_key="v2c-valid",
        )

        result = fuse_governed_glucose_sources(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
            contract=self.contract,
        )

        self.assertEqual(len(result.facts), 4)
        by_ref = {item.fact.source_ref: item for item in result.facts}
        self.assertEqual(
            by_ref[f"log_entry:{manual.id}"].population,
            FusionPopulation.JOURNAL,
        )
        self.assertEqual(
            by_ref[f"log_entry:{voice.id}"].population,
            FusionPopulation.JOURNAL,
        )
        self.assertEqual(
            by_ref[f"log_entry:{imported.id}"].population,
            FusionPopulation.IMPORT,
        )
        cgm_item = by_ref[f"cgm:linx:{cgm.dedupe_key}"]
        self.assertEqual(cgm_item.population, FusionPopulation.CGM)

        for item in result.facts:
            self.assertIsNotNone(item.fact.provenance)
            self.assertEqual(
                item.fact.provenance.source_ref,
                item.fact.source_ref,
            )

    def test_same_value_and_timestamp_from_two_sources_are_not_silently_deduplicated(self):
        when = self.start + dt.timedelta(hours=2)
        self._log(source="manual", when=when, glucose=140)
        self._log(source="import", when=when, glucose=140)

        result = fuse_governed_glucose_sources(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
            contract=GovernedGlucoseFusionContract.journal_with(
                FusionPopulation.IMPORT
            ),
        )

        self.assertEqual(len(result.facts), 2)
        self.assertEqual(
            {item.population for item in result.facts},
            {FusionPopulation.JOURNAL, FusionPopulation.IMPORT},
        )
        self.assertIn(
            "cross_source_duplicates_preserved_not_deduplicated",
            result.limitations,
        )

    def test_legacy_logentry_cgm_is_excluded_and_reported(self):
        when = self.start + dt.timedelta(hours=3)
        self._log(source="manual", when=when, glucose=120)
        self._log(source="cgm", when=when, glucose=220)

        result = fuse_governed_glucose_sources(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
            contract=GovernedGlucoseFusionContract.journal_with(
                FusionPopulation.CGM
            ),
        )

        self.assertEqual(len(result.facts), 1)
        journal_summary = next(
            summary
            for summary in result.population_summaries
            if summary.population is FusionPopulation.JOURNAL
        )
        self.assertEqual(journal_summary.excluded_count, 1)
        self.assertEqual(
            journal_summary.exclusion_reason,
            "legacy_logentry_cgm_not_authorized",
        )

    def test_unlinked_cgm_transport_row_fails_closed(self):
        when = self.start + dt.timedelta(hours=4)
        CGMReadingRecord.objects.create(
            patient=self.patient,
            source="linx",
            session=None,
            recorded_at=when,
            glucose_mg_dl=170,
            dedupe_key="v2c-unlinked",
        )
        self._log(source="manual", when=when, glucose=130)

        result = fuse_governed_glucose_sources(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
            contract=GovernedGlucoseFusionContract.journal_with(
                FusionPopulation.CGM
            ),
        )

        self.assertEqual(len(result.facts), 1)
        cgm_summary = next(
            summary
            for summary in result.population_summaries
            if summary.population is FusionPopulation.CGM
        )
        self.assertEqual(cgm_summary.included_count, 0)
        self.assertEqual(cgm_summary.excluded_count, 1)
        self.assertEqual(
            cgm_summary.exclusion_reason,
            "missing_or_invalid_sensor_session_linkage",
        )

    def test_patient_scope_is_never_crossed(self):
        when = self.start + dt.timedelta(hours=5)
        self._log(source="manual", when=when, glucose=125)
        self._log(
            source="manual",
            when=when,
            glucose=250,
            patient=self.other_patient,
        )
        self._log(
            source="import",
            when=when,
            glucose=260,
            patient=self.other_patient,
        )

        result = fuse_governed_glucose_sources(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
            contract=self.contract,
        )

        self.assertEqual(len(result.facts), 1)
        self.assertEqual(result.facts[0].fact.subject_ref, f"patient:{self.patient.id}")

    def test_contract_and_timezone_are_required(self):
        with self.assertRaises(FusionInputError):
            fuse_governed_glucose_sources(
                patient_id=self.patient.id,
                window_start=self.start.replace(tzinfo=None),
                window_end=self.end.replace(tzinfo=None),
                contract=self.contract,
            )
        with self.assertRaises(FusionInputError):
            fuse_governed_glucose_sources(
                patient_id=self.patient.id,
                window_start=self.start,
                window_end=self.end,
                contract=None,  # type: ignore[arg-type]
            )
