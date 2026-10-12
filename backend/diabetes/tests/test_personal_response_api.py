from datetime import UTC, datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from diabetes.models.entry import LogEntry


class PersonalResponseApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="journal8-api-patient")
        self.other_patient = User.objects.create_user(username="journal8-api-other")
        self.now = timezone.now()

    def _log(self, patient, *, days_ago: int, glucose: int, stressed: str = ""):
        LogEntry.objects.create(
            patient=patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            stressed=stressed,
            source="manual",
        )

    def test_endpoint_requires_authentication(self):
        response = self.client.get("/api/v1/personal-response/")

        self.assertIn(response.status_code, {401, 403})

    def test_endpoint_is_patient_scoped_and_reports_synced_scope(self):
        for day, glucose in enumerate((150, 160, 170)):
            self._log(self.patient, days_ago=day, glucose=glucose, stressed="yes")
        for day, glucose in enumerate((240, 250, 260, 270)):
            self._log(self.other_patient, days_ago=day, glucose=glucose, stressed="yes")

        self.client.force_login(self.patient)
        response = self.client.get("/api/v1/personal-response/?days=90")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data_scope"], "server_synced_logs")
        self.assertEqual(payload["total_readings"], 3)
        self.assertEqual(payload["patterns"][0]["observations"], 3)
        self.assertEqual(payload["patterns"][0]["median_glucose_mg_dl"], 160.0)

    def test_requested_window_is_bounded_to_ninety_days(self):
        self._log(self.patient, days_ago=0, glucose=120)
        self._log(self.patient, days_ago=1, glucose=125)
        self._log(self.patient, days_ago=2, glucose=130)

        self.client.force_login(self.patient)
        response = self.client.get("/api/v1/personal-response/?days=365")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["window_days"], 90)

    def test_future_logged_at_is_absent_from_api_and_clinical_memory(self):
        """The public projection must not promote next-day future evidence."""
        now = timezone.now()
        # Pin the two valid rows to UTC noon, never a near-midnight
        # boundary dependent on when CI happens to execute.
        same_day = datetime.combine(
            (now - timedelta(days=10)).date(),
            time(hour=12),
            tzinfo=UTC,
        )
        for i in range(2):
            LogEntry.objects.create(
                patient=self.patient,
                logged_at=same_day + timedelta(minutes=4 * i),
                blood_sugar=130 + i * 10,
                stressed="yes",
                source="manual",
            )
        LogEntry.objects.create(
            patient=self.patient,
            logged_at=now + timedelta(days=2),
            blood_sugar=190,
            stressed="yes",
            source="manual",
        )

        self.client.force_login(self.patient)
        response = self.client.get("/api/v1/personal-response/?days=90")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "insufficient_data")
        self.assertEqual(payload["total_readings"], 2)
        self.assertEqual(payload["distinct_days"], 1)
        self.assertEqual(payload["patterns"], [])
        from diabetes.models.clinical_observation import ClinicalObservationState

        self.assertFalse(
            ClinicalObservationState.objects.filter(patient=self.patient).exists()
        )
