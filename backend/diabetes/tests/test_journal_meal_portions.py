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
        treatment_type="oral_meds",
        target_range_low=70,
        target_range_high=180,
    )
    return user


class JournalMealPortionTests(TestCase):
    def setUp(self):
        self.user = _patient("journal_portions")
        self.client = Client()
        self.client.force_login(self.user)

    def test_existing_style_log_keeps_empty_portions_without_inference(self):
        response = self.client.post(
            "/api/v1/logs",
            data={
                "blood_sugar": 126,
                "meal_type": "lunch",
                "meal_items": ["couscous"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = loads(response.content)
        self.assertEqual(payload["meal_portions"], [])
        entry = LogEntry.objects.get(patient=self.user)
        self.assertEqual(entry.meal_portions, [])

    def test_natural_portion_is_persisted_as_user_input_only(self):
        response = self.client.post(
            "/api/v1/logs",
            data={
                "blood_sugar": 132,
                "meal_type": "breakfast",
                "meal_items": ["msemen"],
                "meal_portions": [
                    {"food_id": "msemen", "portion_id": "one_piece"},
                ],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = loads(response.content)
        self.assertEqual(
            payload["meal_portions"],
            [{"food_id": "msemen", "portion_id": "one_piece", "grams": None}],
        )
        entry = LogEntry.objects.get(patient=self.user)
        self.assertEqual(entry.meal_portions[0]["food_id"], "msemen")
        self.assertNotIn("carbs", entry.meal_portions[0])
        self.assertNotIn("calories", entry.meal_portions[0])
        self.assertNotIn("glycemic_index", entry.meal_portions[0])

    def test_manual_grams_are_bounded_and_persisted(self):
        response = self.client.post(
            "/api/v1/logs",
            data={
                "blood_sugar": 141,
                "meal_items": ["apple"],
                "meal_portions": [
                    {"food_id": "apple", "grams": 135},
                ],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get(patient=self.user)
        self.assertEqual(entry.meal_portions[0]["grams"], 135.0)

    def test_portion_without_portion_id_or_grams_is_rejected(self):
        response = self.client.post(
            "/api/v1/logs",
            data={
                "blood_sugar": 141,
                "meal_items": ["apple"],
                "meal_portions": [{"food_id": "apple"}],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(LogEntry.objects.filter(patient=self.user).count(), 0)

    def test_batch_sync_preserves_portions_and_client_uuid(self):
        uuid = "77777777-7777-7777-7777-777777777777"
        response = self.client.post(
            "/api/v1/logs/batch",
            data=[
                {
                    "blood_sugar": 154,
                    "meal_type": "lunch",
                    "meal_items": ["moroccan_bread"],
                    "meal_portions": [
                        {"food_id": "moroccan_bread", "portion_id": "quarter"},
                    ],
                    "client_uuid": uuid,
                }
            ],
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get(client_uuid=uuid)
        self.assertEqual(entry.meal_items, ["moroccan_bread"])
        self.assertEqual(
            entry.meal_portions,
            [{"food_id": "moroccan_bread", "portion_id": "quarter", "grams": None}],
        )
