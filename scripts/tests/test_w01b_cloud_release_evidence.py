"""W01-B: sanitized cloud inventory must never silently certify production."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from check_w01b_cloud_release_evidence import DEFAULT, evaluate  # noqa: E402


class CloudEvidenceNoGoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def blockers(self, snapshot=None) -> set[str]:
        return set(evaluate(self.inventory if snapshot is None else snapshot))

    def test_actual_read_only_inventory_is_explicit_no_go(self):
        blockers = self.blockers()
        self.assertGreaterEqual(len(blockers), 12)
        self.assertIn("NEON_PRODUCTION_BRANCH_UNPROTECTED", blockers)
        self.assertIn("PREVIEW_PRODUCTION_DB_ISOLATION_UNVERIFIED", blockers)
        self.assertIn("UNPROVEN_W02_HUMAN_APPROVAL", blockers)
        self.assertIn("UNPROVEN_W14_CLINICAL_LEGAL_SECURITY_APPROVAL", blockers)

    def test_raw_database_urls_are_rejected_without_reflecting_values(self):
        snapshot = copy.deepcopy(self.inventory)
        snapshot["vercel"]["backend"]["debug_value"] = (
            "postgresql://private:secret@db.invalid/database"
        )
        self.assertEqual(
            evaluate(snapshot), ["SECRET_MATERIAL_IN_EVIDENCE: sanitized metadata only"]
        )

    def test_frontend_project_swap_fails(self):
        snapshot = copy.deepcopy(self.inventory)
        snapshot["vercel"]["frontend"]["id"] = snapshot["vercel"]["backend"]["id"]
        self.assertIn("FRONTEND_PROJECT_NOT_VERIFIED", self.blockers(snapshot))

    def test_root_directory_unverified_is_not_inferred_from_manifest(self):
        snapshot = copy.deepcopy(self.inventory)
        self.assertIn("FRONTEND_ROOT_DIRECTORY_UNVERIFIED", self.blockers(snapshot))
        self.assertIn("BACKEND_ROOT_DIRECTORY_UNVERIFIED", self.blockers(snapshot))

    def test_frontend_and_backend_commits_must_not_be_claimed_current(self):
        blockers = self.blockers()
        self.assertIn("CURRENT_FRONTEND_DEPLOYMENT_NOT_MAIN_SHA", blockers)
        self.assertIn("CURRENT_BACKEND_DEPLOYMENT_NOT_MAIN_SHA", blockers)

    def test_sql_pg16_probe_does_not_prove_vercel_database_routing(self):
        snapshot = copy.deepcopy(self.inventory)
        self.assertTrue(snapshot["neon"]["synthetic"]["read_only_query_passed"])
        self.assertIn("VERCEL_TO_NEON_ROUTING_UNVERIFIED", self.blockers(snapshot))

    def test_synthetic_project_identity_must_be_distinct(self):
        snapshot = copy.deepcopy(self.inventory)
        snapshot["neon"]["synthetic"]["project_id"] = snapshot["neon"]["production"]["project_id"]
        self.assertIn("SYNTHETIC_NEON_NOT_PROVEN_SEPARATE", self.blockers(snapshot))

    def test_public_network_and_unprotected_branch_are_reported_separately(self):
        snapshot = copy.deepcopy(self.inventory)
        snapshot["neon"]["production"]["branch_protected"] = True
        blockers = self.blockers(snapshot)
        self.assertNotIn("NEON_PRODUCTION_BRANCH_UNPROTECTED", blockers)
        self.assertIn("NEON_PUBLIC_CONNECTION_EXPOSURE_NEEDS_REVIEW", blockers)
        self.assertIn("NEON_PRODUCTION_NETWORK_PROCESSORS_NOT_APPROVED", blockers)

    def test_positive_snapshot_is_still_only_technical_not_release_approval(self):
        snapshot = copy.deepcopy(self.inventory)
        front, back = snapshot["vercel"]["frontend"], snapshot["vercel"]["backend"]
        for project in (front, back):
            project["root_directory_verified"] = True
            project["release_candidate_verified"] = True
            project["production_target_commit"] = snapshot["github_main_sha"]
        back["iamina_env_declared"] = True
        back["preview_db_isolated_verified"] = True
        prod, syn = snapshot["neon"]["production"], snapshot["neon"]["synthetic"]
        prod["branch_protected"] = True
        prod["public_connections_blocked"] = True
        prod["network_and_processors_approved"] = True
        syn["vercel_to_neon_verified"] = True
        snapshot["remaining_proofs"] = {key: True for key in snapshot["remaining_proofs"]}
        self.assertEqual(evaluate(snapshot), [])
        # No release action is present in this module: external human attestation
        # is required even if a future snapshot claims every field True.


if __name__ == "__main__":
    unittest.main()
