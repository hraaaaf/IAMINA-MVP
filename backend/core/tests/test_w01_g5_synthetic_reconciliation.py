"""Deny-by-default synthetic W01 G5 reconciliation command tests."""
from datetime import datetime, timezone as dt_timezone
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from core.models import BasePatientProfile
from core.models.erasure_attempt import ErasureAttempt
from core.management.commands.reconcile_w01_g5_synthetic import (
    _CONFIRMATION, _EXPECTED_IDENTITY,
)

class SyntheticW01ReconciliationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        for pk, label in ((5, "A"), (6, "B")):
            email = f"w01g5-bff-{'a' if pk == 5 else 'b'}" + "0" * 19 + "@example.invalid"
            user = User.objects.create_user(
                id=pk, username=email, email=email,
                first_name="Synthetic", last_name=f"W01-{label}",
                password="unimportant-synthetic-test",
            )
            user.date_joined = datetime(2026, 10, 27, 17, 4, 10, tzinfo=dt_timezone.utc)
            user.save(update_fields=["date_joined"])
            BasePatientProfile.objects.create(patient=user)

    def _call(self, **kwargs):
        with patch(
            "core.management.commands.reconcile_w01_g5_synthetic._verify_identity"
        ) as identity:
            output = StringIO()
            call_command("reconcile_w01_g5_synthetic", stdout=output, **kwargs)
        identity.assert_called_once()
        return output.getvalue()

    def test_dry_run_never_erases_and_requires_exact_two_accounts(self):
        text = self._call()
        self.assertIn("DRY_RUN identity=verified targets=2", text)
        self.assertEqual(get_user_model().objects.count(), 2)
        get_user_model().objects.create_user(username="other@sample.invalid")
        with self.assertRaises(CommandError):
            self._call(apply=True, confirm=_CONFIRMATION)
        self.assertEqual(get_user_model().objects.count(), 3)

    def test_apply_requires_confirmation_and_exact_identity(self):
        with self.assertRaises(CommandError):
            self._call(apply=True)
        with patch(
            "core.management.commands.reconcile_w01_g5_synthetic.connection.cursor"
        ) as cursor:
            cursor.return_value.__enter__.return_value.fetchone.return_value = (
                "production", *_EXPECTED_IDENTITY[1:]
            )
            with self.assertRaises(CommandError):
                call_command("reconcile_w01_g5_synthetic", stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 2)

    def test_rejects_changed_synthetic_record_before_any_effect(self):
        user = get_user_model().objects.get(pk=5)
        user.last_name = "not-synthetic"
        user.save(update_fields=["last_name"])
        with patch("core.management.commands.reconcile_w01_g5_synthetic._erase_account_data") as erase:
            with self.assertRaises(CommandError):
                self._call(apply=True, confirm=_CONFIRMATION)
        erase.assert_not_called()

    def test_apply_calls_existing_service_and_checks_completed_claims(self):
        def synthetic_application_erase(user, request=None):
            ErasureAttempt.objects.create(
                patient_id_snapshot=user.pk,
                state=ErasureAttempt.State.COMPLETED,
                firebase_uid_snapshot="",
            )
            from core.models.erasure_record import ErasureRecord
            from django.utils import timezone
            ErasureRecord.objects.create(
                patient_id_snapshot=user.pk, firebase_uid_snapshot="",
                completed_at=timezone.now(),
            )
            user.delete()

        with patch(
            "core.management.commands.reconcile_w01_g5_synthetic._erase_account_data",
            side_effect=synthetic_application_erase,
        ) as erase:
            text = self._call(apply=True, confirm=_CONFIRMATION)
        self.assertEqual(erase.call_count, 2)
        self.assertIn("APPLIED app_erased=2 auth_user=0 profiles=0", text)
        self.assertEqual(get_user_model().objects.count(), 0)
