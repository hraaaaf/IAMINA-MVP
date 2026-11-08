"""Safety tests for the operator-only W02 C7 synthetic Neon migration runner.

No Neon connection or credentials. Does NOT execute the live schema migration.
"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import w02_c7_migrate_new_db as m  # noqa: E402

FAKE = (
    "postgresql://iamina925_empty_owner:SYNTHETIC_TEST_ONLY_PASSWORD"
    "@ep-old-art-b9sy0oo4-pooler.c-7.eu-central-1.aws.neon.tech/"
    "iamina_w02_c7_synthetic?channel_binding=require&sslmode=require"
)
EXAMPLE_PLAN = (
    "Planned operations:\n"
    "core.0020_web_refresh_candidate\n"
    "core.0021_web_refresh_transport_nonce\n"
)


class W02C7ScopedMigrationRunnerTests(unittest.TestCase):
    def test_valid_target_is_the_new_db_and_owner_only(self):
        m.validate_target(FAKE)
        m.verify_source()

    def test_old_db_denied_even_with_same_owner(self):
        with self.assertRaises(m.MigrationDenied):
            m.validate_target(FAKE.replace("iamina_w02_c7_synthetic?", "iamina925_empty?"))

    def test_other_user_neon_host_or_plaintext_denied(self):
        for altered in (
            FAKE.replace("iamina925_empty_owner:", "iamina_preview_app:"),
            FAKE.replace("@ep-old-art-", "@ep-fake-art-"),
            FAKE.replace("sslmode=require", "sslmode=disable"),
            FAKE.replace("channel_binding=require", "channel_binding=disable"),
            FAKE.replace("postgresql://", "http://"),
            FAKE + "&connect_timeout=60",
            FAKE + "\nDATABASE_URL=evil",
            "",
        ):
            with self.subTest(target="redacted"):
                with self.assertRaises(m.MigrationDenied):
                    m.validate_target(altered)

    def test_plan_uses_only_read_only_django_and_never_migrates(self):
        with (
            patch.object(m, "snapshot", return_value={"tables": 0, "migrations": False}) as snapshot,
            patch.object(m, "django_command", return_value=EXAMPLE_PLAN) as dj,
            patch.dict(os.environ, {"VERCEL_ENV": "preview"}),
        ):
            result = m.run(FAKE, apply=False, confirmation="")
        self.assertEqual(result["status"], "PLAN_VALIDATED_NO_WRITE")
        self.assertEqual(snapshot.call_count, 1)
        self.assertEqual(dj.call_count, 1)
        self.assertTrue(dj.call_args.kwargs["read_only"])

    def test_apply_requires_both_exact_confirmation_and_approval_env(self):
        with (
            patch.object(m, "snapshot") as snapshot,
            patch.object(m, "django_command") as dj,
            patch.dict(os.environ, {"IAMINA_W02_C7_MIGRATION_APPROVED": "no"}),
        ):
            with self.assertRaises(m.MigrationDenied):
                m.run(FAKE, apply=True, confirmation=m.NEW_DB)
            with self.assertRaises(m.MigrationDenied):
                m.run(FAKE, apply=True, confirmation="iamina925_empty")
            snapshot.assert_not_called()
            dj.assert_not_called()

    def test_does_not_apply_if_django_plan_missing_c7(self):
        with (
            patch.object(m, "snapshot", return_value={"tables": 0}),
            patch.object(m, "django_command", return_value="core.0019_auth_abuse_bucket") as dj,
            patch.dict(os.environ, {"IAMINA_W02_C7_MIGRATION_APPROVED": "yes"}),
        ):
            with self.assertRaises(m.MigrationDenied):
                m.run(FAKE, apply=True, confirmation=m.NEW_DB)
            self.assertEqual(dj.call_count, 1)

    def test_with_authorization_uses_one_mutating_migrate_then_read_only_check(self):
        with (
            patch.object(m, "snapshot", side_effect=[
                {"tables": 0, "migrations": False},
                {"tables": 116, "core": 3, "users": 0, "profiles": 0},
            ]) as snapshot,
            patch.object(m, "django_command", side_effect=[
                EXAMPLE_PLAN, "Operations to perform: OK", "No changes detected",
            ]) as dj,
            patch.dict(os.environ, {"IAMINA_W02_C7_MIGRATION_APPROVED": "yes", "VERCEL_ENV": "preview"}),
        ):
            result = m.run(FAKE, apply=True, confirmation=m.NEW_DB)
        self.assertEqual(result["status"], "MIGRATED_NEW_SYNTHETIC_DB")
        self.assertEqual(snapshot.call_count, 2)
        self.assertEqual(dj.call_count, 3)
        self.assertEqual([x.kwargs["read_only"] for x in dj.call_args_list],
                         [True, False, True])

    def test_production_vercel_env_rejected(self):
        with (
            patch.dict(os.environ, {"VERCEL_ENV": "production"}),
            patch.object(m, "snapshot") as snapshot,
        ):
            with self.assertRaises(m.MigrationDenied):
                m.run(FAKE, apply=False, confirmation="")
            snapshot.assert_not_called()

    def test_missing_dsn_never_prints_credentials(self):
        env = {**os.environ, "DATABASE_URL": FAKE.replace(
            "iamina_w02_c7_synthetic?", "iamina925_empty?"
        )}
        run = subprocess.run(
            [sys.executable, str(ROOT / "scripts/w02_c7_migrate_new_db.py"), "--plan"],
            env=env, capture_output=True, text=True, timeout=6, check=False,
        )
        self.assertEqual(run.returncode, 2)
        self.assertIn("W02_C7_DENIED_OR_INCOMPLETE", run.stdout)
        self.assertNotIn("SYNTHETIC_TEST_ONLY_PASSWORD", run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
