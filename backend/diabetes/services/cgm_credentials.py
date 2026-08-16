from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken


class CGMCredentialError(RuntimeError):
    """Stable fail-closed credential configuration/decryption error."""


def _fernet() -> Fernet:
    raw_key = os.environ.get("CGM_CREDENTIAL_KEY", "").strip()
    if not raw_key:
        raise CGMCredentialError("cgm_credential_key_unavailable")
    try:
        return Fernet(raw_key.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise CGMCredentialError("cgm_credential_key_invalid") from exc


def encrypt_cgm_credential(secret: str) -> str:
    secret = secret.strip()
    if not secret:
        raise CGMCredentialError("cgm_credential_empty")
    return _fernet().encrypt(secret.encode("utf-8")).decode("ascii")


def decrypt_cgm_credential(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
        raise CGMCredentialError("cgm_credential_unreadable") from exc
