"""Decision #2: proactive insight is NOT an OS notification, reminder or LLM push.

These synthetic API regressions verify the patient/session and delivery-bookkeeping
boundary on the existing Django Ninja proactive routes. They do not authorize a
notification, a clinical prediction or a patient messaging feature.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.observation_memory import refresh_personal_response_memory


class Decision02ProactiveApiBoundaryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="v1-decision02-owner")
        self.foreign = User.objects.create_user(username="v1-decision02-foreign")
        self.now = timezone.now()

    def _seed_pattern(self, patient, *, stressed=True):
        for day, glucose in enumerate((150, 160, 170)):
            LogEntry.objects.create(
                patient=patient,
                logged_at=self.now - timedelta(days=day),
                blood_sugar=glucose,
                source="manual",
                stressed="yes" if stressed else "",
            )
        LogEntry.objects.create(
            patient=patient,
            logged_at=self.now - timedelta(days=3),
            blood_sugar=110,
            source="manual",
        )

    def test_anonymous_preview_and_evaluation_cannot_access_patient_evidence(self):
        self._seed_pattern(self.foreign)
        refresh_personal_response_memory(patient_id=self.foreign.id)
        prior_observation_count = ClinicalObservationState.objects.count()

        for method, path in (
            ("get", "/api/v1/proactive-insights/preview/"),
            ("post", "/api/v1/proactive-insights/evaluate/"),
        ):
            response = getattr(self.client, method)(path)
            self.assertIn(response.status_code, {401, 403})
            self.assertEqual(
                ProactiveInsightState.objects.count(),
                0,
                "An unauthenticated read or command must never consume attention",
            )

        self.assertEqual(
            ClinicalObservationState.objects.count(), prior_observation_count
        )

    def test_request_supplied_patient_id_never_overrides_authenticated_subject(self):
        self._seed_pattern(self.foreign)
        refresh_personal_response_memory(patient_id=self.foreign.id)
        self.client.force_login(self.patient)

        preview = self.client.get(
            "/api/v1/proactive-insights/preview/",
            {"patient_id": self.foreign.id},
        )
        evaluated = self.client.post(
            f"/api/v1/proactive-insights/evaluate/?patient_id={self.foreign.id}",
            data='{"patient_id": 999999}',
            content_type="application/json",
        )

        self.assertEqual(preview.status_code, 200)
        self.assertEqual(evaluated.status_code, 200)
        self.assertEqual(preview.json()["status"], "insufficient_data")
        self.assertEqual(evaluated.json()["status"], "insufficient_data")
        self.assertIsNone(preview.json()["item"])
        self.assertIsNone(evaluated.json()["item"])
        self.assertFalse(
            ProactiveInsightState.objects.filter(
                observation__patient=self.foreign
            ).exists()
        )
        self.assertFalse(
            ProactiveInsightState.objects.filter(
                observation__patient=self.patient
            ).exists()
        )

    def test_preview_is_read_only_and_evaluate_replay_not_second_delivery(self):
        self._seed_pattern(self.patient)
        refresh_personal_response_memory(patient_id=self.patient.id)
        observation = ClinicalObservationState.objects.get(patient=self.patient)
        unchanged_at = observation.last_refreshed_at
        self.client.force_login(self.patient)

        first = self.client.get("/api/v1/proactive-insights/preview/")
        second = self.client.get("/api/v1/proactive-insights/preview/")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(first.json()["status"], "available")
        self.assertFalse(first.json()["item"]["surface_now"])
        self.assertFalse(ProactiveInsightState.objects.exists())
        observation.refresh_from_db()
        self.assertEqual(observation.last_refreshed_at, unchanged_at)

        shown = self.client.post(
            "/api/v1/proactive-insights/evaluate/",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(shown.status_code, 200)
        self.assertEqual(shown.json()["status"], "surfaced")
        self.assertTrue(shown.json()["item"]["surface_now"])
        self.assertEqual(shown.json()["item"]["escalation_class"], "none")
        delivery = ProactiveInsightState.objects.get(
            observation__patient=self.patient
        )
        first_signature = delivery.last_delivered_signature
        first_at = delivery.last_surfaced_at

        replay = self.client.post(
            "/api/v1/proactive-insights/evaluate/",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["status"], "no_change")
        self.assertIsNone(replay.json()["item"])
        delivery.refresh_from_db()
        self.assertEqual(delivery.last_delivered_signature, first_signature)
        self.assertEqual(delivery.last_surfaced_at, first_at)
        self.assertEqual(ProactiveInsightState.objects.count(), 1)
