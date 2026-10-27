"""Synthetic tests for D2 expired-row physical retention, without scheduler."""
import json
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from core.models import D2InAppNotice


class D2ExpiredNoticePurgeTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username="d2-purge-a")
        self.b = User.objects.create_user(username="d2-purge-b")
        self.now = timezone.now()

    def _notice(self, patient, key, expires_at):
        return D2InAppNotice.objects.create(
            patient=patient,
            signature=f"{key:064x}",
            kind="context",
            expires_at=expires_at,
        )

    def test_dry_run_does_not_delete_and_apply_removes_only_expired_for_a_and_b(self):
        self._notice(self.a, 1, self.now - timedelta(seconds=1))
        self._notice(self.b, 2, self.now - timedelta(days=1))
        self._notice(self.a, 3, self.now + timedelta(days=1))
        output = StringIO()

        with patch(
            "core.management.commands.purge_d2_expired_notices.timezone.now",
            return_value=self.now,
        ):
            call_command("purge_d2_expired_notices", stdout=output)
            self.assertIn("DRY_RUN expired=2", output.getvalue())
            self.assertEqual(D2InAppNotice.objects.count(), 3)

            output = StringIO()
            call_command(
                "purge_d2_expired_notices", apply=True, batch_size=1,
                stdout=output,
            )
            self.assertIn("APPLIED deleted=2 expired_remaining=0", output.getvalue())
            self.assertEqual(
                list(D2InAppNotice.objects.values_list("signature", flat=True)),
                [f"{3:064x}"],
            )

            output = StringIO()
            call_command("purge_d2_expired_notices", apply=True, stdout=output)
            self.assertIn("APPLIED deleted=0", output.getvalue())

    def test_exact_expiry_is_deleted_and_next_second_remains(self):
        self._notice(self.a, 4, self.now)
        self._notice(self.b, 5, self.now + timedelta(seconds=1))
        with patch(
            "core.management.commands.purge_d2_expired_notices.timezone.now",
            return_value=self.now,
        ):
            call_command("purge_d2_expired_notices", apply=True, stdout=StringIO())
        self.assertFalse(D2InAppNotice.objects.filter(signature=f"{4:064x}").exists())
        self.assertTrue(D2InAppNotice.objects.filter(signature=f"{5:064x}").exists())

    def test_invalid_batch_sizes_fail_without_deletion(self):
        self._notice(self.a, 6, self.now - timedelta(days=1))
        for size in (0, -1, 1001):
            with self.assertRaises(CommandError):
                call_command(
                    "purge_d2_expired_notices", apply=True,
                    batch_size=size, stdout=StringIO(),
                )
        self.assertEqual(D2InAppNotice.objects.count(), 1)

    def test_monitor_overdue_fails_closed_without_deleting(self):
        self._notice(self.a, 7, self.now - timedelta(minutes=91))
        self._notice(self.b, 8, self.now - timedelta(minutes=10))
        output = StringIO()
        with patch(
            "core.management.commands.purge_d2_expired_notices.timezone.now",
            return_value=self.now,
        ):
            with self.assertRaisesMessage(CommandError, "D2_RETENTION_OVERDUE"):
                call_command(
                    "purge_d2_expired_notices", max_overdue_minutes=60,
                    stdout=output,
                )
        metrics = json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(metrics["expired_before"], 2)
        self.assertEqual(metrics["overdue_count"], 1)
        self.assertEqual(metrics["deleted"], 0)
        self.assertEqual(D2InAppNotice.objects.count(), 2)

    def test_max_deletes_fails_before_any_mutation(self):
        self._notice(self.a, 9, self.now - timedelta(days=1))
        self._notice(self.b, 10, self.now - timedelta(days=1))
        with self.assertRaisesMessage(CommandError, "D2_RETENTION_LIMIT"):
            call_command(
                "purge_d2_expired_notices", apply=True, max_deletes=1,
                stdout=StringIO(),
            )
        self.assertEqual(D2InAppNotice.objects.count(), 2)

    def test_aggregate_json_omits_account_and_clinical_fields(self):
        self._notice(self.a, 11, self.now - timedelta(days=1))
        output = StringIO()
        call_command("purge_d2_expired_notices", apply=True, stdout=output)
        metrics = json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(metrics["mode"], "APPLIED")
        self.assertEqual(metrics["deleted"], 1)
        self.assertEqual(metrics["expired_remaining"], 0)
        self.assertEqual(metrics["schema_version"], "1.0")
        for forbidden in ("patient", "email", "signature", "blood_sugar"):
            self.assertNotIn(forbidden, output.getvalue())

    def test_invalid_monitor_or_delete_limits_are_non_destructive(self):
        self._notice(self.a, 12, self.now - timedelta(days=1))
        for kwargs in (
            {"max_deletes": 0, "apply": True},
            {"max_deletes": 100001, "apply": True},
            {"max_overdue_minutes": 0},
            {"max_overdue_minutes": 10081},
            {"max_overdue_minutes": 60, "apply": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(CommandError):
                    call_command(
                        "purge_d2_expired_notices", stdout=StringIO(), **kwargs
                    )
        self.assertEqual(D2InAppNotice.objects.count(), 1)
