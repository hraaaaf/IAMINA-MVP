"""Synthetic-only Redis-free Pulper: AEAD preview held in volatile browser memory.

No server-side transient medical staging and no raw OCR text in the token.
DO NOT activate for real patient data before independent privacy review.
"""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
import uuid
from dataclasses import asdict

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

from diabetes.services.documents.schema import (
    FieldEvidence,
    GlucoseReading,
    LabValues,
    MedicationEntry,
    PulperOutput,
)

_TTL_SECONDS = 3600
_MAX_TOKEN_CHARS = 128 * 1024
_VERSION = "iamina.pulper.synthetic.aead.v1"


class PreviewEnvelopeError(ValueError):
    """Stable failure without disclosing a token, patient field or cryptographic key."""


def synthetic_mode_enabled() -> bool:
    return (
        getattr(settings, "IAMINA_NO_REDIS", False)
        and getattr(settings, "IAMINA_PULPER_STATELESS_SYNTHETIC", False)
        and getattr(settings, "DEBUG", False)
        and not getattr(settings, "VERCEL", False)
        and not getattr(settings, "VERCEL_ENV", "")
    )


def _key() -> bytes:
    secret = settings.SECRET_KEY
    if not isinstance(secret, str) or len(secret) < 24:
        raise PreviewEnvelopeError("invalid preview key configuration")
    return hashlib.sha256((secret + ":w01:synthetic-pulper:aead:v1").encode()).digest()


def _aad(patient_id: int, batch_id: str, version: int) -> bytes:
    if type(patient_id) is not int or patient_id <= 0 or type(version) is not int:
        raise PreviewEnvelopeError("invalid preview identity")
    try:
        canonical = str(uuid.UUID(batch_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise PreviewEnvelopeError("invalid preview batch") from exc
    if canonical != batch_id:
        raise PreviewEnvelopeError("noncanonical preview batch")
    return f"{_VERSION}:{patient_id}:{canonical}:{version}".encode("ascii")


def issue_preview_envelope(
    output: PulperOutput, *, patient_id: int, batch_id: str,
    auth_version: int, now: int | None = None,
) -> str:
    if not synthetic_mode_enabled():
        raise PreviewEnvelopeError("synthetic preview disabled")
    aad = _aad(patient_id, batch_id, auth_version)
    t = int(time.time()) if now is None else now
    if type(t) is not int or t < 0:
        raise PreviewEnvelopeError("invalid preview time")
    payload = asdict(output)
    payload.pop("raw_text", None)
    encoded = json.dumps(
        {"v": 1, "iat": t, "exp": t + _TTL_SECONDS, "data": payload},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > 72 * 1024:
        raise PreviewEnvelopeError("preview exceeds bounded envelope")
    nonce = secrets.token_bytes(12)
    token = base64.urlsafe_b64encode(
        nonce + AESGCM(_key()).encrypt(nonce, encoded, aad)
    ).decode("ascii").rstrip("=")
    if len(token) > _MAX_TOKEN_CHARS:
        raise PreviewEnvelopeError("preview token too large")
    return token


def _evidence(data: dict) -> dict[str, FieldEvidence]:
    if not isinstance(data, dict) or len(data) > 64:
        raise PreviewEnvelopeError("invalid evidence")
    return {str(k): FieldEvidence(**v) for k, v in data.items()}


def _restore_output(data: dict) -> PulperOutput:
    if not isinstance(data, dict):
        raise PreviewEnvelopeError("invalid preview content")
    if len(data.get("glucose_readings", [])) > 2000 or len(data.get("medications", [])) > 200:
        raise PreviewEnvelopeError("oversized preview content")
    payload = dict(data)
    payload.pop("raw_text", None)
    readings = []
    for row in payload.pop("glucose_readings", []):
        item = dict(row)
        item["evidence"] = _evidence(item.get("evidence", {}))
        readings.append(GlucoseReading(**item))
    medications = []
    for row in payload.pop("medications", []):
        item = dict(row)
        item["evidence"] = _evidence(item.get("evidence", {}))
        medications.append(MedicationEntry(**item))
    lv = dict(payload.pop("lab_values", {}))
    lv["evidence"] = _evidence(lv.get("evidence", {}))
    payload["glucose_readings"] = readings
    payload["medications"] = medications
    payload["lab_values"] = LabValues(**lv)
    payload["raw_text"] = ""
    return PulperOutput(**payload)


def verify_preview_envelope(
    token: str, *, patient_id: int, batch_id: str,
    auth_version: int, now: int | None = None,
) -> PulperOutput:
    if not synthetic_mode_enabled():
        raise PreviewEnvelopeError("synthetic preview disabled")
    aad = _aad(patient_id, batch_id, auth_version)
    if not isinstance(token, str) or not 50 <= len(token) <= _MAX_TOKEN_CHARS:
        raise PreviewEnvelopeError("invalid preview token")
    try:
        raw = base64.b64decode(
            token + "=" * (-len(token) % 4), altchars=b"-_", validate=True,
        )
        if len(raw) <= 28:
            raise PreviewEnvelopeError("invalid preview token")
        plaintext = AESGCM(_key()).decrypt(raw[:12], raw[12:], aad)
        payload = json.loads(plaintext)
        current = int(time.time()) if now is None else now
        if type(current) is not int or type(payload) is not dict:
            raise PreviewEnvelopeError("invalid preview timestamp")
        issued, expires = payload.get("iat"), payload.get("exp")
        if (
            payload.get("v") != 1 or type(issued) is not int
            or type(expires) is not int or issued > current + 30
            or expires != issued + _TTL_SECONDS or current >= expires
        ):
            raise PreviewEnvelopeError("expired or invalid preview")
        return _restore_output(payload["data"])
    except (InvalidTag, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise PreviewEnvelopeError("invalid or expired preview") from exc


def preview_nonce_digest(batch_id: str) -> str:
    _aad(1, batch_id, 0)
    return hashlib.sha256(("pulper-confirm:v1:" + batch_id).encode()).hexdigest()
