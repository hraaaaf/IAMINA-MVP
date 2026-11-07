"""W02 C7 atomic receipt: REAL Django HttpRequest + PG16 + Node22 BFF verifier.

Synthetic signed Vercel OIDC, BFF HMAC and accounts only. C7 is NOT an
installed API route and returns NO real HTTP Set-Cookie. These tests prove
atomicity, bounded access, pre-spent nonce and A/B contention on a PG row.
"""
import base64  # noqa: I001  (shared pytest fixtures are deliberately re-exported)
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import pytest
from django.db import close_old_connections, connection
from django.test import Client, override_settings

from core.models import WebRefreshConsumedSecret, WebRefreshTransportNonce
from core.tests.test_w02_f09c3_oidc_atomic_tabs import (
    _BFF_KEY, _CSRF_KEY, _OWNER, _PROJECT, _PROJECT_ID,
    oidc,  # noqa: F401
)
from core.tests.test_w02_f09c4_http_adapter_pg import (
    _API_HOST, _ORIGIN, _django_req, _node_signed_http, _session,
    _settings as c4_settings,  # noqa: F401
)
from core.web_refresh_boundary import verify_family_csrf
from core.web_refresh_c5_family_bearer import (
    WebFamilyBearerRejected, verify_family_bound_web_bearer,
)
from core.web_refresh_c7_atomic_candidate import (
    WebRefreshC7Rejected,
    execute_unmounted_atomic_refresh_bundle,
)

pytestmark = pytest.mark.django_db(transaction=True)
_ROOT = Path(__file__).resolve().parents[3]
_REPLY_KEY = "C7_RESPONSE_HMAC_TEST_ONLY_2026_DISTINCT_KEY_48"


@pytest.fixture(autouse=True)
def _c7_settings(c4_settings, settings):  # noqa: F811  (pytest fixture injection)
    settings.F09_C5_FAMILY_ACCESS_ENABLED = True
    settings.F09_C5_ACCESS_MAX_AGE_SECONDS = 60
    settings.F09_C7_ATOMIC_ENABLED = True
    settings.F09_C7_COOKIE_MAX_AGE_SECONDS = 120
    settings.F09_C7_RESPONSE_HMAC_KEY = _REPLY_KEY


def _prepared(oidc_token, family, raw, csrf):
    signed = _node_signed_http(oidc_token, family, raw, csrf)
    return signed, _django_req(signed)


def _execute(signed, jwks):
    return execute_unmounted_atomic_refresh_bundle(
        _django_req(signed), _synthetic_jwks=jwks
    )


def _verify_actual_node(signed, result, response_key=_REPLY_KEY):
    js = """
const {verifyCandidateC7BackendResult} = require('./frontend/api/w02_f09c7_verify_reply.js');
const originalSignedHeaders = JSON.parse(process.env.C7_REQUEST_HEADERS);
const upstream = {
  status:200,
  headers:JSON.parse(process.env.C7_REPLY_HEADERS),
  body:Buffer.from(process.env.C7_REPLY_BODY_B64,'base64'),
};
try {
  const reply = verifyCandidateC7BackendResult({
    enabled:true, upstream, originalSignedHeaders,
    responseHmacKey:process.env.C7_RESPONSE_KEY,
  });
  process.stdout.write(JSON.stringify({
    accepted:true, status:reply.status,
    cookieCount:reply.headers['set-cookie'].length,
    noRefreshInJson:!reply.body.includes('iamina-wr1.'),
    noCsrfInJson:!reply.body.includes('c2.'),
    accessInJson:JSON.parse(reply.body).access_token.startsWith('iamina-web.'),
    httpOnly:reply.headers['set-cookie'].slice(0,2)
      .every(row=>row.includes('HttpOnly; Secure; SameSite=Strict')),
  }));
} catch {
  process.stdout.write(JSON.stringify({accepted:false}));
}
"""
    env = {
        **os.environ,
        "C7_REQUEST_HEADERS": json.dumps(signed["headers"]),
        "C7_REPLY_HEADERS": json.dumps(result["headers"]),
        "C7_REPLY_BODY_B64": base64.b64encode(result["body"]).decode("ascii"),
        "C7_RESPONSE_KEY": response_key,
    }
    proc = subprocess.run(
        ["node", "-e", js], cwd=_ROOT, env=env, text=True,
        capture_output=True, timeout=10, check=False,
    )
    assert proc.returncode == 0, proc.stderr[:300]
    return json.loads(proc.stdout)


def test_c7_flag_off_denies_before_nonce_or_family_mutation(oidc):  # noqa: F811
    sign, jwks = oidc
    _, family, raw, csrf = _session("c7-disabled")
    signed, _ = _prepared(sign(), family, raw, csrf)
    with override_settings(F09_C7_ATOMIC_ENABLED=False):
        with pytest.raises(WebRefreshC7Rejected):
            _execute(signed, jwks)
    assert WebRefreshConsumedSecret.objects.count() == 0
    assert WebRefreshTransportNonce.objects.count() == 0


def test_c7_atomic_refresh_bearer_csrf_and_authenticated_node_reply(oidc):  # noqa: F811
    sign, jwks = oidc
    user, family, raw, csrf = _session("c7-success")
    signed, _ = _prepared(sign(), family, raw, csrf)
    receipt = _execute(signed, jwks)
    assert receipt["status"] == 200
    assert receipt["headers"]["cache-control"] == "no-store"
    assert "set-cookie" not in receipt["headers"]
    values = json.loads(receipt["body"])
    assert set(values) == {
        "familyId", "refreshSecret", "csrfToken", "accessBearer",
        "accessMaxAgeSeconds", "cookieMaxAgeSeconds",
    }
    assert values["refreshSecret"] != raw
    assert values["accessMaxAgeSeconds"] == 60
    assert values["cookieMaxAgeSeconds"] <= 120
    assert verify_family_bound_web_bearer(values["accessBearer"]).pk == user.pk
    family.refresh_from_db()
    assert verify_family_csrf(
        family, origin=_ORIGIN, cookie_token=values["csrfToken"],
        header_token=values["csrfToken"],
    )
    assert not verify_family_csrf(
        family, origin=_ORIGIN, cookie_token=csrf, header_token=csrf,
    )
    assert WebRefreshConsumedSecret.objects.count() == 1
    assert WebRefreshTransportNonce.objects.count() == 1
    assert _verify_actual_node(signed, receipt) == {
        "accepted": True, "status": 200, "cookieCount": 3,
        "noRefreshInJson": True, "noCsrfInJson": True,
        "accessInJson": True, "httpOnly": True,
    }


def test_c7_reply_hmac_rejects_tamper_wrong_key_and_wrong_request_nonce(oidc):  # noqa: F811
    sign, jwks = oidc
    _, family, raw, csrf = _session("c7-reply-attest")
    signed, _ = _prepared(sign(), family, raw, csrf)
    receipt = _execute(signed, jwks)
    assert _verify_actual_node(signed, receipt, "WRONG_BFF_RESULT_SECRET_KEY_2026_48") == {
        "accepted": False
    }
    tampered = {**receipt, "body": receipt["body"] + b" "}
    assert _verify_actual_node(signed, tampered) == {"accepted": False}
    wrong_nonce = {**signed, "headers": {
        **signed["headers"], "x-iamina-bff-nonce": "Q" * 43,
    }}
    assert _verify_actual_node(wrong_nonce, receipt) == {"accepted": False}


def test_c7_postrotation_failure_rolls_back_all_family_changes_but_nonce_spent(oidc):  # noqa: F811
    sign, jwks = oidc
    _, family, raw, csrf = _session("c7-rollback")
    signed, _ = _prepared(sign(), family, raw, csrf)
    with patch(
        "core.web_refresh_c7_atomic_candidate.issue_family_bound_web_bearer",
        side_effect=WebFamilyBearerRejected("test-only-injected-failure"),
    ):
        with pytest.raises(WebRefreshC7Rejected):
            _execute(signed, jwks)
    family.refresh_from_db()
    assert family.revoke_at is None
    assert WebRefreshConsumedSecret.objects.count() == 0
    assert WebRefreshTransportNonce.objects.count() == 1
    with pytest.raises(WebRefreshC7Rejected):
        _execute(signed, jwks)
    # A new independently signed nonce remains valid after rollback.
    res = _execute(_node_signed_http(sign(), family, raw, csrf), jwks)
    assert res["status"] == 200
    assert WebRefreshConsumedSecret.objects.count() == 1


@pytest.mark.parametrize("mutation", [
    "host", "cookie", "bearer", "oidc", "origin", "raw", "csrf", "body",
])
def test_c7_hostile_transport_denies_without_family_rotation(oidc, mutation):  # noqa: F811
    sign, jwks = oidc
    _, family, raw, csrf = _session("c7-hostile-" + mutation)
    signed, _ = _prepared(sign(), family, raw, csrf)
    overrides = {}
    if mutation == "host":
        overrides["HTTP_HOST"] = "attack.example"
    elif mutation == "cookie":
        overrides["HTTP_COOKIE"] = "sessionid=forged"
    elif mutation == "bearer":
        overrides["HTTP_AUTHORIZATION"] = "Bearer forged"
    elif mutation == "oidc":
        overrides["HTTP_X_VERCEL_TRUSTED_OIDC_IDP_TOKEN"] = "forgery"
    elif mutation == "origin":
        overrides["HTTP_X_IAMINA_BFF_ORIGIN"] = "https://attack.example"
    elif mutation == "raw":
        signed["body"] = signed["body"].replace(raw, "iamina-wr1." + "A" * 64)
    elif mutation == "csrf":
        signed["body"] = signed["body"].replace(csrf, "forged")
    elif mutation == "body":
        signed["body"] += '{"unexpected":true}'
    req = _django_req(signed, **overrides)
    with pytest.raises(WebRefreshC7Rejected):
        execute_unmounted_atomic_refresh_bundle(req, _synthetic_jwks=jwks)
    assert WebRefreshConsumedSecret.objects.count() == 0


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PG16 row lock proof")
def test_c7_two_signed_tabs_one_atomic_bundle_no_cross_family_revoke(oidc):  # noqa: F811
    sign, jwks = oidc
    user, family, raw, csrf = _session("c7-two-tab")
    signed = [
        _node_signed_http(sign(), family, raw, csrf),
        _node_signed_http(sign(), family, raw, csrf),
    ]
    barrier = Barrier(2)

    def run(index):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                receipt = _execute(signed[index], jwks)
                return "ok", receipt
            except WebRefreshC7Rejected:
                return "denied", None
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, (0, 1)))
    assert sorted(row[0] for row in outcomes) == ["denied", "ok"]
    assert WebRefreshConsumedSecret.objects.count() == 1
    assert WebRefreshTransportNonce.objects.count() == 2
    family.refresh_from_db()
    assert family.revoke_at is None
    winning = next(v for status, v in outcomes if status == "ok")
    assert verify_family_bound_web_bearer(json.loads(winning["body"])["accessBearer"]).pk == user.pk


def test_c7_real_refresh_route_stays_404_and_never_sets_cookie():
    response = Client().post(
        "/api/v1/auth/refresh", data="{}", content_type="application/json",
    )
    assert response.status_code == 404
    assert "Set-Cookie" not in response.headers
