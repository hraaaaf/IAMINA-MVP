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
        # Real HTTP auth in Django test client may have different request
        # middleware from direct signer calls; verify account and bearer via
        # the same login endpoint used by Flutter's native AuthService.
        self.client_a = Client()
        self.client_b = Client()
        self.token_a = self._login(self.patient_a, self.client_a)
        self.token_b = self._login(self.patient_b, self.client_b)
        self.assertEqual(verify_native_token(self.token_a).pk, self.patient_a.pk)
        self.assertEqual(verify_native_token(self.token_b).pk, self.patient_b.pk)

    def _login(self, user, client):
        response = client.post(
            "/api/v1/auth/login",
            data={"email": user.email, "password": "synthetic-password-never-used"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["access_token"]

    def _seed(self, token):
        # The API resolves patient ownership via Django authenticated session.
        # Pair the native bearer with its OWN HTTP session, never the last login.
        client = self.client_a if token == self.token_a else self.client_b
        return client.post(
            "/api/v1/demo/seed",
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    def test_fresh_authenticated_patient_cannot_receive_demo_logs_or_profile(self):
        response = self._seed(self.token_a)
        self.assertEqual(response.status_code, 403)
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
                self.assertEqual(self._seed(token).status_code, 403)

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
            password="synthetic-password-never-used",
        )
        token = issue_native_token(demo)
        demo_client = Client()
        self._login(demo, demo_client)
        response = demo_client.post(
            "/api/v1/demo/seed", data={}, content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(LogEntry.objects.filter(patient=demo).exists())

    def test_actual_seed_handler_denies_authenticated_request_with_403(self):
        # HTTP auth may reject a credential earlier (401). Once the operation
        # is reached with an authenticated patient, it must explicitly return
        # 403 before any synthetic rows/profile are written.
        with self.assertRaises(HttpError) as error:
            seed_demo_data(SimpleNamespace(user=self.patient_a))
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(LogEntry.objects.filter(patient=self.patient_a).count(), 0)

    def test_authenticated_a_b_a_logs_are_isolated_after_repeated_denied_seeding(self):
        """Native bearer switch A→B→A never returns the other account's readings."""
        entry_a = LogEntry.objects.create(
            patient=self.patient_a, blood_sugar=Decimal("95.0"), source="manual",
        )
        entry_b = LogEntry.objects.create(
            patient=self.patient_b, blood_sugar=Decimal("210.0"), source="manual",
        )
        for patient, client, token, expected_id, foreign_id in (
            (self.patient_a, self.client_a, self.token_a, entry_a.pk, entry_b.pk),
            (self.patient_b, self.client_b, self.token_b, entry_b.pk, entry_a.pk),
            (self.patient_a, self.client_a, self.token_a, entry_a.pk, entry_b.pk),
        ):
            before = client.get(
                "/api/v1/logs",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
            self.assertEqual(before.status_code, 200)
            self.assertEqual(before.json()["total"], 1)
            self.assertEqual([item["id"] for item in before.json()["items"]], [expected_id])
            self.assertNotIn(foreign_id, [item["id"] for item in before.json()["items"]])
            self.assertEqual(self._seed(token).status_code, 403)
            after = client.get(
                "/api/v1/logs",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
            self.assertEqual(after.status_code, 200)
            self.assertEqual(after.json(), before.json())
            self.assertEqual(LogEntry.objects.filter(patient=patient).count(), 1)

    def test_conflicting_cookie_and_bearer_never_fall_back(self):
        """A stale/invalid explicit bearer must not silently read cookie A."""
        entry_a = LogEntry.objects.create(
            patient=self.patient_a, blood_sugar=Decimal("95"), source="manual",
        )
        entry_b = LogEntry.objects.create(
            patient=self.patient_b, blood_sugar=Decimal("210"), source="manual",
        )
        # A has a valid session cookie, but an explicit B bearer is a
        # conflicting authority: deny rather than choosing either patient.
        bearer_b = self.client_a.get(
            "/api/v1/logs", HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
        )
        self.assertEqual(bearer_b.status_code, 401)
        # B with B's own session and bearer still reads only B.
        b_own_session = self.client_b.get(
            "/api/v1/logs", HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
        )
        self.assertEqual(b_own_session.status_code, 200)
        self.assertEqual(
            [item["id"] for item in b_own_session.json()["items"]], [entry_b.pk],
        )
        # An explicitly invalid bearer is never a license to fall back to A.
        invalid_bearer = self.client_a.get(
            "/api/v1/logs", HTTP_AUTHORIZATION="Bearer iamina.invalid",
        )
        self.assertEqual(invalid_bearer.status_code, 401)
        # Cookie-only login stays supported for the Web/PWA session mode.
        cookie_only = self.client_a.get("/api/v1/logs")
        self.assertEqual(cookie_only.status_code, 200)
        self.assertEqual(
            [item["id"] for item in cookie_only.json()["items"]], [entry_a.pk],
        )

    def test_anonymous_seed_request_stays_unauthorized(self):
        # setUp logs in both fixtures through the HTTP route; clear its session.
        response = Client().post(
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
        self.assertEqual(
            self.client.post(
                "/api/v1/demo/seed", data={}, content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {bearer}",
            ).status_code, 403,
        )
        self.assertEqual(LogEntry.objects.filter(patient=user).count(), 0)

    def test_read_only_demo_scenarios_are_still_available(self):
        response = self.client.get("/api/v1/demo/scenarios")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 8)
