"""One-shot synthetic W01 cleanup: full preflight, 2-click challenge and atomic erase."""
from __future__ import annotations

import os
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from ninja.errors import HttpError

from core.models import BasePatientProfile
from core.models.erasure_record import ErasureRecord
from diabetes.api.v1.w01_synthetic_cleanup import (
    SyntheticCleanupConfirm,
    synthetic_cleanup_execute,
    synthetic_cleanup_preflight,
)

HOST = "iamina-certified-example123-achraf-benmoussa-s-projects.vercel.app"
ENV = {
    "VERCEL": "1", "VERCEL_ENV": "preview", "IAMINA_ENV": "development",
    "VERCEL_PROJECT_ID": "prj_Pn9FnyconF3h2w9gOU74iV98kJoU",
    "VERCEL_URL": HOST,
    "IAMINA_EXPECTED_DB_HOST": "ep-old-art-b9sy0oo4.c-7.eu-central-1.aws.neon.tech",
    "IAMINA_EXPECTED_DB_NAME": "iamina925_empty",
    "IAMINA_EXPECTED_DB_ROLE": "iamina_preview_app",
    "IAMINA_W01_G5_CLEANUP_ENABLED": "true",
}
IDENTITY = {"database_name": "iamina925_empty", "role_name": "iamina_preview_app",
            "neon_project_id": "noisy-truth-00115950", "neon_branch_id": "br-sweet-frog-b9ok6ptp"}


class OneShotW01SyntheticCleanupTest(TestCase):
    def setUp(self):
        for i, label in ((3, "A"), (4, "B")):
            email = f"w01g5-bff-{i:020x}@example.invalid"
            user = User.objects.create_user(
                pk=i, email=email, username=email,
                password="test-only", first_name="Synthetic", last_name=f"W01-{label}",
            )
            BasePatientProfile.objects.create(patient=user)
        self.factory = RequestFactory()

    def _get(self):
        return self.factory.get("/api/v1/ops/w01-g5-synthetic-cleanup", HTTP_HOST=HOST)

    def _post(self):
        return self.factory.post("/api/v1/ops/w01-g5-synthetic-cleanup", HTTP_HOST=HOST)

    def test_disabled_by_default_and_wrong_scope_always_404(self):
        with patch.dict(os.environ, {k:v for k,v in ENV.items()
                                     if k!="IAMINA_W01_G5_CLEANUP_ENABLED"}, clear=True):
            with self.assertRaises(HttpError) as e:
                synthetic_cleanup_preflight(self._get())
            self.assertEqual(e.exception.status_code,404)
        with patch.dict(os.environ, {**ENV,"VERCEL_ENV":"production"}, clear=True):
            with self.assertRaises(HttpError) as e:
                synthetic_cleanup_preflight(self._get())
            self.assertEqual(e.exception.status_code,404)

    def test_fresh_challenge_then_atomically_deletes_exact_two(self):
        with patch.dict(os.environ,ENV,clear=True), patch(
            "diabetes.api.v1.w01_synthetic_cleanup.read_synthetic_identity",
            return_value=IDENTITY,
        ), patch("diabetes.api.v1.w01_synthetic_cleanup.run_account_delete_hooks") as hooks:
            pre=synthetic_cleanup_preflight(self._get())
            self.assertEqual(pre["eligible_accounts"],2)
            result=synthetic_cleanup_execute(self._post(),SyntheticCleanupConfirm(
                confirm="DELETE TWO W01 SYNTHETIC ACCOUNTS",challenge=pre["challenge"]
            ))
        self.assertEqual(result,{"deleted_accounts":2,"remaining_accounts":0})
        self.assertEqual(User.objects.count(),0)
        self.assertEqual(ErasureRecord.objects.count(),2)
        self.assertEqual(hooks.call_count,2)

    def test_bad_confirmation_or_challenge_does_not_delete(self):
        with patch.dict(os.environ,ENV,clear=True), patch(
            "diabetes.api.v1.w01_synthetic_cleanup.read_synthetic_identity",
            return_value=IDENTITY,
        ):
            pre=synthetic_cleanup_preflight(self._get())
            for confirm,challenge in [
                ("WRONG",pre["challenge"]),
                ("DELETE TWO W01 SYNTHETIC ACCOUNTS","forged"),
            ]:
                with self.assertRaises(HttpError):
                    synthetic_cleanup_execute(self._post(),SyntheticCleanupConfirm(
                        confirm=confirm,challenge=challenge
                    ))
                self.assertEqual(User.objects.count(),2)

    def test_wrong_database_never_creates_cleanup_challenge(self):
        with patch.dict(os.environ,ENV,clear=True), patch(
            "diabetes.api.v1.w01_synthetic_cleanup.read_synthetic_identity",
            return_value=None,
        ):
            with self.assertRaises(HttpError) as e:
                synthetic_cleanup_preflight(self._get())
            self.assertEqual(e.exception.status_code,503)

    def test_non_synthetic_user_instead_of_target_blocks_entire_batch(self):
        User.objects.filter(pk=4).update(email="real@example.com")
        with patch.dict(os.environ,ENV,clear=True), patch(
            "diabetes.api.v1.w01_synthetic_cleanup.read_synthetic_identity",
            return_value=IDENTITY,
        ):
            with self.assertRaises(HttpError) as e:
                synthetic_cleanup_preflight(self._get())
            self.assertEqual(e.exception.status_code,409)
        self.assertEqual(User.objects.count(),2)

    def test_hook_failure_rolls_back_every_deletion(self):
        with patch.dict(os.environ,ENV,clear=True), patch(
            "diabetes.api.v1.w01_synthetic_cleanup.read_synthetic_identity",
            return_value=IDENTITY,
        ), patch(
            "diabetes.api.v1.w01_synthetic_cleanup.run_account_delete_hooks",
            side_effect=[None, RuntimeError("hook failed")],
        ):
            pre=synthetic_cleanup_preflight(self._get())
            with self.assertRaises(RuntimeError):
                synthetic_cleanup_execute(self._post(),SyntheticCleanupConfirm(
                    confirm="DELETE TWO W01 SYNTHETIC ACCOUNTS",challenge=pre["challenge"]
                ))
        self.assertEqual(User.objects.count(),2)
        self.assertEqual(ErasureRecord.objects.count(),0)
