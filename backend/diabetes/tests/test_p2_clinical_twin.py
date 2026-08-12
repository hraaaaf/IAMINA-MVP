from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.evidence_registry import PERSONAL_RESPONSE_EVIDENCE_ID
from diabetes.services.clinical.observation_memory import (
    PRODUCER_ID,
    refresh_personal_response_memory,
)


class ClinicalObservationMemoryTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-twin-patient")
        self.other_patient = User.objects.create_user(username="p2-twin-other")
        self.now = timezone.now()

    def _log(
        self,
        *,
        patient=None,
        days_ago=0,
        glucose=120,
        stressed="",
        exercised="",
        glycemic_context="",
        meal_type="",
    ) -> LogEntry:
        return LogEntry.objects.create(
            patient=patient or self.patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            source="manual",
            stressed=stressed,
            exercised=exercised,
            glycemic_context=glycemic_context,
            meal_type=meal_type,
        )

    def _stress_pattern(self, *, patient=None, base=150) -> None:
        target = patient or self.patient
        for day, glucose in enumerate((base, base + 10, base + 20)):
            self._log(
                patient=target,
                days_ago=day,
                glucose=glucose,
                stressed="yes",
            )

    def test_first_sighting_persists_only_deterministic_observation_metadata(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=110)

        result = refresh_personal_response_memory(patient_id=self.patient.id)

        self.assertEqual(result.status, "ready")
        row = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        self.assertEqual(row.truth_kind, TruthKind.DETERMINISTIC_DERIVATION.value)
        self.assertEqual(row.status, ClinicalObservationState.STATUS_ACTIVE)
        self.assertEqual(row.recurrence_count, 1)
        self.assertEqual(row.evidence_strength, "limited")
        self.assertEqual(row.evidence_strength_trend, ClinicalObservationState.TREND_INITIAL)
        self.assertEqual(row.observations, 3)
        self.assertEqual(row.distinct_days, 3)
        self.assertEqual(row.observation_median_glucose_mg_dl, 160.0)
        self.assertEqual(row.window_median_glucose_mg_dl, 155.0)
        self.assertEqual(row.baseline_delta_mg_dl, 5.0)
        self.assertEqual(row.evidence_window_days, 90)
        self.assertEqual(row.evidence_id, PERSONAL_RESPONSE_EVIDENCE_ID)
        self.assertEqual(row.producer, PRODUCER_ID)
        self.assertEqual(
            row.context_modifiers,
            {"source_field": "stressed", "recorded_value": "yes"},
        )

    def test_same_supporting_evidence_is_semantically_idempotent(self):
        self._stress_pattern()

        refresh_personal_response_memory(patient_id=self.patient.id)
        first = ClinicalObservationState.objects.get(patient=self.patient)
        first_fingerprint = first.last_evidence_fingerprint

        refresh_personal_response_memory(patient_id=self.patient.id)
        second = ClinicalObservationState.objects.get(patient=self.patient)

        self.assertEqual(second.recurrence_count, 1)
        self.assertEqual(second.last_evidence_fingerprint, first_fingerprint)
        self.assertEqual(second.previous_evidence_strength, "")
        self.assertEqual(
            second.evidence_strength_trend,
            ClinicalObservationState.TREND_INITIAL,
        )
        self.assertIsNone(second.previous_baseline_delta_mg_dl)
        self.assertIsNone(second.baseline_delta_change_mg_dl)

    def test_new_support_strengthens_evidence_without_inflating_recurrence(self):
        self._stress_pattern()
        refresh_personal_response_memory(patient_id=self.patient.id)

        self._log(days_ago=3, glucose=180, stressed="yes")
        self._log(days_ago=4, glucose=190, stressed="yes")
        refresh_personal_response_memory(patient_id=self.patient.id)

        row = ClinicalObservationState.objects.get(patient=self.patient)
        self.assertEqual(row.recurrence_count, 1)
        self.assertEqual(row.previous_evidence_strength, "limited")
        self.assertEqual(row.evidence_strength, "moderate")
        self.assertEqual(
            row.evidence_strength_trend,
            ClinicalObservationState.TREND_STRENGTHENING,
        )
        self.assertEqual(row.observations, 5)

        refresh_personal_response_memory(patient_id=self.patient.id)
        row.refresh_from_db()
        self.assertEqual(row.recurrence_count, 1)
        self.assertEqual(row.previous_evidence_strength, "limited")
        self.assertEqual(row.evidence_strength, "moderate")
        self.assertEqual(
            row.evidence_strength_trend,
            ClinicalObservationState.TREND_STRENGTHENING,
        )

    def test_background_baseline_evolution_does_not_inflate_recurrence(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=100)
        refresh_personal_response_memory(patient_id=self.patient.id)
        before = ClinicalObservationState.objects.get(patient=self.patient)
        original_delta = before.baseline_delta_mg_dl

        self._log(days_ago=4, glucose=80)
        refresh_personal_response_memory(patient_id=self.patient.id)
        after = ClinicalObservationState.objects.get(patient=self.patient)

        self.assertEqual(after.recurrence_count, 1)
        self.assertNotEqual(after.baseline_delta_mg_dl, original_delta)
        self.assertEqual(after.previous_baseline_delta_mg_dl, original_delta)
        expected_change = round(after.baseline_delta_mg_dl - original_delta, 1)
        self.assertEqual(after.baseline_delta_change_mg_dl, expected_change)

        refresh_personal_response_memory(patient_id=self.patient.id)
        after.refresh_from_db()
        self.assertEqual(after.recurrence_count, 1)
        self.assertEqual(after.previous_baseline_delta_mg_dl, original_delta)
        self.assertEqual(after.baseline_delta_change_mg_dl, expected_change)

    def test_eligible_absence_and_true_reactivation_drive_lifecycle_recurrence(self):
        supporting = []
        for day, glucose in enumerate((150, 160, 170)):
            supporting.append(
                self._log(days_ago=day, glucose=glucose, stressed="yes")
            )
        refresh_personal_response_memory(patient_id=self.patient.id)

        LogEntry.objects.filter(id__in=[entry.id for entry in supporting]).update(
            logged_at=self.now - timedelta(days=100)
        )
        self._log(days_ago=0, glucose=110)
        refresh_personal_response_memory(patient_id=self.patient.id)
        row = ClinicalObservationState.objects.get(patient=self.patient)
        self.assertEqual(row.status, ClinicalObservationState.STATUS_ACTIVE)

        self._log(days_ago=1, glucose=115)
        self._log(days_ago=2, glucose=120)
        refresh_personal_response_memory(patient_id=self.patient.id)
        row.refresh_from_db()
        self.assertEqual(row.status, ClinicalObservationState.STATUS_INACTIVE)
        self.assertEqual(row.recurrence_count, 1)

        for day, glucose in ((3, 180), (4, 190), (5, 200)):
            self._log(days_ago=day, glucose=glucose, stressed="yes")
        refresh_personal_response_memory(patient_id=self.patient.id)
        row.refresh_from_db()
        self.assertEqual(row.status, ClinicalObservationState.STATUS_ACTIVE)
        self.assertEqual(row.recurrence_count, 2)

    def test_patient_state_is_strictly_isolated(self):
        self._stress_pattern(patient=self.patient, base=140)
        self._stress_pattern(patient=self.other_patient, base=220)

        refresh_personal_response_memory(patient_id=self.patient.id)
        refresh_personal_response_memory(patient_id=self.other_patient.id)

        patient_row = ClinicalObservationState.objects.get(patient=self.patient)
        other_row = ClinicalObservationState.objects.get(patient=self.other_patient)
        self.assertEqual(patient_row.observation_key, other_row.observation_key)
        self.assertNotEqual(
            patient_row.observation_median_glucose_mg_dl,
            other_row.observation_median_glucose_mg_dl,
        )
        self.assertEqual(
            ClinicalObservationState.objects.filter(patient=self.patient).count(),
            1,
        )

    def test_non_deterministic_truth_kinds_are_rejected_before_any_write(self):
        self._stress_pattern()
        forbidden = (
            TruthKind.USER_CLAIM,
            TruthKind.HEURISTIC_INFERENCE,
            TruthKind.MODEL_INFERENCE,
            TruthKind.CONVERSATIONAL_STATE,
            TruthKind.PREFERENCE,
            TruthKind.OBSERVED_FACT,
        )

        for truth_kind in forbidden:
            with self.assertRaises(ValueError):
                refresh_personal_response_memory(
                    patient_id=self.patient.id,
                    truth_kind=truth_kind,
                )

        self.assertFalse(ClinicalObservationState.objects.exists())

    def test_database_rejects_unapproved_producer_and_evidence_id(self):
        self._stress_pattern()
        refresh_personal_response_memory(patient_id=self.patient.id)
        row = ClinicalObservationState.objects.get(patient=self.patient)

        for field, value in (
            ("producer", "companion.deep_memory"),
            ("evidence_id", "rule.unreviewed.observation.v0"),
            ("truth_kind", TruthKind.MODEL_INFERENCE.value),
        ):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    ClinicalObservationState.objects.filter(pk=row.pk).update(
                        **{field: value}
                    )
            row.refresh_from_db()

        self.assertEqual(row.producer, PRODUCER_ID)
        self.assertEqual(row.evidence_id, PERSONAL_RESPONSE_EVIDENCE_ID)
        self.assertEqual(row.truth_kind, TruthKind.DETERMINISTIC_DERIVATION.value)


class ClinicalObservationMemoryApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="p2-twin-api")
        self.now = timezone.now()

    def _log(self, *, days_ago: int, glucose: int, stressed: str = "") -> None:
        LogEntry.objects.create(
            patient=self.patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            stressed=stressed,
            source="manual",
        )

    def test_short_display_window_cannot_toggle_canonical_clinical_memory(self):
        for day, glucose in ((30, 150), (31, 160), (32, 170)):
            self._log(days_ago=day, glucose=glucose, stressed="yes")
        self._log(days_ago=0, glucose=110)
        self._log(days_ago=1, glucose=115)
        self._log(days_ago=2, glucose=120)

        self.client.force_login(self.patient)
        response = self.client.get("/api/v1/personal-response/?days=7")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["window_days"], 7)
        self.assertEqual(response.json()["patterns"], [])
        row = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        self.assertEqual(row.status, ClinicalObservationState.STATUS_ACTIVE)
        self.assertEqual(row.evidence_window_days, 90)
        self.assertEqual(row.observations, 3)
