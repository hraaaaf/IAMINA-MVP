"""D1 PostgreSQL 16 signed-receipt rehearsal, NEVER a live clinical authority.

This module has no Django URL, migration, settings or user-access path.
It takes caller-provided owner/source facts: they are NOT authenticated here.
Test PostgreSQL schema must be loaded separately (no automatic table creation).
No private key, recovery code, actual patient data or consent is stored.
Production must use separately reviewed KMS/HSM issuance and authenticated
Django owner/possession/consent/server-source evidence, plus durable anti-replay
on a managed PostgreSQL database with restricted roles.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any

import psycopg2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from core.d1_receipt_authority_candidate import (
    ISSUER,
    KID_RE,
    MAX_TTL_SECONDS,
    NONCE_RE,
    OWNER_RE,
    PURPOSE,
    SHA256_RE,
    ReceiptRejected,
    _canonical,
    _unb64,
)

# This constant ensures code cannot be wired to a production schema casually.
SCHEMA = "d1_receipt_ci"
_LOCK_KEYRING = 1260150901  # stable test-only lock for serial key rotation


class PostgresSignedReceiptRehearsal:
    """Synthetic signature verifier with persistent, atomic replay protection."""

    def __init__(self, dsn: str):
        if not isinstance(dsn, str) or not dsn:
            raise ReceiptRejected("D1_PG_TEST_DSN_REQUIRED")
        self._dsn = dsn

    def _connect(self):
        return psycopg2.connect(self._dsn, connect_timeout=5)

    @staticmethod
    def _audit(cur, event: str, kid: str, nonce: str | None) -> None:
        nonce_sha = hashlib.sha256(nonce.encode("ascii")).hexdigest() if nonce else None
        cur.execute(
            "INSERT INTO d1_receipt_ci.audit_events (event,kid,nonce_sha256) "
            "VALUES (%s,%s,%s)", (event, kid, nonce_sha)
        )

    def trust_test_public_key(self, kid: str, key_raw: bytes) -> None:
        """Move previous signer to verify-only and pin the new public key.

        This is NOT a product KMS rotation API. Only test caller controls keys.
        """
        if (not isinstance(kid, str) or not KID_RE.fullmatch(kid) or
            not isinstance(key_raw, bytes) or len(key_raw) != 32):
            raise ReceiptRejected("D1_PG_PUBLIC_KEY_INVALID")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_KEYRING,))
                cur.execute(
                    "SELECT public_raw,status FROM d1_receipt_ci.public_keys "
                    "WHERE kid=%s FOR UPDATE", (kid,)
                )
                row = cur.fetchone()
                if row and bytes(row[0]) != key_raw:
                    raise ReceiptRejected("D1_PG_KID_COLLISION")
                if row and row[1] == "revoked":
                    raise ReceiptRejected("D1_PG_KEY_REVOKED")
                cur.execute(
                    "UPDATE d1_receipt_ci.public_keys SET status='verify' "
                    "WHERE status='active'"
                )
                if row:
                    cur.execute(
                        "UPDATE d1_receipt_ci.public_keys SET status='active' "
                        "WHERE kid=%s", (kid,)
                    )
                else:
                    cur.execute(
                        "INSERT INTO d1_receipt_ci.public_keys(kid,public_raw,status) "
                        "VALUES (%s,%s,'active')",
                        (kid, psycopg2.Binary(key_raw))
                    )
                self._audit(cur, "SYNTHETIC_KEY_ACTIVATED", kid, None)

    def revoke_test_public_key(self, kid: str) -> None:
        if not isinstance(kid, str) or not KID_RE.fullmatch(kid):
            raise ReceiptRejected("D1_PG_KID_INVALID")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_KEYRING,))
                cur.execute(
                    "UPDATE d1_receipt_ci.public_keys SET status='revoked' "
                    "WHERE kid=%s AND status!='revoked' RETURNING kid", (kid,)
                )
                if cur.fetchone() is None:
                    raise ReceiptRejected("D1_PG_KEY_NOT_REVOCABLE")
                self._audit(cur, "SYNTHETIC_KEY_REVOKED", kid, None)

    @staticmethod
    def _validated_payload(receipt: dict, expected_owner: str,
                           live_sha256: str, now: int) -> tuple[dict, bytes]:
        if not isinstance(receipt, dict) or set(receipt.keys()) != {"payload", "signature"}:
            raise ReceiptRejected("D1_PG_RECEIPT_SHAPE_INVALID")
        payload = receipt["payload"]
        fields = {
            "version", "purpose", "issuer", "kid", "owner",
            "sourceSha256", "restoredSha256", "issuedAt",
            "expiresAt", "nonce", "advisoryOnly",
        }
        if not isinstance(payload, dict) or set(payload.keys()) != fields:
            raise ReceiptRejected("D1_PG_RECEIPT_PAYLOAD_INVALID")
        kid, nonce, owner = payload["kid"], payload["nonce"], payload["owner"]
        issued, expires = payload["issuedAt"], payload["expiresAt"]
        if (
            type(payload["version"]) is not int or payload["version"] != 1 or
            payload["purpose"] != PURPOSE or payload["issuer"] != ISSUER or
            payload["advisoryOnly"] is not True or
            not isinstance(kid, str) or not KID_RE.fullmatch(kid) or
            not isinstance(nonce, str) or not NONCE_RE.fullmatch(nonce) or
            not isinstance(owner, str) or not OWNER_RE.fullmatch(owner) or
            not isinstance(expected_owner, str) or owner != expected_owner or
            not isinstance(live_sha256, str) or not SHA256_RE.fullmatch(live_sha256) or
            payload["sourceSha256"] != live_sha256 or
            payload["restoredSha256"] != live_sha256 or
            type(issued) is not int or type(expires) is not int or
            expires <= issued or expires - issued > MAX_TTL_SECONDS or
            now < issued - 30 or now > expires
        ):
            raise ReceiptRejected("D1_PG_RECEIPT_SCOPE_INVALID")
        return payload, _unb64(receipt["signature"])

    def verify_and_consume(self, receipt: dict, *, expected_owner: str,
                           live_sha256: str, now: int | None = None) -> dict[str, Any]:
        """Atomic Ed25519 and nonce check; result is always advisory-only."""
        now = int(time.time()) if now is None else now
        payload, signature = self._validated_payload(
            receipt, expected_owner, live_sha256, now
        )
        kid, nonce = payload["kid"], payload["nonce"]
        with self._connect() as conn:
            with conn.cursor() as cur:
                # FOR SHARE prevents a concurrent revocation changing the
                # public key state before the current verification commits.
                cur.execute(
                    "SELECT public_raw,status FROM d1_receipt_ci.public_keys "
                    "WHERE kid=%s FOR SHARE", (kid,)
                )
                row = cur.fetchone()
                if not row or row[1] == "revoked":
                    raise ReceiptRejected("D1_PG_KEY_UNTRUSTED")
                try:
                    Ed25519PublicKey.from_public_bytes(bytes(row[0])).verify(
                        signature, _canonical(payload)
                    )
                except (InvalidSignature, ValueError) as exc:
                    raise ReceiptRejected("D1_PG_SIGNATURE_INVALID") from exc
                cur.execute(
                    "INSERT INTO d1_receipt_ci.nonces_consumed (issuer,nonce,kid) "
                    "VALUES (%s,%s,%s) ON CONFLICT (issuer,nonce) DO NOTHING "
                    "RETURNING nonce", (ISSUER, nonce, kid)
                )
                if cur.fetchone() is None:
                    raise ReceiptRejected("D1_PG_NONCE_REPLAY")
                self._audit(cur, "SYNTHETIC_RECEIPT_CONSUMED", kid, nonce)
        return {
            "result": "READY_FOR_EXTERNAL_SECURITY_REVIEW_ONLY",
            "authorizedToMigrate": False,
            "clinicalGo": False,
            "serverAuthenticatedOwner": False,
            "serverVerifiedConsent": False,
            "sourcePossessionProven": False,
        }
