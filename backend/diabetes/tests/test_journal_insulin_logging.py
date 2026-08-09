from datetime import date
from json import loads

from django.contrib.auth.models import User
from django.test import Client, TestCase

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile, LogEntry


def _patient(username: str) -> User:
    user = User.objects.create_user(username=username, email=f"{username}@test.com")
    base = BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1985, 6, 15),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type2",
        treatment_type="insulin",
        target_range_low=70,
        target_range_high=180,
    )
    return user


class JournalInsulinLoggingTests(TestCase):
    def setUp(self):
        self.user = _patient("journal_insulin")
        self.client = Client()
        self.client.force_login(self.user)

    def test_decimal_administered_dose_is_persisted_without_rounding(self):
        response = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 128, "insulin_units": 4.5},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = loads(response.content)
        self.assertEqual(payload["insulin_units"], 4.5)
        self.assertEqual(float(LogEntry.objects.get(patient=self.user).insulin_units), 4.5)

    def test_negative_administered_dose_is_rejected(self):
        response = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 128, "insulin_units": -1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)
        self.assertFalse(LogEntry.objects.filter(patient=self.user).exists())

    def test_batch_replay_updates_same_patient_snapshot_instead_of_noop(self):
        client_uuid = "88888888-8888-8888-8888-888888888888"
        first = {
            "blood_sugar": 132,
            "glycemic_context": "pre_meal",
            "meal_type": "lunch",
            "insulin_units": 4.5,
            "client_uuid": client_uuid,
        }
        response = self.client.post(
            "/api/v1/logs/batch",
            data=[first],
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get(client_uuid=client_uuid)
        original_id = entry.id

        edited = dict(first)
        edited["insulin_units"] = 4.75
        response = self.client.post(
            "/api/v1/logs/batch",
            data=[edited],
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.id, original_id)
        self.assertEqual(float(entry.insulin_units), 4.75)
        self.assertEqual(entry.glycemic_context, "pre_meal")
        self.assertEqual(entry.meal_type, "lunch")

    def test_batch_uuid_owned_by_another_patient_is_not_accepted(self):
        client_uuid = "99999999-9999-9999-9999-999999999999"
        other = _patient("journal_insulin_other")
        LogEntry.objects.create(
            patient=other,
            blood_sugar=140,
            insulin_units=3,
            client_uuid=client_uuid,
        )
        response = self.client.post(
            "/api/v1/logs/batch",
            data=[{
                "blood_sugar": 120,
                "insulin_units": 8,
                "client_uuid": client_uuid,
            }],
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = loads(response.content)
        self.assertEqual(payload["synced_ids"], [])
        self.assertEqual(len(payload["errors"]), 1)
        existing = LogEntry.objects.get(client_uuid=client_uuid)
        self.assertEqual(existing.patient_id, other.id)
        self.assertEqual(float(existing.insulin_units), 3.0)
