"""W02-F09-C3 isolated synthetic service-JWT, family transaction, tab races.

This tests a candidate module, NOT a mounted HTTP endpoint or browser E2E.
Only disposable PostgreSQL and generated keys/accounts are used.
"""
import base64
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.contrib.auth.models import User
from django.db import close_old_connections, connection
from django.test import override_settings
from django.utils import timezone

from core.models import (
    BasePatientProfile, WebRefreshConsumedSecret,
    WebRefreshTransportNonce,
)
from core.web_refresh_boundary import issue_family_csrf
from core.web_refresh_c3_candidate import (
    WebRefreshC3Rejected, rotate_web_refresh_c3_candidate,
    verify_vercel_service_identity,
)
from core.web_refresh_protocol import issue_web_refresh_family

pytestmark = pytest.mark.django_db(transaction=True)
_ROOT = Path(__file__).resolve().parents[3]
_HOST = "iamina-c3-synthetic.vercel.app"
_ORIGIN = "https://" + _HOST
_BODY = b'{"kind":"synthetic-c3-only"}'
_BFF_KEY = "TEST_ONLY_C3_BFF_HMAC_separate_secret_2026_48"
_CSRF_KEY = "TEST_ONLY_C3_CSRF_separate_secret_2026_48"
_OWNER = "iamina-synthetic-owner"
_PROJECT = "iamina-synthetic-web"
_PROJECT_ID = "prj_ABCDEF1234567890abcde"


@pytest.fixture(autouse=True)
def _settings(settings):
    settings.F09_WEB_REFRESH_ENABLED = True
    settings.F09_WEB_REFRESH_IDLE_SECONDS = 120
    settings.F09_WEB_REFRESH_ABSOLUTE_SECONDS = 540
    settings.F09_C2_BOUNDARY_ENABLED = True
    settings.F09_C2_BFF_HMAC_KEY = _BFF_KEY
    settings.F09_C2_CSRF_HMAC_KEY = _CSRF_KEY
    settings.F09_C2_EXPECTED_WEB_ORIGIN = _ORIGIN
    settings.F09_C2_CSRF_TTL_SECONDS = 60
    settings.F09_C3_ENABLED = True
    settings.F09_C3_SYNTHETIC_JWKS_ALLOWED = True
    settings.F09_C3_OIDC_OWNER = _OWNER
    settings.F09_C3_OIDC_PROJECT = _PROJECT
    settings.F09_C3_OIDC_PROJECT_ID = _PROJECT_ID


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


@pytest.fixture
def oidc():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private.public_key().public_numbers()
    jwks = {"keys": [{
        "kty": "RSA", "alg": "RS256", "use": "sig", "kid": "synthetic-key",
        "n": _b64(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")),
        "e": _b64(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")),
    }]}

    def sign(*, overrides=None, header_overrides=None):
        now = int(time.time())
        claims = {
            "iss": "https://oidc.vercel.com/" + _OWNER,
            "aud": "https://vercel.com/" + _OWNER,
            "sub": f"owner:{_OWNER}:project:{_PROJECT}:environment:preview",
            "owner": _OWNER, "project": _PROJECT,
            "project_id": _PROJECT_ID, "environment": "preview",
            "iat": now - 5, "nbf": now - 5, "exp": now + 300,
        }
        claims.update(overrides or {})
        header = {"alg": "RS256", "typ": "JWT", "kid": "synthetic-key"}
        header.update(header_overrides or {})
        encoded = ".".join([
            _b64(json.dumps(header, sort_keys=True, separators=(",", ":")).encode()),
            _b64(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode()),
        ])
        signature = private.sign(encoded.encode(), padding.PKCS1v15(), hashes.SHA256())
        return encoded + "." + _b64(signature)

    return sign, jwks


def _headers():
    """Call actual Node22 signer (not a Python approximation)."""
    js = """
const {signRefreshBoundary} = require('./frontend/api/w02_f09c2_signing.js');
const headers = signRefreshBoundary({
  key: process.env.C3_TEST_KEY,
  host: process.env.C3_TEST_HOST,
  body: Buffer.from(process.env.C3_TEST_BODY, 'utf8'),
});
process.stdout.write(JSON.stringify(headers));
"""
    env = {**os.environ, "C3_TEST_KEY": _BFF_KEY,
           "C3_TEST_HOST": _HOST, "C3_TEST_BODY": _BODY.decode()}
    result = subprocess.run(
        ["node", "-e", js], cwd=_ROOT, env=env, text=True,
        capture_output=True, timeout=8, check=False,
    )
    assert result.returncode == 0, result.stderr[:300]
    return json.loads(result.stdout)


def _patient(suffix):
    user = User.objects.create_user(
        username="c3-" + suffix,
        email=f"c3-{suffix}@example.invalid",
        password="Synthetic-Test-Only-No-Real-Patient!",
    )
    BasePatientProfile.objects.get_or_create(patient=user)
    return user


def _session(suffix):
    user = _patient(suffix)
    family, raw_secret = issue_web_refresh_family(user)
    csrf = issue_family_csrf(family, origin=_ORIGIN)
    return user, family, raw_secret, csrf


def _rotate(token, jwks, family, raw, csrf, *, headers=None, origin=_ORIGIN):
    return rotate_web_refresh_c3_candidate(
        oidc_token=token, signed_headers=_headers() if headers is None else headers,
        signed_body=_BODY, family_id=family.pk, raw_refresh_secret=raw,
        origin=origin, cookie_csrf=csrf, header_csrf=csrf,
        _synthetic_jwks=jwks,
    )


def test_c3_is_off_by_default_even_with_valid_oidc_and_hmac(oidc):
    token, jwks = oidc[0](), oidc[1]
    _, family, raw, csrf = _session("off")
    with override_settings(F09_C3_ENABLED=False):
        with pytest.raises(WebRefreshC3Rejected):
            _rotate(token, jwks, family, raw, csrf)
    assert WebRefreshTransportNonce.objects.count() == 0
    assert WebRefreshConsumedSecret.objects.count() == 0


def test_c3_valid_signed_oidc_team_issuer_exact_claims(oidc):
    sign, jwks = oidc
    assert verify_vercel_service_identity(sign(), _synthetic_jwks=jwks)


@pytest.mark.parametrize("claim,bad", [
    ("iss", "https://oidc.vercel.com/other"),
    ("aud", "https://vercel.com/other"),
    ("sub", "owner:other:project:other:environment:preview"),
    ("owner", "other"), ("project", "another"),
    ("project_id", "prj_WRONG1234567890"), ("environment", "production"),
    ("iat", 4102444800), ("nbf", 4102444800), ("exp", 1),
])
def test_c3_rejects_wrong_oidc_claims(oidc, claim, bad):
    sign, jwks = oidc
    with pytest.raises(WebRefreshC3Rejected):
        verify_vercel_service_identity(sign(overrides={claim: bad}), _synthetic_jwks=jwks)


def test_c3_oidc_rejects_alg_confusion_signature_tamper_and_duplicate_kid(oidc):
    sign, jwks = oidc
    bad_alg = sign(header_overrides={"alg": "none"})
    forged = sign()[:-5] + "AAAAA"
    duplicate = {"keys": jwks["keys"] + jwks["keys"]}
    for token, keys in [(bad_alg, jwks), (forged, jwks), (sign(), duplicate)]:
        with pytest.raises(WebRefreshC3Rejected):
            verify_vercel_service_identity(token, _synthetic_jwks=keys)
    with override_settings(F09_C3_SYNTHETIC_JWKS_ALLOWED=False):
        with pytest.raises(WebRefreshC3Rejected):
            verify_vercel_service_identity(sign(), _synthetic_jwks=jwks)


def test_c3_invalid_service_never_consumes_transport_nonce(oidc):
    sign, jwks = oidc
    _, family, raw, csrf = _session("bad-service")
    with pytest.raises(WebRefreshC3Rejected):
        _rotate(sign(overrides={"project_id": "prj_ATTACK1234567890"}),
                jwks, family, raw, csrf)
    assert WebRefreshTransportNonce.objects.count() == 0
    assert WebRefreshConsumedSecret.objects.count() == 0


def test_c3_valid_service_rotates_once_and_stale_csrf_fails(oidc):
    sign, jwks = oidc
    _, family, raw, csrf = _session("success")
    replacement = _rotate(sign(), jwks, family, raw, csrf)
    assert replacement.startswith("iamina-wr1.")
    assert replacement != raw
    family.refresh_from_db()
    assert family.revoke_at is None
    assert WebRefreshConsumedSecret.objects.count() == 1
    assert WebRefreshTransportNonce.objects.count() == 1
    with pytest.raises(WebRefreshC3Rejected):
        _rotate(sign(), jwks, family, raw, csrf)
    assert WebRefreshConsumedSecret.objects.count() == 1
    assert WebRefreshTransportNonce.objects.count() == 2


def test_c3_cross_account_csrf_rejected_and_nonce_spent(oidc):
    sign, jwks = oidc
    _, family_a, _, csrf_a = _session("cross-a")
    _, family_b, raw_b, _ = _session("cross-b")
    with pytest.raises(WebRefreshC3Rejected):
        _rotate(sign(), jwks, family_b, raw_b, csrf_a)
    assert WebRefreshTransportNonce.objects.count() == 1
    assert WebRefreshConsumedSecret.objects.count() == 0
    family_a.refresh_from_db()
    family_b.refresh_from_db()
    assert family_a.revoke_at is None and family_b.revoke_at is None


def test_c3_explicit_revocation_and_auth_generation_deny(oidc):
    sign, jwks = oidc
    user, family, raw, csrf = _session("logout")
    family.revoke_at = timezone.now()
    family.save(update_fields=["revoke_at"])
    with pytest.raises(WebRefreshC3Rejected):
        _rotate(sign(), jwks, family, raw, csrf)
    assert WebRefreshConsumedSecret.objects.count() == 0

    _, fresh, fresh_raw, fresh_csrf = _session("token-generation")
    BasePatientProfile.objects.filter(patient_id=fresh.user_id).update(
        auth_token_version=fresh.auth_version + 1,
    )
    with pytest.raises(WebRefreshC3Rejected):
        _rotate(sign(), jwks, fresh, fresh_raw, fresh_csrf)
    assert WebRefreshConsumedSecret.objects.count() == 0


def test_c3_invalid_csrf_still_spends_nonce_and_cannot_retry_request(oidc):
    sign, jwks = oidc
    _, family, raw, csrf = _session("csrf")
    headers = _headers()
    with pytest.raises(WebRefreshC3Rejected):
        _rotate(sign(), jwks, family, raw, "invalid-csrf", headers=headers)
    assert WebRefreshTransportNonce.objects.count() == 1
    with pytest.raises(WebRefreshC3Rejected):
        _rotate(sign(), jwks, family, raw, csrf, headers=headers)
    assert WebRefreshTransportNonce.objects.count() == 1
    assert WebRefreshConsumedSecret.objects.count() == 0


@pytest.mark.skipif(connection.vendor != "postgresql", reason="Atomic two-tab proof needs PG16")
def test_c3_two_tabs_same_family_one_rotation_one_denial(oidc):
    sign, jwks = oidc
    user, family, raw, csrf = _session("tab-race")
    headers = [_headers(), _headers()]
    barrier = Barrier(2)

    def tab(index):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                rotated = _rotate(sign(), jwks, family, raw, csrf, headers=headers[index])
                return ("ok", rotated)
            except WebRefreshC3Rejected:
                return ("denied", None)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(tab, (0, 1)))

    assert sorted(status for status, _ in results) == ["denied", "ok"]
    assert WebRefreshConsumedSecret.objects.count() == 1
    assert WebRefreshTransportNonce.objects.count() == 2
    family.refresh_from_db()
    assert family.revoke_at is None
    profile = BasePatientProfile.objects.get(patient=user)
    assert profile.auth_token_version == family.auth_version
