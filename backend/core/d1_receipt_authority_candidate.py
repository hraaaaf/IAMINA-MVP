"""D1 server-side receipt authority PROTOTYPE, NEVER routed to patients.

Synthetic-only design rehearsal. No Django API, no installed production keys,
no authentication/consent/possession verifier, no clinical migration authority.

This service validates cryptographic syntax and persists nonce consumption in
a SQLite file to test durable transactional replay rejection. Production must
replace the ephemeral in-memory signer with KMS/HSM, the local ledger with
managed DB transactions, and mock input context with verified backend facts.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ISSUER = "iamina-d1-ci-synthetic-only"
PURPOSE = "J1_BACKUP_RESTORED_J2_REVIEW_ONLY"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
KID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{3,50}$")
NONCE_RE = re.compile(r"^[0-9a-f]{32}$")
OWNER_RE = re.compile(r"^amina_vault_v1_native_([1-9][0-9]*)$")
# Narrow lifetime is deliberately shorter than patient recovery workflows.
MAX_TTL_SECONDS = 120


class ReceiptRejected(ValueError):
    """Expected refusal; never an implied authorization to migrate."""


@dataclass(frozen=True)
class CandidateFacts:
    """Only synthetic fixture facts. Production MUST verify these server-side."""

    django_user_id: int
    owner: str
    source_sha256: str
    independently_restored_sha256: str
    consent_record_id: str
    source_possession_evidence_id: str

    def validate(self) -> None:
        if isinstance(self.django_user_id, bool) or not isinstance(self.django_user_id, int):
            raise ReceiptRejected("D1_BACKEND_SUBJECT_INVALID")
        matched = OWNER_RE.fullmatch(self.owner)
        if not matched or int(matched.group(1)) != self.django_user_id:
            raise ReceiptRejected("D1_RECEIPT_OWNER_ID_MISMATCH")
        if not SHA256_RE.fullmatch(self.source_sha256):
            raise ReceiptRejected("D1_SOURCE_HASH_INVALID")
        if self.independently_restored_sha256 != self.source_sha256:
            raise ReceiptRejected("D1_INDEPENDENT_RESTORE_MISMATCH")
        if not (self.consent_record_id.startswith("ci-synth-") and
                self.source_possession_evidence_id.startswith("ci-synth-")):
            raise ReceiptRejected("D1_SYNTHETIC_EVIDENCE_REQUIRED")


def _canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _b64(bytes_: bytes) -> str:
    return base64.urlsafe_b64encode(bytes_).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ReceiptRejected("D1_INVALID_SIGNATURE_ENCODING")
    try:
        result = base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise ReceiptRejected("D1_INVALID_SIGNATURE_ENCODING") from exc
    if _b64(result) != value or len(result) != 64:
        raise ReceiptRejected("D1_INVALID_SIGNATURE_ENCODING")
    return result


class SyntheticReceiptLedger:
    """SQLite-replay ledger + Ed25519 public keyring; no transport endpoint.

    Each call opens its own connection and uses BEGIN IMMEDIATE. Multiple
    instances sharing one disk file atomically reject the same nonce twice.
    A signer private key is provided in memory ONLY for explicit synthetic
    tests, never stored in this SQLite file.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._signers: dict[str, Ed25519PrivateKey] = {}
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        conn.execute("PRAGMA busy_timeout=10000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS d1_candidate_keys ("
                "kid TEXT PRIMARY KEY, public BLOB NOT NULL,"
                "state TEXT NOT NULL CHECK(state IN ('active','verify','revoked')))"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS d1_one_active_key "
                "ON d1_candidate_keys(state) WHERE state='active'"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS d1_candidate_consumed ("
                "issuer TEXT NOT NULL, nonce TEXT NOT NULL, kid TEXT NOT NULL,"
                "used_at INTEGER NOT NULL, PRIMARY KEY(issuer,nonce))"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS d1_candidate_audit ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "event TEXT NOT NULL, kid TEXT, nonce_hash TEXT, occurred_at INTEGER NOT NULL)"
            )

    def _audit(self, conn: sqlite3.Connection, event: str, kid: str | None,
               nonce: str | None, now: int) -> None:
        # No patient IDs, names, raw nonce, SHA of clinical records, code or key.
        nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()[:16] if nonce else None
        conn.execute(
            "INSERT INTO d1_candidate_audit(event,kid,nonce_hash,occurred_at) "
            "VALUES(?,?,?,?)", (event, kid, nonce_hash, now)
        )

    def register_test_signer(self, kid: str, key: Ed25519PrivateKey) -> None:
        if not KID_RE.fullmatch(kid) or not isinstance(key, Ed25519PrivateKey):
            raise ReceiptRejected("D1_KEY_REGISTRATION_INVALID")
        public = key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                previous = conn.execute(
                    "SELECT public,state FROM d1_candidate_keys WHERE kid=?", (kid,)
                ).fetchone()
                if previous is not None and previous[0] != public:
                    raise ReceiptRejected("D1_KEY_ID_COLLISION")
                if previous is not None and previous[1] == "revoked":
                    raise ReceiptRejected("D1_REVOKED_KEY_CANNOT_REACTIVATE")
                conn.execute(
                    "UPDATE d1_candidate_keys SET state='verify' WHERE state='active'"
                )
                conn.execute(
                    "INSERT INTO d1_candidate_keys(kid,public,state) VALUES(?,?,'active') "
                    "ON CONFLICT(kid) DO UPDATE SET state='active'", (kid, public)
                )
                self._audit(conn, "SYNTHETIC_KEY_ACTIVATED", kid, None, int(time.time()))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        self._signers[kid] = key

    def revoke(self, kid: str) -> None:
        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                result = conn.execute(
                    "UPDATE d1_candidate_keys SET state='revoked' WHERE kid=? AND state!='revoked'",
                    (kid,)
                )
                if result.rowcount != 1:
                    raise ReceiptRejected("D1_KEY_NOT_REVOCABLE")
                self._audit(conn, "SYNTHETIC_KEY_REVOKED", kid, None, int(time.time()))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        self._signers.pop(kid, None)

    def issue_test_only(self, facts: CandidateFacts, *,
                        now: int | None = None, ttl_seconds: int = 90) -> dict:
        facts.validate()
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or (
            not 1 <= ttl_seconds <= MAX_TTL_SECONDS
        ):
            raise ReceiptRejected("D1_RECEIPT_TTL_INVALID")
        now = int(time.time()) if now is None else now
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT kid FROM d1_candidate_keys WHERE state='active'"
            ).fetchall()
        if len(rows) != 1:
            raise ReceiptRejected("D1_NO_ACTIVE_TRUSTED_SIGNER")
        kid = rows[0][0]
        signer = self._signers.get(kid)
        if signer is None:
            raise ReceiptRejected("D1_SIGNER_NOT_AVAILABLE_IN_SERVER")
        payload = {
            "version": 1, "purpose": PURPOSE, "issuer": ISSUER,
            "kid": kid, "owner": facts.owner,
            "sourceSha256": facts.source_sha256,
            "restoredSha256": facts.independently_restored_sha256,
            "issuedAt": now, "expiresAt": now + ttl_seconds,
            "nonce": secrets.token_hex(16),
            "advisoryOnly": True,
        }
        signature = _b64(signer.sign(_canonical(payload)))
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._audit(conn, "SYNTHETIC_RECEIPT_ISSUED", kid, payload["nonce"], now)
            conn.commit()
        return {"payload": payload, "signature": signature}

    def verify_and_consume(self, receipt: dict, *,
                           expected_owner: str, live_source_sha256: str,
                           now: int | None = None) -> dict:
        """Atomic receipt consumption. NEVER returns permission to migrate.

        The expected owner and live digest are inputs from a trusted backend
        in the future, NOT established by this prototype.
        """
        now = int(time.time()) if now is None else now
        if not isinstance(receipt, dict) or set(receipt) != {"payload", "signature"}:
            raise ReceiptRejected("D1_RECEIPT_SHAPE_INVALID")
        payload = receipt["payload"]
        if not isinstance(payload, dict) or set(payload) != {
            "version", "purpose", "issuer", "kid", "owner",
            "sourceSha256", "restoredSha256", "issuedAt",
            "expiresAt", "nonce", "advisoryOnly"
        }:
            raise ReceiptRejected("D1_RECEIPT_PAYLOAD_INVALID")
        kid, nonce = payload["kid"], payload["nonce"]
        if (payload["version"] != 1 or payload["purpose"] != PURPOSE or
            payload["issuer"] != ISSUER or payload["advisoryOnly"] is not True or
            not isinstance(kid, str) or not KID_RE.fullmatch(kid) or
            not isinstance(nonce, str) or not NONCE_RE.fullmatch(nonce) or
            not isinstance(payload["owner"], str) or
            not OWNER_RE.fullmatch(payload["owner"]) or
            payload["owner"] != expected_owner or
            not isinstance(live_source_sha256, str) or
            not SHA256_RE.fullmatch(live_source_sha256) or
            payload["sourceSha256"] != live_source_sha256 or
            payload["restoredSha256"] != live_source_sha256 or
            not isinstance(payload["issuedAt"], int) or
            isinstance(payload["issuedAt"], bool) or
            not isinstance(payload["expiresAt"], int) or
            isinstance(payload["expiresAt"], bool) or
            payload["expiresAt"] <= payload["issuedAt"] or
            payload["expiresAt"] - payload["issuedAt"] > MAX_TTL_SECONDS or
            now < payload["issuedAt"] - 30 or now > payload["expiresAt"]):
            raise ReceiptRejected("D1_RECEIPT_SCOPE_EXPIRED_OR_UNTRUSTED")
        signature = _unb64(receipt["signature"])
        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT public,state FROM d1_candidate_keys WHERE kid=?", (kid,)
                ).fetchone()
                if row is None or row[1] == "revoked":
                    raise ReceiptRejected("D1_RECEIPT_SIGNER_NOT_TRUSTED")
                try:
                    Ed25519PublicKey.from_public_bytes(row[0]).verify(
                        signature, _canonical(payload)
                    )
                except (ValueError, InvalidSignature) as exc:
                    raise ReceiptRejected("D1_RECEIPT_SIGNATURE_REJECTED") from exc
                try:
                    conn.execute(
                        "INSERT INTO d1_candidate_consumed(issuer,nonce,kid,used_at) "
                        "VALUES(?,?,?,?)", (ISSUER, nonce, kid, now)
                    )
                except sqlite3.IntegrityError as exc:
                    raise ReceiptRejected("D1_RECEIPT_REPLAY_REJECTED") from exc
                self._audit(conn, "SYNTHETIC_RECEIPT_CONSUMED", kid, nonce, now)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return {
            "result": "READY_FOR_EXTERNAL_SECURITY_REVIEW_ONLY",
            "authorizedToMigrate": False,
            "clinicalGo": False,
        }

    def audit_summary(self) -> list[tuple[str, int]]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT event,COUNT(*) FROM d1_candidate_audit GROUP BY event ORDER BY event"
            ).fetchall()
