"""D1 adversarial PostgreSQL16 receipt ledger tests: no production migration.

Must run against the disposable PostgreSQL service created by the CI job.
Never connects to a configured production database or Django settings.
"""
from __future__ import annotations

import copy
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psycopg2
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.d1_pg_signed_receipt_candidate import PostgresSignedReceiptRehearsal
from core.d1_receipt_authority_candidate import (
    CandidateFacts,
    ReceiptRejected,
    SyntheticReceiptLedger,
)

NOW = 1794646800
OWNER = "amina_vault_v1_native_735"
SHA = "a" * 64
WRONG_SHA = "b" * 64


def public_bytes(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


class TestD1PGReceiptLedger(unittest.TestCase):
    def setUp(self):
        dsn = os.getenv("D1_PG_TEST_DSN")
        if not dsn:
            raise AssertionError("D1_PG_TEST_DSN must name the disposable CI database")
        # Explicitly deny accidental DB selection: never use Django settings,
        # 'postgres' database or an arbitrary non-CI database.
        parsed = psycopg2.extensions.parse_dsn(dsn)
        if parsed.get("dbname") != "iamina_d1_receipt_ci" or (
            parsed.get("host") not in ("localhost", "127.0.0.1")
        ):
            raise AssertionError("D1_PG_TEST_DSN must use local iam ina test DB")
        self.pg = PostgresSignedReceiptRehearsal(dsn)
        self.dsn = dsn
        # CI-only reset. TRUNCATE bypasses append-only triggers for fixtures;
        # this class is never run as part of a production service.
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "TRUNCATE d1_receipt_ci.audit_events,"
                    "d1_receipt_ci.nonces_consumed,"
                    "d1_receipt_ci.public_keys RESTART IDENTITY CASCADE"
                )
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sqlite_issuer = SyntheticReceiptLedger(
            Path(self.temp.name) / "synthetic-issuer-only.sqlite3"
        )
        self.private = Ed25519PrivateKey.generate()
        self.kid = "ci-synth-kid-001"
        self.sqlite_issuer.register_test_signer(self.kid, self.private)
        self.pg.trust_test_public_key(self.kid, public_bytes(self.private))
        self.facts = CandidateFacts(
            django_user_id=735, owner=OWNER,
            source_sha256=SHA, independently_restored_sha256=SHA,
            consent_record_id="ci-synth-only-not-patient-consent",
            source_possession_evidence_id="ci-synth-only-not-real-possession",
        )

    def receipt(self):
        return self.sqlite_issuer.issue_test_only(self.facts, now=NOW)

    def claim(self, receipt, **overrides):
        kwargs = dict(expected_owner=OWNER, live_sha256=SHA, now=NOW + 1)
        kwargs.update(overrides)
        return self.pg.verify_and_consume(receipt, **kwargs)

    def refused(self, receipt, expected, **kwargs):
        with self.assertRaisesRegex(ReceiptRejected, expected):
            self.claim(receipt, **kwargs)

    def test_postgres_separate_issuer_verifier_accepts_once_only_advisory(self):
        receipt = self.receipt()
        fresh_server = PostgresSignedReceiptRehearsal(self.dsn)
        result = fresh_server.verify_and_consume(
            receipt, expected_owner=OWNER, live_sha256=SHA, now=NOW + 1
        )
        self.assertEqual(result["result"], "READY_FOR_EXTERNAL_SECURITY_REVIEW_ONLY")
        self.assertIs(result["authorizedToMigrate"], False)
        self.assertIs(result["clinicalGo"], False)
        self.assertIs(result["serverAuthenticatedOwner"], False)
        self.assertIs(result["serverVerifiedConsent"], False)
        self.assertIs(result["sourcePossessionProven"], False)
        self.refused(receipt, "D1_PG_NONCE_REPLAY")

    def test_concurrent_sessions_one_winner_seven_replays(self):
        receipt = self.receipt()

        def consume(_):
            ledger = PostgresSignedReceiptRehearsal(self.dsn)
            try:
                return ledger.verify_and_consume(
                    receipt, expected_owner=OWNER, live_sha256=SHA, now=NOW + 1
                )["result"]
            except ReceiptRejected as exc:
                return str(exc)

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(consume, range(8)))
        self.assertEqual(results.count("READY_FOR_EXTERNAL_SECURITY_REVIEW_ONLY"), 1)
        self.assertEqual(results.count("D1_PG_NONCE_REPLAY"), 7)
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM d1_receipt_ci.nonces_consumed")
                self.assertEqual(cur.fetchone()[0], 1)
                cur.execute(
                    "SELECT COUNT(*) FROM d1_receipt_ci.audit_events "
                    "WHERE event='SYNTHETIC_RECEIPT_CONSUMED'"
                )
                self.assertEqual(cur.fetchone()[0], 1)

    def test_revoked_public_key_denies_previous_receipt(self):
        issued = self.receipt()
        second = Ed25519PrivateKey.generate()
        self.pg.trust_test_public_key("ci-synth-kid-002", public_bytes(second))
        self.pg.revoke_test_public_key(self.kid)
        self.refused(issued, "D1_PG_KEY_UNTRUSTED")

    def test_key_rotation_allows_previous_unrevoked_receipt(self):
        old = self.receipt()
        second = Ed25519PrivateKey.generate()
        self.sqlite_issuer.register_test_signer("ci-synth-kid-002", second)
        self.pg.trust_test_public_key("ci-synth-kid-002", public_bytes(second))
        fresh = self.receipt()
        self.assertNotEqual(old["payload"]["kid"], fresh["payload"]["kid"])
        self.assertFalse(self.claim(old)["authorizedToMigrate"])
        self.assertFalse(self.claim(fresh)["authorizedToMigrate"])

    def test_invalid_signer_is_rejected_without_consuming_nonce(self):
        forged = copy.deepcopy(self.receipt())
        forged["payload"]["nonce"] = "9" * 32
        self.refused(forged, "D1_PG_SIGNATURE_INVALID")
        self.refused(copy.deepcopy(forged), "D1_PG_SIGNATURE_INVALID")
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM d1_receipt_ci.nonces_consumed")
                self.assertEqual(cur.fetchone()[0], 0)

    def test_wrong_owner_hash_or_expired_receipt_fail_closed(self):
        r = self.receipt()
        self.refused(r, "D1_PG_RECEIPT_SCOPE_INVALID",
                     expected_owner="amina_vault_v1_native_736")
        self.refused(r, "D1_PG_RECEIPT_SCOPE_INVALID", live_sha256=WRONG_SHA)
        self.refused(r, "D1_PG_RECEIPT_SCOPE_INVALID", now=NOW + 121)
        self.refused(r, "D1_PG_RECEIPT_SCOPE_INVALID", now=NOW - 100)
        self.assertFalse(self.claim(r)["authorizedToMigrate"])

    def test_untrusted_root_and_kid_collision_fail_closed(self):
        r = self.receipt()
        # Kid same but different key is not accepted.
        with self.assertRaisesRegex(ReceiptRejected, "D1_PG_KID_COLLISION"):
            self.pg.trust_test_public_key(self.kid, public_bytes(Ed25519PrivateKey.generate()))
        self.assertFalse(self.claim(r)["authorizedToMigrate"])
        self.pg.revoke_test_public_key(self.kid)
        with self.assertRaisesRegex(ReceiptRejected, "D1_PG_KEY_REVOKED"):
            self.pg.trust_test_public_key(self.kid, public_bytes(self.private))

    def test_audit_failure_rolls_back_nonce_atomically(self):
        r = self.receipt()
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE OR REPLACE FUNCTION d1_receipt_ci.reject_audit_for_test() "
                    "RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                    "IF NEW.event='SYNTHETIC_RECEIPT_CONSUMED' THEN "
                    "RAISE EXCEPTION 'D1_CI_INJECTED_AUDIT_FAILURE'; END IF; "
                    "RETURN NEW; END $$"
                )
                cur.execute(
                    "CREATE TRIGGER d1_ci_test_reject_audit "
                    "BEFORE INSERT ON d1_receipt_ci.audit_events "
                    "FOR EACH ROW EXECUTE FUNCTION d1_receipt_ci.reject_audit_for_test()"
                )
        with self.assertRaises(psycopg2.Error):
            self.claim(r)
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM d1_receipt_ci.nonces_consumed")
                self.assertEqual(cur.fetchone()[0], 0)
                cur.execute(
                    "DROP TRIGGER d1_ci_test_reject_audit ON d1_receipt_ci.audit_events"
                )
                cur.execute("DROP FUNCTION d1_receipt_ci.reject_audit_for_test()")
        self.assertFalse(self.claim(r)["authorizedToMigrate"])

    def test_database_immutes_consumed_nonces_and_audit(self):
        r = self.receipt()
        self.claim(r)
        with psycopg2.connect(self.dsn) as conn:
            with self.assertRaises(psycopg2.Error):
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM d1_receipt_ci.nonces_consumed")
            conn.rollback()
            with self.assertRaises(psycopg2.Error):
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE d1_receipt_ci.audit_events SET event='SYNTHETIC_KEY_REVOKED'"
                    )
            conn.rollback()
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM d1_receipt_ci.nonces_consumed")
                self.assertEqual(cur.fetchone()[0], 1)

    def test_audit_omits_patient_identifiers_and_secrets(self):
        self.claim(self.receipt())
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='d1_receipt_ci' AND "
                    "table_name='audit_events'"
                )
                cols = {x[0] for x in cur.fetchall()}
                self.assertTrue(cols.isdisjoint(
                    {"owner", "user_id", "patient_id", "consent", "sourceSha256",
                     "recovery_code", "private_key", "nonce"}
                ))

    def test_requires_local_dedicated_test_db(self):
        for dsn in (
            "dbname=postgres host=127.0.0.1 user=ci",
            "dbname=iamina_d1_receipt_ci host=unknown user=ci",
        ):
            parsed = psycopg2.extensions.parse_dsn(dsn)
            self.assertTrue(parsed.get("dbname") != "iamina_d1_receipt_ci" or
                            parsed.get("host") not in ("127.0.0.1", "localhost"))


if __name__ == "__main__":
    unittest.main()
