"""D9 regression: remote existing-account profile reads remain owner-bound.

Uses real Django-Ninja HTTP bearer parsing and synthetic native credentials.
A successful GET on a fresh client does NOT certify frontend vault hydration.
"""

from types import SimpleNamespace
from unittest.mock import patch as mock_patch

from django.contrib.auth.models import AnonymousUser, User
from django.test import Client, TestCase
from ninja.security import HttpBearer

from core.models import BasePatientProfile
from core.native_auth import issue_native_token, verify_native_token
from diabetes.api.v1.security import HybridBearerAuth, firebase_auth_backend
from diabetes.models import DiabetesProfile


class D9ExistingAccountRemoteProfileTests(TestCase):
    def setUp(self):
        self.account_a = User.objects.create_user(
            username="d9-owner-a", password="d9-synthetic-a"
        )
        self.account_b = User.objects.create_user(
            username="d9-owner-b", password="d9-synthetic-b"
        )
        for user, language, diabetes, treatment in (
            (self.account_a, "fr", "type2", "oral_meds"),
            (self.account_b, "ar-MA", "type1", "insulin_injections"),
        ):
            base = BasePatientProfile.objects.create(
                patient=user, preferred_language=language
            )
            DiabetesProfile.objects.create(
                base_profile=base,
                diabetes_type=diabetes,
                treatment_type=treatment,
            )
        self.token_a = issue_native_token(self.account_a)
        self.token_b = issue_native_token(self.account_b)
        self.assertEqual(verify_native_token(self.token_a).pk, self.account_a.pk)
        self.assertEqual(verify_native_token(self.token_b).pk, self.account_b.pk)
        native_adapter = firebase_auth_backend.authenticate(
            SimpleNamespace(user=AnonymousUser()), self.token_a
        )
        self.assertEqual(native_adapter.pk, self.account_a.pk)

    def _get(self, client, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        # conftest.py supplies a session-auth shim; restore the real bearer
        # parser so this cannot pass merely via Django force_login().
        with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
            return client.get("/api/v1/profile", headers=headers)

    def test_a_b_a_separate_clients_only_read_own_remote_profile(self):
        device_a = Client()
        device_b = Client()
        original_a = self._get(device_a, self.token_a)
        self.assertEqual(original_a.status_code, 200, original_a.content)
        self.assertEqual(original_a.json()["diabetes_type"], "type2")
        self.assertEqual(original_a.json()["treatment_type"], "oral_meds")
        self.assertEqual(original_a.json()["preferred_language"], "fr")

        b_response = self._get(device_b, self.token_b)
        self.assertEqual(b_response.status_code, 200, b_response.content)
        self.assertEqual(b_response.json()["diabetes_type"], "type1")
        self.assertEqual(b_response.json()["treatment_type"], "insulin_injections")
        self.assertEqual(b_response.json()["preferred_language"], "ar-MA")

        return_to_a = self._get(device_b, self.token_a)
        self.assertEqual(return_to_a.status_code, 200, return_to_a.content)
        self.assertEqual(return_to_a.json()["diabetes_type"], "type2")
        self.assertEqual(return_to_a.json()["treatment_type"], "oral_meds")
        self.assertEqual(return_to_a.json()["preferred_language"], "fr")

    def test_fresh_http_client_with_existing_bearer_reads_existing_owner(self):
        first_device = self._get(Client(), self.token_a)
        fresh_device = self._get(Client(), self.token_a)
        self.assertEqual(first_device.status_code, 200, first_device.content)
        self.assertEqual(fresh_device.status_code, 200, fresh_device.content)
        self.assertEqual(fresh_device.json(), first_device.json())
        self.assertTrue(fresh_device.json()["clinical_profile_complete"])

    def test_no_bearer_and_invalid_bearer_never_return_patient_profile(self):
        for credential in (None, "iamina.invalid-native-token"):
            response = self._get(Client(), credential)
            self.assertIn(response.status_code, (401, 403))
            self.assertNotIn(b"oral_meds", response.content)
            self.assertNotIn(b"insulin_injections", response.content)

    def test_no_patient_profile_does_not_borrow_another_users_data(self):
        empty_owner = User.objects.create_user(
            username="d9-no-profile", password="d9-no-profile-test"
        )
        response = self._get(Client(), issue_native_token(empty_owner))
        self.assertEqual(response.status_code, 404, response.content)
        self.assertNotIn(b"oral_meds", response.content)

    def test_optional_clinical_fields_remain_unanswered_on_remote_read(self):
        unknown = User.objects.create_user(
            username="d9-unknown-clinical-fields", password="d9-unknown-test"
        )
        base = BasePatientProfile.objects.create(
            patient=unknown, preferred_language="fr"
        )
        DiabetesProfile.objects.create(base_profile=base)
        response = self._get(Client(), issue_native_token(unknown))
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertIsNone(body["diabetes_type"])
        self.assertIsNone(body["treatment_type"])
        self.assertFalse(body["clinical_profile_complete"])
