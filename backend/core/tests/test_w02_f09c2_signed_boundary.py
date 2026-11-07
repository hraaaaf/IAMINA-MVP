"""W02-F09-C2 RED-first: draft-only signed Web BFF -> Django transport.

All actors and keys are synthetic. None of these helpers is registered at an
HTTP endpoint. A browser cannot trigger rotation: C1 is ALWAYS HTTP 404.
Proof covers cryptographic binding AND durable nonce consumption on PG16.
"""

import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.db import close_old_connections, connection
from django.test import Client, override_settings
from django.utils import timezone

from core.models import BasePatientProfile, WebRefreshTransportNonce
from core.web_refresh_boundary import (
    WebRefreshBoundaryRejected,
    issue_family_csrf,
    verify_bff_refresh_envelope,
    verify_family_csrf,
)
from core.web_refresh_protocol import issue_web_refresh_family, rotate_web_refresh_family

pytestmark = pytest.mark.django_db(transaction=True)

_ROOT = Path(__file__).resolve().parents[3]
_HOST = "iamina-c2-synthetic.vercel.app"
_ORIGIN = "https://" + _HOST
_BODY = b'{"kind":"synthetic-refresh-proof"}'
_BFF_KEY = "TEST_ONLY_w02_F09_C2_shared_boundary_signer_2026_48_chars"
_CSRF_KEY = "TEST_ONLY_w02_F09_C2_independent_csrf_secret_2026_48"
_OTHER_KEY = "TEST_ONLY_w02_F09_C2_wrong_transport_signer_2026_48"


@pytest.fixture(autouse=True)
def _candidate_config(settings):
    settings.F09_WEB_REFRESH_ENABLED = True
    settings.F09_WEB_REFRESH_IDLE_SECONDS = 120
    settings.F09_WEB_REFRESH_ABSOLUTE_SECONDS = 540
    settings.F09_C2_BOUNDARY_ENABLED = True
    settings.F09_C2_BFF_HMAC_KEY = _BFF_KEY
    settings.F09_C2_CSRF_HMAC_KEY = _CSRF_KEY
    settings.F09_C2_EXPECTED_WEB_ORIGIN = _ORIGIN
    settings.F09_C2_CSRF_TTL_SECONDS = 60


def _patient(suffix):
    user = User.objects.create_user(
        username="c2-" + suffix,
        email=f"c2-{suffix}@example.invalid",
        password="Test-only-Web-Signed-Boundary-2026!",
    )
    BasePatientProfile.objects.get_or_create(patient=user)
    return user


def _from_node(*, timestamp=None, body=_BODY):
    """Actual Node22 producer, not a Python imitation of HMAC."""
    timestamp = int(time.time()) if timestamp is None else timestamp
    script = """
const {signRefreshBoundary} = require('./frontend/api/w02_f09c2_signing.js');
const out = signRefreshBoundary({
  key: process.env.C2_TEST_KEY,
  host: process.env.C2_TEST_HOST,
  timestampSeconds: Number(process.env.C2_TEST_TIME),
  nonceBytes: Buffer.alloc(32, 7),
  body: Buffer.from(process.env.C2_TEST_BODY, 'utf8'),
});
process.stdout.write(JSON.stringify(out));
"""
    env = {
        **os.environ,
        "C2_TEST_KEY": _BFF_KEY,
        "C2_TEST_HOST": _HOST,
        "C2_TEST_TIME": str(timestamp),
        "C2_TEST_BODY": body.decode("utf-8"),
    }
    result = subprocess.run(
        ["node", "-e", script],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    assert result.returncode == 0, result.stderr[:400]
    return json.loads(result.stdout)


def _verify(headers, *, body=_BODY, method="POST", path="/api/v1/auth/refresh"):
    return verify_bff_refresh_envelope(
        headers=headers,
        body=body,
        method=method,
        path=path,
    )


def test_c2_no_http_renewal_even_if_signed_transport_helpers_exist():
    response = Client().post(
        "/api/v1/auth/refresh",
        data=json.dumps({"kind": "synthetic"}),
        content_type="application/json",
    )
    assert response.status_code == 404
    assert not WebRefreshTransportNonce.objects.exists()


def test_c2_off_by_default_even_with_valid_node_proof():
    headers = _from_node()
    with override_settings(F09_C2_BOUNDARY_ENABLED=False):
        with pytest.raises(WebRefreshBoundaryRejected):
            _verify(headers)
    assert not WebRefreshTransportNonce.objects.exists()


def test_c2_node_to_django_hmac_verifies_once_only_and_never_logs_raw_material():
    headers = _from_node()
    assert _verify(headers) is True
    stored = WebRefreshTransportNonce.objects.get()
    assert len(stored.nonce_digest) == 64
    assert headers["x-iamina-bff-nonce"] not in repr(stored.__dict__)
    assert _BFF_KEY not in repr(stored.__dict__)
    with pytest.raises(WebRefreshBoundaryRejected):
        _verify(headers)
    assert WebRefreshTransportNonce.objects.count() == 1


@pytest.mark.parametrize(
    "attack",
    ["body", "method", "path", "origin", "timestamp", "nonce", "signature", "wrong_key"],
)
def test_c2_transport_tamper_or_wrong_key_never_consumes_nonce(attack):
    headers = _from_node()
    body, method, path = _BODY, "POST", "/api/v1/auth/refresh"
    if attack == "body":
        body += b"!"
    elif attack == "method":
        method = "GET"
    elif attack == "path":
        path = "/api/v1/auth/login"
    elif attack == "origin":
        headers["x-iamina-bff-origin"] = "https://attacker.example"
    elif attack == "timestamp":
        headers["x-iamina-bff-timestamp"] = str(int(time.time()) + 100)
    elif attack == "nonce":
        headers["x-iamina-bff-nonce"] = "A" * 43
    elif attack == "signature":
        headers["x-iamina-bff-proof"] = "v1." + "a" * 64
    else:
        with override_settings(F09_C2_BFF_HMAC_KEY=_OTHER_KEY):
            with pytest.raises(WebRefreshBoundaryRejected):
                _verify(headers)
        assert not WebRefreshTransportNonce.objects.exists()
        return
    with pytest.raises(WebRefreshBoundaryRejected):
        _verify(headers, body=body, method=method, path=path)
    assert not WebRefreshTransportNonce.objects.exists()


@pytest.mark.parametrize("delta", [-45, 45])
def test_c2_old_or_future_signed_envelope_is_denied(delta):
    headers = _from_node(timestamp=int(time.time()) + delta)
    with pytest.raises(WebRefreshBoundaryRejected):
        _verify(headers)
    assert not WebRefreshTransportNonce.objects.exists()


@pytest.mark.parametrize("field", ["x-iamina-bff-nonce", "x-iamina-bff-proof", "x-iamina-bff-origin"])
def test_c2_missing_required_signed_header_is_denied(field):
    headers = _from_node()
    del headers[field]
    with pytest.raises(WebRefreshBoundaryRejected):
        _verify(headers)


def test_c2_bad_key_configuration_never_authenticates():
    headers = _from_node()
    with override_settings(F09_C2_BFF_HMAC_KEY="short"):
        with pytest.raises(WebRefreshBoundaryRejected):
            _verify(headers)
    with override_settings(F09_C2_BFF_HMAC_KEY=_CSRF_KEY, F09_C2_CSRF_HMAC_KEY=_CSRF_KEY):
        with pytest.raises(WebRefreshBoundaryRejected):
            _verify(headers)
    assert not WebRefreshTransportNonce.objects.exists()


def test_c2_family_signed_csrf_is_account_origin_and_rotation_bound():
    a = _patient("signed-a")
    b = _patient("signed-b")
    family_a, secret_a = issue_web_refresh_family(a)
    family_b, _ = issue_web_refresh_family(b)
    header_token = issue_family_csrf(family_a, origin=_ORIGIN)
    assert verify_family_csrf(family_a, origin=_ORIGIN, cookie_token=header_token, header_token=header_token)
    assert not verify_family_csrf(family_b, origin=_ORIGIN, cookie_token=header_token, header_token=header_token)
    assert not verify_family_csrf(family_a, origin="https://evil.test", cookie_token=header_token, header_token=header_token)
    assert not verify_family_csrf(family_a, origin=_ORIGIN, cookie_token=header_token, header_token="x")
    assert not verify_family_csrf(family_a, origin=_ORIGIN, cookie_token="x", header_token=header_token)
    rotate_web_refresh_family(secret_a)
    family_a.refresh_from_db()
    assert not verify_family_csrf(family_a, origin=_ORIGIN, cookie_token=header_token, header_token=header_token)


def test_c2_csrf_ttl_invalid_policy_and_expiry_fail_closed():
    a = _patient("signed-ttl")
    family, _ = issue_web_refresh_family(a)
    token = issue_family_csrf(family, origin=_ORIGIN)
    with patch("core.web_refresh_boundary.timezone.now", return_value=timezone.now() + timedelta(seconds=65)):
        assert not verify_family_csrf(family, origin=_ORIGIN, cookie_token=token, header_token=token)
    with override_settings(F09_C2_CSRF_TTL_SECONDS=None):
        with pytest.raises(WebRefreshBoundaryRejected):
            issue_family_csrf(family, origin=_ORIGIN)
        assert not verify_family_csrf(family, origin=_ORIGIN, cookie_token=token, header_token=token)
    with override_settings(F09_C2_BOUNDARY_ENABLED=False):
        with pytest.raises(WebRefreshBoundaryRejected):
            issue_family_csrf(family, origin=_ORIGIN)
        assert not verify_family_csrf(family, origin=_ORIGIN, cookie_token=token, header_token=token)


@pytest.mark.skipif(connection.vendor != "postgresql", reason="Concurrency proof requires PostgreSQL")
def test_c2_same_signed_envelope_two_pg16_requests_exactly_one_wins():
    headers = _from_node()
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                return ("accepted", _verify(headers))
            except WebRefreshBoundaryRejected:
                return ("rejected", False)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert sorted(x[0] for x in results) == ["accepted", "rejected"]
    assert WebRefreshTransportNonce.objects.count() == 1
