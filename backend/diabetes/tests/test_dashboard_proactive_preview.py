from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.observation_memory import refresh_personal_response_memory
from diabetes.services.clinical.proactive_intelligence import evaluate_proactive_insights
from diabetes.services.clinical.proactive_preview import preview_proactive_insights


class DashboardProactivePreviewTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="dashboard-preview-patient")
        self.now = timezone.now()

    def _log(
        self,
        *,
        days_ago: int,
        glucose: int,
        stressed: str = "",
        exercised: str = "",
    ) -> LogEntry:
        return LogEntry.objects.create(
            patient=self.patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            source="manual",
            stressed=stressed,
            exercised=exercised,
        )

    def _stress_pattern(self) -> None:
        for day, glucose in enumerate((150, 160, 170)):
            self._log(days_ago=day, glucose=glucose, stressed="yes")
        self._log(days_ago=3, glucose=110)

    def _two_patterns(self) -> None:
        for day, glucose in enumerate((150, 160, 170)):
            self._log(
                days_ago=day,
                glucose=glucose,
                stressed="yes",
                exercised="yes",
            )
        self._log(days_ago=3, glucose=110)

    def test_preview_reuses_governed_authority_without_creating_delivery_state(self):
        self._stress_pattern()
        refresh_personal_response_memory(patient_id=self.patient.id)
        observation = ClinicalObservationState.objects.get(patient=self.patient)
        refreshed_at = observation.last_refreshed_at

        result = preview_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        self.assertEqual(result.status, "available")
        self.assertEqual(result.pending_count, 1)
        self.assertIsNotNone(result.item)
        item = result.item
        assert item is not None
        self.assertEqual(item.observation_key, "context:stress")
        self.assertFalse(item.surface_now)
        self.assertEqual(item.escalation_class, "none")
        self.assertEqual(item.priority.safety_time_sensitivity, "non_urgent_observation")
        self.assertIn(item.allowed_next_step, {"MONITOR", "PREPARE_CLINICIAN_DISCUSSION"})
        self.assertEqual(ProactiveInsightState.objects.count(), 0)

        observation.refresh_from_db()
        self.assertEqual(observation.last_refreshed_at, refreshed_at)

    def test_preview_and_mutating_command_choose_the_same_governed_candidate(self):
        self._two_patterns()
        refresh_personal_response_memory(patient_id=self.patient.id)

        preview = preview_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )
        self.assertEqual(ProactiveInsightState.objects.count(), 0)
        self.assertIsNotNone(preview.item)

        evaluated = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        self.assertIsNotNone(evaluated.item)
        assert preview.item is not None
        assert evaluated.item is not None
        self.assertEqual(preview.item.observation_key, evaluated.item.observation_key)
        self.assertEqual(preview.item.allowed_next_step, evaluated.item.allowed_next_step)
        self.assertEqual(preview.item.evidence_id, evaluated.item.evidence_id)

    def test_preview_respects_existing_cooldown_without_mutating_it(self):
        self._two_patterns()
        first = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )
        self.assertEqual(first.status, "surfaced")
        surfaced = ProactiveInsightState.objects.exclude(last_surfaced_at=None).get()
        surfaced_at = surfaced.last_surfaced_at
        delivered_signature = surfaced.last_delivered_signature

        preview = preview_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=1),
        )

        self.assertEqual(preview.status, "cooldown")
        self.assertIsNone(preview.item)
        self.assertGreaterEqual(preview.pending_count, 1)
        surfaced.refresh_from_db()
        self.assertEqual(surfaced.last_surfaced_at, surfaced_at)
        self.assertEqual(surfaced.last_delivered_signature, delivered_signature)

    def test_preview_fails_closed_without_governed_clinical_twin_state(self):
        result = preview_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        self.assertEqual(result.status, "insufficient_data")
        self.assertIsNone(result.item)
        self.assertEqual(result.pending_count, 0)
        self.assertEqual(ClinicalObservationState.objects.count(), 0)
        self.assertEqual(ProactiveInsightState.objects.count(), 0)


class DashboardProactivePreviewApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="dashboard-preview-api")
        self.other = User.objects.create_user(username="dashboard-preview-other")
        self.now = timezone.now()

    def _pattern(self, patient: User, *, base: int) -> None:
        for day, glucose in enumerate((base, base + 10, base + 20)):
            LogEntry.objects.create(
                patient=patient,
                logged_at=self.now - timedelta(days=day),
                blood_sugar=glucose,
                source="manual",
                stressed="yes",
            )
        LogEntry.objects.create(
            patient=patient,
            logged_at=self.now - timedelta(days=3),
            blood_sugar=base - 30,
            source="manual",
        )

    def test_preview_get_is_patient_scoped_repeatable_and_non_mutating(self):
        self._pattern(self.patient, base=150)
        self._pattern(self.other, base=220)
        refresh_personal_response_memory(patient_id=self.patient.id)
        refresh_personal_response_memory(patient_id=self.other.id)
        self.client.force_login(self.patient)
        patient_observation = ClinicalObservationState.objects.get(patient=self.patient)
        refreshed_at = patient_observation.last_refreshed_at

        first = self.client.get("/api/v1/proactive-insights/preview/")
        second = self.client.get("/api/v1/proactive-insights/preview/")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        payload = first.json()
        self.assertEqual(payload["status"], "available")
        self.assertIn("does not consume", payload["safety_notice"])
        self.assertIsNotNone(payload["item"])
        self.assertFalse(payload["item"]["surface_now"])
        self.assertEqual(payload["item"]["escalation_class"], "none")
        self.assertEqual(
            ProactiveInsightState.objects.filter(
                observation__patient=self.patient
            ).count(),
            0,
        )
        self.assertEqual(
            ProactiveInsightState.objects.filter(
                observation__patient=self.other
            ).count(),
            0,
        )
        patient_observation.refresh_from_db()
        self.assertEqual(patient_observation.last_refreshed_at, refreshed_at)
