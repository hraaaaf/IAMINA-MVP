"""D7 realistic bearer-auth profile API isolation (synthetic identities)."""

import json
from types import SimpleNamespace
from unittest.mock import patch as mock_patch

from django.contrib.auth.models import AnonymousUser, User
from django.test import Client, TestCase
from ninja.security import HttpBearer

from core.models import BasePatientProfile
from core.native_auth import issue_native_token, verify_native_token
from diabetes.api.v1.security import HybridBearerAuth, firebase_auth_backend
from diabetes.models import DiabetesProfile


class PatientDeclaredTreatmentHttpIsolationTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(
            username="d7-api-synthetic-a", password="test-only-pass-a"
        )
        self.b = User.objects.create_user(
            username="d7-api-synthetic-b", password="test-only-pass-b"
        )
        for user in (self.a, self.b):
            base = BasePatientProfile.objects.create(patient=user)
            DiabetesProfile.objects.create(base_profile=base)

        self.client = Client()
        self.token_a = issue_native_token(self.a)
        self.token_b = issue_native_token(self.b)
        self.assertEqual(verify_native_token(self.token_a).pk, self.a.pk)
        self.assertEqual(verify_native_token(self.token_b).pk, self.b.pk)
        # Distinguish token issuance from the downstream HTTP auth adapter.
        direct = firebase_auth_backend.authenticate(
            SimpleNamespace(user=AnonymousUser()), self.token_a
        )
        self.assertIsNotNone(direct, "The native bearer adapter rejected a valid token")
        self.assertEqual(direct.pk, self.a.pk)

    def _get(self, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        # backend/conftest.py patches HybridBearerAuth.__call__ globally to
        # accept force_login session tests and otherwise return None. These
        # native bearer E2E cases MUST exercise Django-Ninja's real parsing.
        with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
            return self.client.get("/api/v1/profile", headers=headers)

    def _patch(self, token, payload):
        # Restore the real, fail-closed HTTP bearer path for this request only.
        # Never bypass token verification or weaken the production handler.
        with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
            return self.client.patch(
                "/api/v1/profile",
                data=json.dumps(payload),
                content_type="application/json",
                headers={"Authorization": f"Bearer {token}"},
            )

    def test_a_and_b_roundtrip_only_their_own_declarations(self):
        patch_a = self._patch(
            self.token_a,
            {
                "treatment_declaration": {
                    "version": 1,
                    "state": "declared",
                    "codes": ["insulin", "oral_meds", "lifestyle"],
                }
            },
        )
        self.assertEqual(patch_a.status_code, 200, patch_a.content)
        self.assertEqual(
            self._get(self.token_a).json()["treatment_declarations"],
            ["insulin", "oral_meds", "lifestyle"],
        )
        b_before = self._get(self.token_b)
        self.assertEqual(b_before.status_code, 200, b_before.content)
        self.assertEqual(b_before.json()["treatment_declarations"], [])
        self.assertEqual(
            b_before.json()["treatment_declaration_state"],
            "not_answered",
        )

        patch_b = self._patch(
            self.token_b,
            {
                "treatment_declaration": {
                    "version": 1,
                    "state": "unsure",
                    "codes": [],
                }
            },
        )
        self.assertEqual(patch_b.status_code, 200, patch_b.content)
        self.assertEqual(
            self._get(self.token_b).json()["treatment_declaration_state"],
            "unsure",
        )
        self.assertEqual(
            self._get(self.token_a).json()["treatment_declarations"],
            ["insulin", "oral_meds", "lifestyle"],
        )

    def test_invalid_declaration_rejected_without_any_data_change(self):
        bad = self._patch(
            self.token_a,
            {
                "treatment_declaration": {
                    "version": 1,
                    "state": "declared",
                    "codes": ["insulin", "insulin"],
                }
            },
        )
        self.assertEqual(bad.status_code, 422, bad.content)
        profile = DiabetesProfile.objects.get(base_profile__patient=self.a)
        self.assertEqual(profile.treatment_declarations, [])
        self.assertIsNone(profile.treatment_declaration_source)

    def test_forged_native_bearer_is_denied_before_patient_lookup(self):
        forged = self.token_a + "-tampered"
        self.assertIn(self._get(forged).status_code, (401, 403))
        rejected = self._patch(
            forged,
            {"treatment_declaration": {
                "version": 1,
                "state": "declared",
                "codes": ["insulin"],
            }},
        )
        self.assertIn(rejected.status_code, (401, 403))
        for user in (self.a, self.b):
            profile = DiabetesProfile.objects.get(base_profile__patient=user)
            self.assertEqual(profile.treatment_declarations, [])
            self.assertIsNone(profile.treatment_declaration_source)

    def test_missing_auth_does_not_expose_either_profile(self):
        response = self._get()
        self.assertIn(response.status_code, (401, 403))
        self.assertNotIn("treatment_declarations", response.content.decode())
