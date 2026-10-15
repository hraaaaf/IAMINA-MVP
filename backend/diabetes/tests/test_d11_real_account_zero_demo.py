"""D11: no authenticated patient can receive fabricated demo clinical data."""

from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import Client, TestCase
from ninja.errors import HttpError

from core.models import BasePatientProfile
from core.native_auth import issue_native_token, verify_native_token
from diabetes.api.v1.demo import seed_demo_data
from diabetes.models import DiabetesProfile, LogEntry


class DemoSeedPatientIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient_a = User.objects.create_user(
            username="d11_real_patient_a",
            email="d11-a@example.test",
            password="synthetic-password-never-used",
        )
        self.patient_b = User.objects.create_user(
            username="d11_real_patient_b",
            email="d11-b@example.test",
            password="synthetic-password-never-used",
        )
        self.token_a = issue_native_token(self.patient_a)
        self.token_b = issue_native_token(self.patient_b)
        # These are genuine, verifiable native bearers; no fabricated token.
        self.assertEqual(verify_native_token(self.token_a).pk, self.patient_a.pk)
        self.assertEqual(verify_native_token(self.token_b).pk, self.patient_b.pk)

    def _seed(self, token):
        return self.client.post(
            "/api/v1/demo/seed",
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    def test_fresh_authenticated_patient_cannot_receive_demo_logs_or_profile(self):
        response = self._seed(self.token_a)
        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(LogEntry.objects.filter(patient=self.patient_a).count(), 0)
        self.assertFalse(
            DiabetesProfile.objects.filter(base_profile__patient=self.patient_a).exists()
        )
        # Native token creation only builds an empty identity profile.
        base = BasePatientProfile.objects.get(patient=self.patient_a)
        self.assertIsNone(base.date_of_birth)
        self.assertIsNone(base.gender)

    def test_seed_cannot_mutate_existing_patient_or_any_other_patient(self):
        real_entry = LogEntry.objects.create(
            patient=self.patient_a,
            blood_sugar=Decimal("126.00"),
            source="manual",
        )
        other_entry = LogEntry.objects.create(
            patient=self.patient_b,
            blood_sugar=Decimal("102.00"),
            source="manual",
        )

        for token in (self.token_a, self.token_b):
            for _ in range(2):
                self.assertIn(self._seed(token).status_code, (401, 403))

        self.assertEqual(
            list(LogEntry.objects.filter(patient=self.patient_a).values_list("id", flat=True)),
            [real_entry.pk],
        )
        self.assertEqual(
            list(LogEntry.objects.filter(patient=self.patient_b).values_list("id", flat=True)),
            [other_entry.pk],
        )

    def test_even_demo_named_authenticated_account_cannot_seed_patient_history(self):
        demo = User.objects.create_user(
            username="patient1",
            password="synthetic-demo-only",
        )
        token = issue_native_token(demo)
        self.assertIn(self._seed(token).status_code, (401, 403))
        self.assertFalse(LogEntry.objects.filter(patient=demo).exists())

    def test_actual_seed_handler_denies_authenticated_request_with_403(self):
        # HTTP auth may reject a credential earlier (401). Once the operation
        # is reached with an authenticated patient, it must explicitly return
        # 403 before any synthetic rows/profile are written.
        with self.assertRaises(HttpError) as error:
            seed_demo_data(SimpleNamespace(user=self.patient_a))
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(LogEntry.objects.filter(patient=self.patient_a).count(), 0)

    def test_anonymous_seed_request_stays_unauthorized(self):
        response = self.client.post(
            "/api/v1/demo/seed", data={}, content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_native_registration_exposes_zero_fabricated_clinical_records(self):
        response = self.client.post(
            "/api/v1/auth/register",
            data={
                "email": "d11-new-signup@example.test",
                "password": "Distinct-Strong-Passphrase-2026!",
                "first_name": "Synthetic",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        bearer = response.json()["access_token"]
        user = User.objects.get(email="d11-new-signup@example.test")

        self.assertEqual(LogEntry.objects.filter(patient=user).count(), 0)
        self.assertFalse(
            DiabetesProfile.objects.filter(base_profile__patient=user).exists()
        )
        self.assertIsNone(BasePatientProfile.objects.get(patient=user).date_of_birth)

        medical_history = self.client.get(
            "/api/v1/logs",
            HTTP_AUTHORIZATION=f"Bearer {bearer}",
        )
        self.assertEqual(medical_history.status_code, 200)
        self.assertEqual(medical_history.json()["total"], 0)
        self.assertEqual(self._seed(bearer).status_code, 403)
        self.assertEqual(LogEntry.objects.filter(patient=user).count(), 0)

    def test_read_only_demo_scenarios_are_still_available(self):
        response = self.client.get("/api/v1/demo/scenarios")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 8)
