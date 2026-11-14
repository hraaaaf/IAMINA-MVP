"""D1 synthetic receipt authority: independent server-side security oracles.

Uses a file-backed SQLite ledger shared across distinct service instances.
No Django migrations, external identity, patient records, endpoints or KMS.
"""
from __future__ import annotations

import copy
import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.d1_receipt_authority_candidate import (
    CandidateFacts,
    ReceiptRejected,
    SyntheticReceiptLedger,
)

OWNER = "amina_vault_v1_native_735"
HASH = "a" * 64
DIFFERENT_HASH = "b" * 64
NOW = 1794646800


class TestD1ReceiptAuthority(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "only-synthetic-d1.sqlite3"
        self.ledger = SyntheticReceiptLedger(self.file)
        self.key = Ed25519PrivateKey.generate()
        self.ledger.register_test_signer("ci-synth-kid-001", self.key)
        self.facts = CandidateFacts(
            django_user_id=735,
            owner=OWNER,
            source_sha256=HASH,
            independently_restored_sha256=HASH,
            consent_record_id="ci-synth-consent-review-only",
            source_possession_evidence_id="ci-synth-possession-review-only",
        )

    def receipt(self, **kwargs):
        return self.ledger.issue_test_only(self.facts, now=NOW, **kwargs)

    def consume(self, value, *, ledger=None, owner=OWNER, digest=HASH, now=NOW + 1):
        return (ledger or self.ledger).verify_and_consume(
            value, expected_owner=owner, live_source_sha256=digest, now=now
        )

    def refused(self, value, reason, **kwargs):
        with self.assertRaisesRegex(ReceiptRejected, reason):
            self.consume(value, **kwargs)

    def test_issue_verify_and_persistently_block_replay_after_restart(self):
        issued = self.receipt()
        fresh_process_simulation = SyntheticReceiptLedger(self.file)
        result = self.consume(issued, ledger=fresh_process_simulation)
        self.assertEqual(result["result"], "READY_FOR_EXTERNAL_SECURITY_REVIEW_ONLY")
        self.assertIs(result["authorizedToMigrate"], False)
        self.assertIs(result["clinicalGo"], False)
        self.refused(issued, "D1_RECEIPT_REPLAY_REJECTED")

    def test_parallel_consumers_only_one_wins_across_sqlite_connections(self):
        issued = self.receipt()
        def claim(_):
            reader = SyntheticReceiptLedger(self.file)
            try:
                return self.consume(issued, ledger=reader)["result"]
            except ReceiptRejected as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(claim, range(8)))
        self.assertEqual(results.count("READY_FOR_EXTERNAL_SECURITY_REVIEW_ONLY"), 1)
        self.assertEqual(results.count("D1_RECEIPT_REPLAY_REJECTED"), 7)
        with sqlite3.connect(self.file) as conn:
            count = conn.execute("SELECT COUNT(*) FROM d1_candidate_consumed").fetchone()[0]
        self.assertEqual(count, 1)

    def test_roll_back_nonce_if_audit_write_fails(self):
        issued = self.receipt()
        with sqlite3.connect(self.file) as conn:
            conn.execute(
                "CREATE TRIGGER d1_audit_fail BEFORE INSERT ON d1_candidate_audit "
                "WHEN NEW.event='SYNTHETIC_RECEIPT_CONSUMED' "
                "BEGIN SELECT RAISE(FAIL, 'synthetic audit unavailable'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.consume(issued)
        with sqlite3.connect(self.file) as conn:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM d1_candidate_consumed").fetchone()[0], 0
            )
            conn.execute("DROP TRIGGER d1_audit_fail")
        self.assertEqual(
            self.consume(issued)["result"],
            "READY_FOR_EXTERNAL_SECURITY_REVIEW_ONLY",
        )

    def test_rotate_keeps_previous_signatures_verifiable(self):
        old = self.receipt()
        self.ledger.register_test_signer("ci-synth-kid-002", Ed25519PrivateKey.generate())
        new = self.receipt()
        self.assertNotEqual(old["payload"]["kid"], new["payload"]["kid"])
        self.assertFalse(self.consume(old)["authorizedToMigrate"])
        self.assertFalse(self.consume(new)["authorizedToMigrate"])
        events = dict(self.ledger.audit_summary())
        self.assertGreaterEqual(events["SYNTHETIC_KEY_ACTIVATED"], 2)

    def test_revoked_key_does_not_verify_old_receipts(self):
        old = self.receipt()
        self.ledger.register_test_signer("ci-synth-kid-002", Ed25519PrivateKey.generate())
        self.ledger.revoke("ci-synth-kid-001")
        self.refused(old, "D1_RECEIPT_SIGNER_NOT_TRUSTED")
        current = self.receipt()
        self.assertEqual(current["payload"]["kid"], "ci-synth-kid-002")

    def test_reuse_revoked_kid_and_colliding_kid_are_denied(self):
        with self.assertRaisesRegex(ReceiptRejected, "D1_KEY_ID_COLLISION"):
            self.ledger.register_test_signer("ci-synth-kid-001", Ed25519PrivateKey.generate())
        self.ledger.revoke("ci-synth-kid-001")
        with self.assertRaisesRegex(ReceiptRejected, "D1_REVOKED_KEY_CANNOT_REACTIVATE"):
            self.ledger.register_test_signer("ci-synth-kid-001", self.key)
        with self.assertRaisesRegex(ReceiptRejected, "D1_NO_ACTIVE_TRUSTED_SIGNER"):
            self.receipt()

    def test_new_instance_cannot_issue_without_private_key_material(self):
        new_instance = SyntheticReceiptLedger(self.file)
        with self.assertRaisesRegex(ReceiptRejected, "D1_SIGNER_NOT_AVAILABLE_IN_SERVER"):
            new_instance.issue_test_only(self.facts, now=NOW)
        self.assertTrue(self.file.exists())

    def test_altered_payload_fails_signature_validation(self):
        changed = copy.deepcopy(self.receipt())
        changed["payload"]["nonce"] = "9" * 32
        self.refused(changed, "D1_RECEIPT_SIGNATURE_REJECTED")
        extra = copy.deepcopy(self.receipt())
        extra["payload"]["debug"] = True
        self.refused(extra, "D1_RECEIPT_PAYLOAD_INVALID")

    def test_wrong_owner_and_live_source_digest_fail_closed(self):
        issued = self.receipt()
        self.refused(issued, "D1_RECEIPT_SCOPE_EXPIRED_OR_UNTRUSTED",
                     owner="amina_vault_v1_native_736")
        self.refused(issued, "D1_RECEIPT_SCOPE_EXPIRED_OR_UNTRUSTED",
                     digest=DIFFERENT_HASH)
        self.assertFalse(self.consume(issued)["authorizedToMigrate"])

    def test_wrong_issuer_without_signing_key_is_denied(self):
        bad = copy.deepcopy(self.receipt())
        bad["payload"]["issuer"] = "some-other-service"
        self.refused(bad, "D1_RECEIPT_SCOPE_EXPIRED_OR_UNTRUSTED")

    def test_expired_and_future_issued_are_denied(self):
        issued = self.receipt()
        self.refused(issued, "D1_RECEIPT_SCOPE_EXPIRED_OR_UNTRUSTED",
                     now=NOW + 121)
        self.refused(issued, "D1_RECEIPT_SCOPE_EXPIRED_OR_UNTRUSTED",
                     now=NOW - 100)

    def test_prohibit_too_long_lived_or_unverified_synthetic_facts(self):
        with self.assertRaisesRegex(ReceiptRejected, "D1_RECEIPT_TTL_INVALID"):
            self.receipt(ttl_seconds=3600)
        bad = CandidateFacts(
            django_user_id=736, owner=OWNER, source_sha256=HASH,
            independently_restored_sha256=HASH,
            consent_record_id="ci-synth-test",
            source_possession_evidence_id="ci-synth-test",
        )
        with self.assertRaisesRegex(ReceiptRejected, "D1_RECEIPT_OWNER_ID_MISMATCH"):
            self.ledger.issue_test_only(bad, now=NOW)
        mismatched_restore = CandidateFacts(
            django_user_id=735, owner=OWNER, source_sha256=HASH,
            independently_restored_sha256=DIFFERENT_HASH,
            consent_record_id="ci-synth-test",
            source_possession_evidence_id="ci-synth-test",
        )
        with self.assertRaisesRegex(ReceiptRejected, "D1_INDEPENDENT_RESTORE_MISMATCH"):
            self.ledger.issue_test_only(mismatched_restore, now=NOW)
        no_real_evidence = CandidateFacts(
            django_user_id=735, owner=OWNER, source_sha256=HASH,
            independently_restored_sha256=HASH,
            consent_record_id="consent-provided-by-untrusted-client",
            source_possession_evidence_id="ci-synth-test",
        )
        with self.assertRaisesRegex(ReceiptRejected, "D1_SYNTHETIC_EVIDENCE_REQUIRED"):
            self.ledger.issue_test_only(no_real_evidence, now=NOW)

    def test_private_keys_and_patient_identifiers_absent_from_audit(self):
        receipt = self.receipt()
        self.consume(receipt)
        events = self.ledger.audit_summary()
        self.assertIn(("SYNTHETIC_RECEIPT_CONSUMED", 1), events)
        with sqlite3.connect(self.file) as conn:
            rows = conn.execute(
                "SELECT event,kid,nonce_hash FROM d1_candidate_audit"
            ).fetchall()
            self.assertTrue(rows)
            self.assertTrue(all(len(r) == 3 for r in rows))
            self.assertEqual(
                conn.execute(
                    "SELECT COUNT(*) FROM pragma_table_info('d1_candidate_audit') "
                    "WHERE name IN ('owner','patient_id','raw_nonce','private_key')"
                ).fetchone()[0],
                0,
            )
        raw_private = self.key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self.assertNotIn(raw_private, self.file.read_bytes())

    def test_cross_instance_same_kid_public_key_collision_denied(self):
        another = SyntheticReceiptLedger(self.file)
        with self.assertRaisesRegex(ReceiptRejected, "D1_KEY_ID_COLLISION"):
            another.register_test_signer(
                "ci-synth-kid-001", Ed25519PrivateKey.generate()
            )


if __name__ == "__main__":
    unittest.main()
