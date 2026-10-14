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

    def _patch(self, token, payload, expected_updated_at=None):
        # Restore the real, fail-closed HTTP bearer path for this request only.
        # Never bypass token verification or weaken the production handler.
        with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
            return self.client.patch(
                "/api/v1/profile",
                data=json.dumps(payload),
                content_type="application/json",
                headers={
                    "Authorization": f"Bearer {token}",
                    **(
                        {"X-Iamina-Treatment-Expected-Updated-At": expected_updated_at}
                        if expected_updated_at is not None else {}
                    ),
                },
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
            expected_updated_at="none",
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
            expected_updated_at="none",
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

    def test_missing_revision_cannot_create_or_clobber_patient_declaration(self):
        payload = {"treatment_declaration": {
            "version": 1, "state": "declared", "codes": ["insulin"],
        }}

        def headerless_patch():
            # Real Django-Ninja bearer path; only the CAS header is omitted.
            with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
                return self.client.patch(
                    "/api/v1/profile",
                    data=json.dumps(payload),
                    content_type="application/json",
                    headers={"Authorization": f"Bearer {self.token_a}"},
                )

        missing_first = headerless_patch()
        self.assertEqual(missing_first.status_code, 428, missing_first.content)
        before = self._get(self.token_a).json()
        self.assertEqual(before["treatment_declarations"], [])
        self.assertIsNone(before["treatment_declaration_updated_at"])

        accepted = self._patch(self.token_a, payload, expected_updated_at="none")
        self.assertEqual(accepted.status_code, 200, accepted.content)
        current = accepted.json()["treatment_declaration_updated_at"]
        self.assertIsNotNone(current)

        payload["treatment_declaration"]["codes"] = ["oral_meds"]
        missing_again = headerless_patch()
        self.assertEqual(missing_again.status_code, 428, missing_again.content)
        unchanged = self._get(self.token_a).json()
        self.assertEqual(unchanged["treatment_declarations"], ["insulin"])
        self.assertEqual(unchanged["treatment_declaration_updated_at"], current)
        self.assertEqual(self._get(self.token_b).json()["treatment_declarations"], [])

        accepted_with_revision = self._patch(
            self.token_a, payload, expected_updated_at=current,
        )
        self.assertEqual(accepted_with_revision.status_code, 200)
        self.assertEqual(
            self._get(self.token_a).json()["treatment_declarations"],
            ["oral_meds"],
        )

    def test_legacy_profile_patch_without_cas_header_remains_supported(self):
        response = self._patch(self.token_a, {"preferred_language": "fr"})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self._get(self.token_a).json()["preferred_language"], "fr")
        self.assertEqual(self._get(self.token_b).json()["treatment_declarations"], [])

    def test_compare_and_swap_prevents_stale_cross_device_declaration(self):
        first = self._patch(
            self.token_a,
            {"treatment_declaration": {
                "version": 1,
                "state": "declared",
                "codes": ["lifestyle"],
            }},
            expected_updated_at="none",
        )
        self.assertEqual(first.status_code, 200, first.content)
        original = first.json()["treatment_declaration_updated_at"]
        self.assertIsNotNone(original)
        persisted = DiabetesProfile.objects.get(
            base_profile__patient=self.a
        ).treatment_declaration_updated_at
        self.assertEqual(original, persisted.isoformat(timespec="microseconds"))
        self.assertEqual(
            self._get(self.token_a).json()["treatment_declaration_updated_at"],
            original,
        )
        self.assertEqual(self._get(self.token_b).json()["treatment_declarations"], [])

        stale = self._patch(
            self.token_a,
            {"treatment_declaration": {
                "version": 1,
                "state": "declared",
                "codes": ["insulin"],
            }},
            expected_updated_at="none",
        )
        self.assertEqual(stale.status_code, 409, stale.content)
        self.assertEqual(self._get(self.token_a).json()["treatment_declarations"], [
            "lifestyle"
        ])

        second = self._patch(
            self.token_a,
            {"treatment_declaration": {
                "version": 1,
                "state": "declared",
                "codes": ["lifestyle", "oral_meds"],
            }},
            expected_updated_at=original,
        )
        self.assertEqual(second.status_code, 200, second.content)
        current = second.json()["treatment_declaration_updated_at"]
        self.assertNotEqual(original, current)

        replay = self._patch(
            self.token_a,
            {"treatment_declaration": {
                "version": 1,
                "state": "none_declared",
                "codes": [],
            }},
            expected_updated_at=original,
        )
        self.assertEqual(replay.status_code, 409, replay.content)
        self.assertEqual(self._get(self.token_a).json()["treatment_declarations"], [
            "lifestyle", "oral_meds"
        ])
        self.assertEqual(self._get(self.token_b).json()["treatment_declarations"], [])

    def test_malformed_treatment_revision_is_rejected_without_mutation(self):
        for revision in ("invalid-time", "2026-10-13T21:00:00", "0"):
            bad = self._patch(
                self.token_a,
                {"treatment_declaration": {
                    "version": 1,
                    "state": "declared",
                    "codes": ["insulin"],
                }},
                expected_updated_at=revision,
            )
            self.assertEqual(bad.status_code, 422, bad.content)
        unrelated = self._patch(
            self.token_a,
            {"preferred_language": "fr"},
            expected_updated_at="none",
        )
        self.assertEqual(unrelated.status_code, 422, unrelated.content)
        saved = DiabetesProfile.objects.get(base_profile__patient=self.a)
        self.assertIsNone(saved.treatment_declaration_updated_at)
        self.assertEqual(saved.treatment_declarations, [])

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
