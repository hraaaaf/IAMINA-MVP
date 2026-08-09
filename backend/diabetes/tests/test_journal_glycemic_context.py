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


class JournalGlycemicContextTests(TestCase):
    def setUp(self):
        self.user = _patient("journal_context")
        self.client = Client()
        self.client.force_login(self.user)

    def test_create_keeps_glycemic_context_separate_from_meal_type(self):
        response = self.client.post(
            "/api/v1/logs",
            data={
                "blood_sugar": 126,
                "glycemic_context": "pre_meal",
                "meal_type": "lunch",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = loads(response.content)
        self.assertEqual(payload["glycemic_context"], "pre_meal")
        self.assertEqual(payload["meal_type"], "lunch")
        entry = LogEntry.objects.get(patient=self.user)
        self.assertEqual(entry.glycemic_context, "pre_meal")
        self.assertEqual(entry.meal_type, "lunch")

    def test_context_is_optional_and_not_inferred(self):
        response = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 126, "meal_type": "lunch"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = loads(response.content)
        self.assertEqual(payload["glycemic_context"], "")
        self.assertEqual(payload["meal_type"], "lunch")

    def test_batch_sync_preserves_context_and_client_uuid_idempotency(self):
        uuid = "44444444-4444-4444-4444-444444444444"
        data = [
            {
                "blood_sugar": 142,
                "glycemic_context": "post_meal",
                "meal_type": "dinner",
                "client_uuid": uuid,
            }
        ]
        first = self.client.post(
            "/api/v1/logs/batch", data=data, content_type="application/json"
        )
        second = self.client.post(
            "/api/v1/logs/batch", data=data, content_type="application/json"
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(LogEntry.objects.filter(client_uuid=uuid).count(), 1)
        entry = LogEntry.objects.get(client_uuid=uuid)
        self.assertEqual(entry.glycemic_context, "post_meal")
        self.assertEqual(entry.meal_type, "dinner")

    def test_structured_meal_items_are_preserved_without_inference(self):
        response = self.client.post(
            "/api/v1/logs",
            data={
                "blood_sugar": 128,
                "meal_type": "breakfast",
                "meal_items": ["moroccan_bread", "egg", "mint_tea"],
                "meal_description": "sans sucre",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = loads(response.content)
        self.assertEqual(
            payload["meal_items"],
            ["moroccan_bread", "egg", "mint_tea"],
        )
        entry = LogEntry.objects.get(patient=self.user)
        self.assertEqual(
            entry.meal_items,
            ["moroccan_bread", "egg", "mint_tea"],
        )
        self.assertEqual(entry.meal_description, "sans sucre")

    def test_batch_sync_preserves_structured_meal_items(self):
        uuid = "66666666-6666-6666-6666-666666666666"
        response = self.client.post(
            "/api/v1/logs/batch",
            data=[{
                "blood_sugar": 154,
                "meal_type": "lunch",
                "meal_items": ["couscous", "vegetables"],
                "client_uuid": uuid,
            }],
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get(client_uuid=uuid)
        self.assertEqual(entry.meal_items, ["couscous", "vegetables"])
