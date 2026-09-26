from __future__ import annotations

import datetime as dt

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from diabetes.contracts.governed_longitudinal import (
    GovernedLongitudinalContract,
    LongitudinalContractError,
)
from diabetes.contracts.multi_source_fusion import (
    FusionPopulation,
    GovernedGlucoseFusionContract,
)
from diabetes.models import LogEntry
from diabetes.services.clinical.governed_longitudinal import (
    compute_governed_longitudinal_intelligence,
)
from diabetes.services.import_identity import make_import_client_uuid


class GovernedLongitudinalContractTests(SimpleTestCase):
    def test_requires_governed_fusion_contract_and_positive_sufficiency(self):
        fusion = GovernedGlucoseFusionContract.journal_with(FusionPopulation.IMPORT)
        contract = GovernedLongitudinalContract(fusion_contract=fusion)
        self.assertEqual(contract.minimum_facts_per_population, 3)
        self.assertEqual(contract.minimum_distinct_days_per_population, 2)

        with self.assertRaises(LongitudinalContractError):
            GovernedLongitudinalContract(
                fusion_contract=fusion,
                minimum_facts_per_population=0,
            )


class GovernedLongitudinalIntelligenceTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="v2d-patient")
        self.other = User.objects.create_user(username="v2d-other")
        self.start = dt.datetime(2026, 9, 1, tzinfo=dt.UTC)
        self.end = dt.datetime(2026, 9, 5, tzinfo=dt.UTC)
        self.contract = GovernedLongitudinalContract(
            fusion_contract=GovernedGlucoseFusionContract.journal_with(
                FusionPopulation.IMPORT
            )
        )

    def _log(self, *, source: str, when: dt.datetime, glucose: int, patient=None):
        target = patient or self.patient
        kwargs = {}
        if source == "import":
            kwargs["client_uuid"] = make_import_client_uuid(
                target.id,
                when,
                glucose,
            )
        return LogEntry.objects.create(
            patient=target,
            source=source,
            logged_at=when,
            blood_sugar=glucose,
            **kwargs,
        )

    def test_ready_requires_sufficient_evidence_in_each_requested_population(self):
        for index, glucose in enumerate((110, 120, 130)):
            self._log(
                source="manual",
                when=self.start + dt.timedelta(days=index // 2, hours=index),
                glucose=glucose,
            )
            self._log(
                source="import",
                when=self.start + dt.timedelta(days=index // 2, hours=index, minutes=10),
                glucose=glucose + 5,
            )

        result = compute_governed_longitudinal_intelligence(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
            contract=self.contract,
        )

        self.assertEqual(result.status, "ready")
        by_population = {item.population: item for item in result.populations}
        self.assertTrue(by_population[FusionPopulation.JOURNAL].sufficient)
        self.assertTrue(by_population[FusionPopulation.IMPORT].sufficient)
        self.assertEqual(
            by_population[FusionPopulation.JOURNAL].median_glucose_mg_dl,
            120.0,
        )
        self.assertEqual(
            by_population[FusionPopulation.IMPORT].median_glucose_mg_dl,
            125.0,
        )
        self.assertEqual(len(result.facts), 6)
        self.assertIn("population_boundaries_preserved", result.limitations)
        self.assertIn(
            "cross_source_comparison_is_descriptive_not_causal",
            result.limitations,
        )

    def test_one_population_insufficient_fails_closed_without_dropping_facts(self):
        for index in range(3):
            self._log(
                source="manual",
                when=self.start + dt.timedelta(days=index // 2, hours=index),
                glucose=100 + index,
            )
        self._log(
            source="import",
            when=self.start + dt.timedelta(hours=2),
            glucose=140,
        )

        result = compute_governed_longitudinal_intelligence(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
            contract=self.contract,
        )

        self.assertEqual(result.status, "insufficient_data")
        by_population = {item.population: item for item in result.populations}
        self.assertTrue(by_population[FusionPopulation.JOURNAL].sufficient)
        self.assertFalse(by_population[FusionPopulation.IMPORT].sufficient)
        self.assertEqual(len(result.facts), 4)

    def test_source_refs_and_patient_scope_are_preserved(self):
        journal = self._log(
            source="manual",
            when=self.start + dt.timedelta(hours=1),
            glucose=120,
        )
        imported = self._log(
            source="import",
            when=self.start + dt.timedelta(hours=2),
            glucose=125,
        )
        self._log(
            source="manual",
            when=self.start + dt.timedelta(hours=3),
            glucose=250,
            patient=self.other,
        )

        result = compute_governed_longitudinal_intelligence(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
            contract=self.contract,
        )

        refs = {item.fact.source_ref for item in result.facts}
        self.assertEqual(
            refs,
            {f"log_entry:{journal.id}", f"log_entry:{imported.id}"},
        )
        self.assertTrue(
            all(
                item.fact.subject_ref == f"patient:{self.patient.id}"
                for item in result.facts
            )
        )

    def test_contract_object_is_required(self):
        with self.assertRaises(TypeError):
            compute_governed_longitudinal_intelligence(
                patient_id=self.patient.id,
                window_start=self.start,
                window_end=self.end,
                contract=None,  # type: ignore[arg-type]
            )
