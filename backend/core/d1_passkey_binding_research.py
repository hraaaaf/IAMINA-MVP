"""Fail-closed D1 research service for *server-side* WebAuthn owner binding.

This module is intentionally UNMOUNTED. Passing this service does NOT unlock a
local PRF vault, authenticate a login, or authorize patient data. Only an
authenticated Django session may be passed as the principal in future wiring.
Do not accept a user ID, origin, RP ID, or challenge from a browser as authority.
"""
from __future__ import annotations

import base64
import json
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from core.models import BasePatientProfile
from core.models.d1_research_passkey import (
    D1ResearchPasskeyChallenge,
    D1ResearchPasskeyCredential,
)

TTL_SECONDS = 120


class D1PasskeyResearchDenied(Exception):
    """Non-sensitive refusal: never include credentials, challenges or keys."""


def _deny() -> None:
    raise D1PasskeyResearchDenied("D1_PASSKEY_RESEARCH_DENIED")


def _config():
    if getattr(settings, "D1_PASSKEY_RESEARCH_ENABLED", False) is not True:
        _deny()
    rp_id = getattr(settings, "D1_PASSKEY_RESEARCH_RP_ID", "")
    origin = getattr(settings, "D1_PASSKEY_RESEARCH_ORIGIN", "")
    if not isinstance(rp_id, str) or not isinstance(origin, str):
        _deny()
    try:
        parsed = urlsplit(origin)
    except ValueError:
        _deny()
    if (
        not rp_id or not origin or parsed.scheme != "https"
        or parsed.netloc != rp_id or parsed.hostname != rp_id
        or parsed.port is not None or parsed.path or parsed.query
        or parsed.fragment or parsed.username or parsed.password
        or not rp_id.endswith(".vercel.app")
    ):
        # Experimental exact Preview origin only. No wildcard or derived Host.
        _deny()
    return rp_id, origin


def _principal(user, session_key: str):
    """The future protected session router must provide these server values."""
    if (
        user is None or not getattr(user, "is_authenticated", False)
        or not getattr(user, "is_active", False)
        or not isinstance(session_key, str) or not (16 <= len(session_key) <= 80)
    ):
        _deny()
    version = BasePatientProfile.objects.filter(
        patient_id=user.pk,
    ).values_list("auth_token_version", flat=True).first()
    if version is None:
        _deny()
    return version


def _scope(user, session_key: str):
    rp_id, origin = _config()
    version = _principal(user, session_key)
    return rp_id, origin, version


def _new_challenge(user, session_key, version, rp_id, origin, purpose,
                   *, credential=None, handle=None):
    return D1ResearchPasskeyChallenge.objects.create(
        patient=user,
        credential=credential,
        purpose=purpose,
        challenge=secrets.token_bytes(32),
        user_handle=handle if handle is not None else secrets.token_bytes(32),
        origin=origin,
        rp_id=rp_id,
        auth_token_version=version,
        session_key=session_key,
        expires_at=timezone.now() + timedelta(seconds=TTL_SECONDS),
    )


def _consume(user, session_key, version, rp_id, origin, ceremony_id, purpose):
    """Atomic compare-and-consume before verification: even failure burns nonce."""
    if not isinstance(ceremony_id, str) or len(ceremony_id) > 80:
        _deny()
    try:
        ceremony_id = uuid.UUID(ceremony_id)
    except (ValueError, AttributeError):
        _deny()
    now = timezone.now()
    with transaction.atomic():
        updated = D1ResearchPasskeyChallenge.objects.filter(
            pk=ceremony_id, patient=user, purpose=purpose,
            auth_token_version=version, session_key=session_key,
            rp_id=rp_id, origin=origin, consumed_at__isnull=True,
            expires_at__gt=now,
        ).update(consumed_at=now)
        if updated != 1:
            _deny()
        record = D1ResearchPasskeyChallenge.objects.get(pk=ceremony_id)
    return record


def _canonical_id(value):
    """Reject alternate encodings of the SAME credential ID (cross-owner uniqueness)."""
    if not isinstance(value, str) or not value or len(value) > 1024:
        _deny()
    try:
        raw = base64url_to_bytes(value)
    except Exception:
        _deny()
    canonical = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    if not raw or canonical != value:
        _deny()
    return raw


def _client_payload(credential):
    if not isinstance(credential, dict):
        _deny()
    _canonical_id(credential.get("id"))
    try:
        if (
            not isinstance(credential.get("response"), dict)
            or len(json.dumps(credential)) > 16000
        ):
            _deny()
    except (TypeError, ValueError, OverflowError):
        _deny()
    return credential


def begin_enrollment(user, session_key: str) -> dict:
    rp_id, origin, version = _scope(user, session_key)
    ceremony = _new_challenge(
        user, session_key, version, rp_id, origin, "enroll",
    )
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name="IAMINA D1 research only",
        user_id=bytes(ceremony.user_handle),
        user_name="research-account",
        user_display_name="IAMINA D1 research credential",
        challenge=bytes(ceremony.challenge),
        timeout=TTL_SECONDS * 1000,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )
    return {"ceremony_id": str(ceremony.pk), "options": json.loads(options_to_json(options))}


def finish_enrollment(user, session_key: str, ceremony_id: str, credential: dict) -> dict:
    rp_id, origin, version = _scope(user, session_key)
    ceremony = _consume(user, session_key, version, rp_id, origin, ceremony_id, "enroll")
    payload = _client_payload(credential)
    # The extension result is client-supplied and NOT hardware attestation:
    # required for this research protocol, never proof of PRF availability.
    extensions = payload.get("clientExtensionResults")
    prf = extensions.get("prf") if isinstance(extensions, dict) else None
    if (
        payload.get("authenticatorAttachment") != "platform"
        or not isinstance(prf, dict) or prf.get("enabled") is not True
    ):
        _deny()
    try:
        verified = verify_registration_response(
            credential=payload,
            expected_challenge=bytes(ceremony.challenge),
            expected_rp_id=rp_id,
            expected_origin=origin,
            require_user_verification=True,
        )
        credential_id = verified.credential_id
        if (
            not isinstance(credential_id, bytes)
            or not credential_id
            or credential_id != _canonical_id(payload["id"])
        ):
            _deny()
        if _principal(user, session_key) != version:
            _deny()
        # Credential ID uniqueness is global: neither another account nor
        # a revoked binding can be silently claimed by this account.
        with transaction.atomic():
            D1ResearchPasskeyCredential.objects.create(
                patient=user,
                credential_id=payload["id"],
                public_key=verified.credential_public_key,
                user_handle=ceremony.user_handle,
                sign_count=verified.sign_count,
                rp_id=rp_id,
                origin=origin,
            )
    except (D1PasskeyResearchDenied, IntegrityError):
        _deny()
    except Exception:
        _deny()
    return {"status": "BOUND_RESEARCH_ONLY", "patient_ready": False}


def begin_verification(user, session_key: str, credential_id: str) -> dict:
    rp_id, origin, version = _scope(user, session_key)
    if not isinstance(credential_id, str) or len(credential_id) > 1024:
        _deny()
    binding = D1ResearchPasskeyCredential.objects.filter(
        patient=user, credential_id=credential_id, rp_id=rp_id,
        origin=origin, revoked_at__isnull=True,
    ).first()
    if binding is None:
        _deny()
    ceremony = _new_challenge(
        user, session_key, version, rp_id, origin, "verify",
        credential=binding, handle=binding.user_handle,
    )
    options = generate_authentication_options(
        rp_id=rp_id,
        challenge=bytes(ceremony.challenge),
        timeout=TTL_SECONDS * 1000,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(binding.credential_id)),
        ],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return {"ceremony_id": str(ceremony.pk), "options": json.loads(options_to_json(options))}


def finish_verification(user, session_key: str, ceremony_id: str, credential: dict) -> dict:
    rp_id, origin, version = _scope(user, session_key)
    ceremony = _consume(user, session_key, version, rp_id, origin, ceremony_id, "verify")
    binding = ceremony.credential
    if (
        binding is None or binding.patient_id != user.pk
        or binding.revoked_at is not None or binding.rp_id != rp_id
        or binding.origin != origin
    ):
        _deny()
    payload = _client_payload(credential)
    if payload["id"] != binding.credential_id:
        _deny()
    handle = payload.get("response", {}).get("userHandle")
    if handle is not None:
        try:
            if base64url_to_bytes(handle) != bytes(binding.user_handle):
                _deny()
        except Exception:
            _deny()
    try:
        verified = verify_authentication_response(
            credential=payload,
            expected_challenge=bytes(ceremony.challenge),
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=bytes(binding.public_key),
            credential_current_sign_count=binding.sign_count,
            require_user_verification=True,
        )
        new_count = verified.new_sign_count
        if type(new_count) is not int or new_count < 0:
            _deny()
        if _principal(user, session_key) != version:
            _deny()
        # Nonzero authenticators must advance; zero-only passkeys are allowed.
        with transaction.atomic():
            active = D1ResearchPasskeyCredential.objects.select_for_update().get(
                pk=binding.pk, patient=user, revoked_at__isnull=True,
            )
            if new_count != 0 and new_count <= active.sign_count:
                _deny()
            if new_count == 0 and active.sign_count != 0:
                _deny()
            active.sign_count = new_count
            active.save(update_fields=["sign_count"])
    except Exception:
        _deny()
    # No bearer, authentication token, signed session or DEK is issued.
    return {"status": "ASSERTION_VERIFIED_RESEARCH_ONLY", "patient_ready": False}
