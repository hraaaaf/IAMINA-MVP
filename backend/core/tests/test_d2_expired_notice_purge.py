"""Synthetic tests for D2 expired-row physical retention, without scheduler."""
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
