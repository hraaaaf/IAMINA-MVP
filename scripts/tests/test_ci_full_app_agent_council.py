"""Structural and negative-path tests for the agent council evidence discoverer."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "ci_full_app_agent_council.py"
spec = importlib.util.spec_from_file_location("council", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestCouncilEvidence(unittest.TestCase):
    def test_has_fifteen_unique_domains(self):
        self.assertEqual(len(module.ROLES), 15)
        self.assertEqual(set(module.ROLES), {f"ia{i:02d}-" + next(x.split("-", 1)[1] for x in module.ROLES if x.startswith(f"ia{i:02d}-")) for i in range(1, 16)})

    def test_profiles_are_valid_and_mapping_is_evidence_only(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            for role in module.ROLES:
                result = module.audit_one(role, out)
                self.assertTrue(result["profile_valid"], role)
                self.assertIsNone(result["agent_session_id"])
                self.assertEqual(result["outcome"], "EVIDENCE_DISCOVERY_ONLY_NOT_CERTIFIED")
                self.assertEqual(len(result["observations"]), 2)
                self.assertTrue((out / f"{role}.json").is_file())

    def test_no_fake_pass_for_missing_or_unsupported_content(self):
        p = module.probe("missing", "path/that/does/not/exist.txt", "PASS")
        self.assertEqual(p["status"], "NOT_FOUND")
        found = module.probe("repo contract", "AGENTS.md", "this-does-not-occur-12345")
        self.assertEqual(found["status"], "NOT_OBSERVED_REVIEW_REQUIRED")

if __name__ == "__main__":
    unittest.main()
