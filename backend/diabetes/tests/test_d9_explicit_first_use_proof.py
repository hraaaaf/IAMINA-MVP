"""D9 first-use proof remains an explicit owner-bound event.

These tests exercise the real Django-Ninja HTTP bearer parser, not conftest's
force_login compatibility shim. No patient data or medical diagnosis is sent
when recording first-use completion.
"""
import json
from unittest.mock import patch as mock_patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from ninja.security import HttpBearer

from core.models import BasePatientProfile
from core.native_auth import issue_native_token, revoke_native_tokens
from diabetes.api.v1.security import HybridBearerAuth
from diabetes.models import DiabetesProfile


class D9ExplicitFirstUseProofTests(TestCase):
    url = "/api/v1/profile/first-use"

    def setUp(self):
        self.a = User.objects.create_user(
            username="d9-completion-a", password="synthetic-credential-a"
        )
        self.b = User.objects.create_user(
            username="d9-completion-b", password="synthetic-credential-b"
        )
        self.a_profile = BasePatientProfile.objects.create(patient=self.a)
        self.b_profile = BasePatientProfile.objects.create(patient=self.b)
        # A pre-provisioned empty clinical shell MUST NOT imply onboarding.
        DiabetesProfile.objects.create(base_profile=self.a_profile)
        DiabetesProfile.objects.create(base_profile=self.b_profile)
        self.token_a = issue_native_token(self.a)
        self.token_b = issue_native_token(self.b)

    def _request(self, method, token=None, payload=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        client = Client()
        with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
            if method == "GET":
                return client.get(self.url, headers=headers)
            return client.post(
                self.url,
                data=json.dumps(payload if payload is not None else {
                    "version": 1, "confirmed": True,
                }),
                content_type="application/json",
                headers=headers,
            )

    def test_login_and_empty_clinical_shell_never_mark_first_use(self):
        result = self._request("GET", self.token_a)
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json(), {
            "version": 1, "completed": False, "completed_at": None,
        })
        self.a_profile.refresh_from_db()
        self.assertIsNone(self.a_profile.first_use_completed_at)
        self.assertIsNone(self.a_profile.ai_consent_given_at)

    def test_explicit_completion_is_persistent_and_idempotent(self):
        recorded = self._request("POST", self.token_a)
        self.assertEqual(recorded.status_code, 200, recorded.content)
        proof = recorded.json()
        self.assertEqual(proof["version"], 1)
        self.assertIs(proof["completed"], True)
        self.assertIsNotNone(proof["completed_at"])

        repeated = self._request("POST", self.token_a)
        self.assertEqual(repeated.status_code, 200, repeated.content)
        self.assertEqual(repeated.json(), proof)
        self.assertEqual(self._request("GET", self.token_a).json(), proof)
        self.a_profile.refresh_from_db()
        self.assertIsNone(self.a_profile.ai_consent_given_at)
        self.assertIsNone(self.a_profile.diabetes_profile.diabetes_type)
        self.assertIsNone(self.a_profile.diabetes_profile.treatment_type)

    def test_a_b_a_cannot_borrow_completion_or_consent(self):
        self.assertEqual(self._request("POST", self.token_a).status_code, 200)
        self.assertTrue(self._request("GET", self.token_a).json()["completed"])
        self.assertFalse(self._request("GET", self.token_b).json()["completed"])
        self.assertEqual(self._request("POST", self.token_b).status_code, 200)
        self.assertTrue(self._request("GET", self.token_b).json()["completed"])
        self.assertTrue(self._request("GET", self.token_a).json()["completed"])
        self.a_profile.refresh_from_db()
        self.b_profile.refresh_from_db()
        self.assertIsNone(self.a_profile.ai_consent_given_at)
        self.assertIsNone(self.b_profile.ai_consent_given_at)

    def test_fresh_http_client_reads_only_server_confirmed_completion(self):
        first_device = self._request("GET", self.token_a)
        self.assertFalse(first_device.json()["completed"])
        self.assertEqual(self._request("POST", self.token_a).status_code, 200)
        # Another freshly constructed Client has no session cookie or local
        # database; only the verified bearer selects the server-side owner.
        new_device = self._request("GET", self.token_a)
        self.assertTrue(new_device.json()["completed"])
        self.assertFalse(self._request("GET", self.token_b).json()["completed"])

    def test_absent_or_invalid_bearer_never_exposes_or_writes_completion(self):
        for token in (None, "iamina.invalid"):
            for method in ("GET", "POST"):
                response = self._request(method, token)
                self.assertIn(response.status_code, (401, 403), response.content)
                self.assertNotIn(b"completed_at", response.content)
        self.a_profile.refresh_from_db()
        self.assertIsNone(self.a_profile.first_use_completed_at)

    def test_revoked_bearer_fails_closed_on_read_and_write(self):
        revoke_native_tokens(self.a)
        for method in ("GET", "POST"):
            response = self._request(method, self.token_a)
            self.assertIn(response.status_code, (401, 403), response.content)
        self.a_profile.refresh_from_db()
        self.assertIsNone(self.a_profile.first_use_completed_at)

    def test_malformed_or_missing_explicit_confirmation_cannot_mark_complete(self):
        for payload in (
            {},
            {"version": 2, "confirmed": True},
            {"version": 1, "confirmed": False},
            {"version": 1},
            {"confirmed": True},
            {"version": 1, "confirmed": "false"},
            {"version": 1, "confirmed": True, "patient_id": self.b.pk},
            {"version": 1, "confirmed": True, "diabetes_type": "type2"},
        ):
            response = self._request("POST", self.token_a, payload)
            self.assertEqual(response.status_code, 422, response.content)
        self.a_profile.refresh_from_db()
        self.assertIsNone(self.a_profile.first_use_completed_at)

    def test_first_use_proof_does_not_infer_clinical_completeness(self):
        self.assertEqual(self._request("POST", self.token_a).status_code, 200)
        with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
            response = Client().get(
                "/api/v1/profile",
                headers={"Authorization": f"Bearer {self.token_a}"},
            )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(response.json()["clinical_profile_complete"])
        self.assertIsNone(response.json()["diabetes_type"])
        self.assertIsNone(response.json()["treatment_type"])
