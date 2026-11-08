"""W02-F09-C7 read-only migration lineage gate tests (no database)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from check_w02_f09_c7_migration_lineage import check_migration_lineage  # noqa: E402

BASE = {
    "0019_auth_abuse_bucket",
    "0020_web_refresh_candidate",
    "0021_web_refresh_transport_nonce",
}
REAL_SYNTHETIC_BRANCH_APPLIED_SAMPLE = [
    "0019_auth_abuse_bucket",
    "0020_erasure_attempt",
    "0021_erasure_attempt_claim_states",
    "0022_d2_preview_consent_receipt",
    "0023_d2_in_app_notice",
]


class W02C7MigrationLineageGateTest(unittest.TestCase):
    def test_exact_source_migration_names_need_a_separate_authorization(self):
        report = check_migration_lineage(BASE, ["0019_auth_abuse_bucket"])
        self.assertEqual(report["result"], "LINEAGE_COMPATIBLE_NOT_AUTHORIZED")
        self.assertFalse(report["db_writes_performed"])
        self.assertFalse(report["hosted_c7_activation_authorized"])

    def test_actual_synthetic_neon_applied_migration_labels_force_stop(self):
        report = check_migration_lineage(BASE, REAL_SYNTHETIC_BRANCH_APPLIED_SAMPLE)
        self.assertEqual(report["result"], "BLOCKED")
        self.assertEqual(report["number_collisions"], [
            "0020_erasure_attempt", "0021_erasure_attempt_claim_states",
        ])
        self.assertEqual(report["unrepresented_applied"], [
            "0020_erasure_attempt",
            "0021_erasure_attempt_claim_states",
            "0022_d2_preview_consent_receipt",
            "0023_d2_in_app_notice",
        ])

    def test_no_0019_applied_fails_closed(self):
        self.assertEqual(
            check_migration_lineage(BASE, [])["result"], "BLOCKED",
        )

    def test_unknown_applied_no_number_conflict_still_fails_closed(self):
        report = check_migration_lineage(
            BASE, ["0019_auth_abuse_bucket", "0028_unrelated_feature"],
        )
        self.assertEqual(report["result"], "BLOCKED")
        self.assertEqual(report["number_collisions"], [])
        self.assertEqual(report["unrepresented_applied"], ["0028_unrelated_feature"])

    def test_missing_source_c7_fails_closed(self):
        report = check_migration_lineage(
            {"0019_auth_abuse_bucket"}, ["0019_auth_abuse_bucket"],
        )
        self.assertEqual(report["result"], "BLOCKED")
        self.assertEqual(report["missing_c7_source"], [
            "0020_web_refresh_candidate", "0021_web_refresh_transport_nonce",
        ])

    def test_duplicate_applied_migration_rejected(self):
        with self.assertRaises(ValueError):
            check_migration_lineage(
                BASE, ["0019_auth_abuse_bucket", "0019_auth_abuse_bucket"],
            )

    def test_invalid_name_or_type_rejected(self):
        for bad in ([None], ["../sneaky"], ["0020_"], [234], ["\n"]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    check_migration_lineage(BASE, bad)

    def test_cli_blocks_conflicting_synthetic_history_without_db_access(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in BASE:
                (Path(directory) / (name + ".py")).write_text(
                    "# generated test-only", encoding="utf-8",
                )
            run = subprocess.run([
                sys.executable, str(ROOT / "scripts/check_w02_f09_c7_migration_lineage.py"),
                "--source-dir", directory,
                "--applied-json", json.dumps(REAL_SYNTHETIC_BRANCH_APPLIED_SAMPLE),
            ], text=True, capture_output=True, timeout=7, check=False)
            self.assertEqual(run.returncode, 3, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result["result"], "BLOCKED")
            self.assertEqual(result["db_writes_performed"], False)

    def test_cli_requires_inventory_never_assumes_empty_database(self):
        run = subprocess.run([
            sys.executable, str(ROOT / "scripts/check_w02_f09_c7_migration_lineage.py"),
        ], text=True, capture_output=True, timeout=7, check=False)
        self.assertNotEqual(run.returncode, 0)


if __name__ == "__main__":
    unittest.main()
