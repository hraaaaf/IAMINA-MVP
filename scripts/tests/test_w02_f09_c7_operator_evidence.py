"""W02 C7 operator evidence must not grant migration/clinical authorization."""
import unittest

from scripts.check_w02_f09_c7_operator_evidence import (
    validate, DB, OWNER, SHA, TABLES,
)


def sample(stage="before"):
    return {
        "database": DB, "role": OWNER, "source_sha": SHA,
        "public_tables": 0 if stage == "before" else 90,
        "core_migrations": [] if stage == "before" else [
            "0018_versioned_ai_consent_evidence",
            "0019_auth_abuse_bucket",
            "0020_web_refresh_candidate",
            "0021_web_refresh_transport_nonce",
        ],
        "c7_tables": [] if stage == "before" else sorted(TABLES),
        "user_count": 0, "profile_count": 0,
    }


class W02C7OperatorEvidenceTests(unittest.TestCase):
    def test_before_empty(self):
        x = validate(sample(), "before")
        self.assertEqual(x["status"], "EVIDENCE_VALIDATED_NOT_AUTHORIZATION")
        self.assertFalse(x["clinical_activation_approved"])

    def test_after_valid_source(self):
        x = validate(sample("after"), "after")
        self.assertEqual(x["status"], "EVIDENCE_VALIDATED_NOT_AUTHORIZATION")
        self.assertTrue(x["no_sql_executed_by_gate"])

    def test_wrong_database_denied(self):
        x = sample()
        x["database"] = "iamina925_empty"
        self.assertEqual(validate(x, "before")["status"], "BLOCKED")

    def test_runtime_role_denied_for_migration(self):
        x = sample()
        x["role"] = "iamina_w02_c7_preview_app"
        self.assertEqual(validate(x, "before")["status"], "BLOCKED")

    def test_wrong_sha_denied(self):
        x = sample()
        x["source_sha"] = "not-a-reviewed-sha"
        self.assertEqual(validate(x, "before")["status"], "BLOCKED")

    def test_old_tables_denied(self):
        x = sample()
        x["public_tables"] = 46
        self.assertEqual(validate(x, "before")["status"], "BLOCKED")

    def test_profiles_denied(self):
        x = sample()
        x["profile_count"] = 1
        self.assertEqual(validate(x, "before")["status"], "BLOCKED")

    def test_foreign_migration_denied(self):
        x = sample("after")
        x["core_migrations"].append("0020_erasure_attempt")
        self.assertEqual(validate(x, "after")["status"], "BLOCKED")

    def test_missing_nonce_table_denied(self):
        x = sample("after")
        x["c7_tables"].remove("core_webrefreshtransportnonce")
        self.assertEqual(validate(x, "after")["status"], "BLOCKED")

    def test_missing_migration_denied(self):
        x = sample("after")
        x["core_migrations"].remove("0021_web_refresh_transport_nonce")
        self.assertEqual(validate(x, "after")["status"], "BLOCKED")

    def test_bad_schema_denied(self):
        for evidence in [None, [], {}, {"database": DB}]:
            self.assertEqual(validate(evidence, "before")["status"], "BLOCKED")

    def test_forged_boolean_counts_denied(self):
        x = sample()
        x["public_tables"] = False
        self.assertEqual(validate(x, "before")["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
