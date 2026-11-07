"""W02-F09-C4 — actual Node22 BFF-built HTTP request, Django adapter unmounted.

PG16-only synthetic credentials. RequestFactory exercises Django HttpRequest
parsing; real Client still gets 404 because no refresh handler is mounted.
No bearer/cookie/HTTP response is minted. This is NOT hosted browser E2E.
"""
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from django.db import close_old_connections, connection
from django.test import Client, RequestFactory, override_settings

from core.models import WebRefreshConsumedSecret, WebRefreshTransportNonce
from core.tests.test_w02_f09c3_oidc_atomic_tabs import (
    _BFF_KEY,
    _CSRF_KEY,
    _OWNER,
    _PROJECT,
    _PROJECT_ID,
    _session,
    oidc,  # noqa: F401: pytest fixture re-export
)
from core.web_refresh_c4_http_candidate import (
    WebRefreshC4Rejected,
    execute_unmounted_web_refresh,
)

pytestmark = pytest.mark.django_db(transaction=True)
_ROOT = Path(__file__).resolve().parents[3]
_HOST = "iamina-c3-synthetic.vercel.app"
_ORIGIN = "https://" + _HOST
_API_HOST = "iamina-c4-api-synthetic.vercel.app"


@pytest.fixture(autouse=True)
def _settings(settings):
    settings.ALLOWED_HOSTS = ["testserver", _API_HOST]
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
    settings.F09_C4_HTTP_ADAPTER_ENABLED = True
    settings.F09_C4_EXPECTED_API_HOST = _API_HOST


def _node_signed_http(oidc_token, family, raw, csrf):
    js = """
const {prepareDedicatedRefresh} = require('./frontend/api/w02_f09c4_prepare.js');
const host = process.env.C4_WEB_HOST;
const csrf = process.env.C4_CSRF;
const req = {
  method: 'POST',
  headers: {
    host,
    origin: 'https://' + host,
    'sec-fetch-site': 'same-origin',
    cookie: 'iamina_refresh_family=' + process.env.C4_FAMILY +
      '; iamina_refresh=' + process.env.C4_REFRESH +
      '; iamina_refresh_csrf=' + csrf,
    'x-iamina-csrf': csrf,
    authorization: 'Bearer client-forgery-never-forward',
    'x-vercel-trusted-oidc-idp-token': 'browser-forgery',
  },
};
const out = prepareDedicatedRefresh(req, {
  env: {VERCEL_ENV:'preview', VERCEL_URL:host,
    VERCEL_PROJECT_ID:'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI'},
  oidcFromRuntime: process.env.C4_OIDC,
  signingKey: process.env.C4_BFF_KEY,
});
process.stdout.write(JSON.stringify({
  headers:out.headers, body:out.body.toString('utf8'), path:out.path,
}));
"""
    env = {
        **os.environ,
        "C4_WEB_HOST": _HOST,
        "C4_CSRF": csrf,
        "C4_FAMILY": str(family.pk),
        "C4_REFRESH": raw,
        "C4_OIDC": oidc_token,
        "C4_BFF_KEY": _BFF_KEY,
    }
    result = subprocess.run(
        ["node", "-e", js], cwd=_ROOT, env=env,
        capture_output=True, text=True, check=False, timeout=8,
    )
    assert result.returncode == 0, result.stderr[:350]
    return json.loads(result.stdout)


def _django_req(signed, *, body=None, **extra):
    meta = {
        "HTTP_HOST": _API_HOST,
        **{
            "HTTP_" + key.upper().replace("-", "_"): value
            for key, value in signed["headers"].items()
        },
        **extra,
    }
    return RequestFactory().post(
        "/api/v1/auth/refresh",
        data=signed["body"] if body is None else body,
        content_type="application/json",
        **meta,
    )


def _execute(signed, jwks, **extra):
    return execute_unmounted_web_refresh(
        _django_req(signed, **extra), _synthetic_jwks=jwks,
    )


def test_c4_real_http_route_is_still_404_and_never_creates_session():
    response = Client().post(
        "/api/v1/auth/refresh", data="{}",
        content_type="application/json",
    )
    assert response.status_code == 404
    assert not response.has_header("set-cookie")
    assert WebRefreshConsumedSecret.objects.count() == 0
    assert WebRefreshTransportNonce.objects.count() == 0


def test_c4_adapter_disabled_by_default_even_with_signed_request(oidc):
    sign, jwks = oidc
    _, family, raw, csrf = _session("c4-default-off")
    prepared = _node_signed_http(sign(), family, raw, csrf)
    with override_settings(F09_C4_HTTP_ADAPTER_ENABLED=False):
        with pytest.raises(WebRefreshC4Rejected):
            _execute(prepared, jwks)
    assert WebRefreshTransportNonce.objects.count() == 0


def test_c4_node22_to_django_http_adaptation_rotates_once(oidc):
    sign, jwks = oidc
    user, family, raw, csrf = _session("c4-happy")
    signed = _node_signed_http(sign(), family, raw, csrf)
    assert "cookie" not in signed["headers"]
    assert "authorization" not in signed["headers"]
    assert "x-vercel-oidc-token" not in signed["headers"]
    rotated = _execute(signed, jwks)
    assert rotated.startswith("iamina-wr1.")
    assert rotated != raw
    assert WebRefreshConsumedSecret.objects.count() == 1
    assert WebRefreshTransportNonce.objects.count() == 1
    with pytest.raises(WebRefreshC4Rejected):
        _execute(signed, jwks)
    assert WebRefreshConsumedSecret.objects.count() == 1


@pytest.mark.parametrize("mutation", [
    "bad_body", "cookie_forwarded", "bearer_forwarded", "bad_host",
    "missing_oidc", "tampered_oidc", "duplicate_json",
])
def test_c4_http_untrusted_input_denied_without_rotation(oidc, mutation):
    sign, jwks = oidc
    _, family, raw, csrf = _session("c4-deny-" + mutation)
    signed = _node_signed_http(sign(), family, raw, csrf)
    extra = {}
    body = None
    if mutation == "bad_body":
        body = signed["body"] + " "
    elif mutation == "cookie_forwarded":
        extra["HTTP_COOKIE"] = "iamina_refresh=" + raw
    elif mutation == "bearer_forwarded":
        extra["HTTP_AUTHORIZATION"] = "Bearer client-token"
    elif mutation == "bad_host":
        extra["HTTP_HOST"] = "attacker.example"
    elif mutation == "missing_oidc":
        extra["HTTP_X_VERCEL_TRUSTED_OIDC_IDP_TOKEN"] = ""
    elif mutation == "tampered_oidc":
        extra["HTTP_X_VERCEL_TRUSTED_OIDC_IDP_TOKEN"] = "not-a-vercel-jwt"
    elif mutation == "duplicate_json":
        body = signed["body"][:-1] + ', "family_id": 99}'
    request = _django_req(signed, body=body, **extra)
    with pytest.raises(WebRefreshC4Rejected):
        execute_unmounted_web_refresh(request, _synthetic_jwks=jwks)
    assert WebRefreshConsumedSecret.objects.count() == 0


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PG16 row-lock race")
def test_c4_two_http_requests_one_rotation_after_lock(oidc):
    sign, jwks = oidc
    _, family, raw, csrf = _session("c4-multitab")
    signed = [
        _node_signed_http(sign(), family, raw, csrf),
        _node_signed_http(sign(), family, raw, csrf),
    ]
    barrier = Barrier(2)

    def worker(index):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                return ("ok", _execute(signed[index], jwks))
            except WebRefreshC4Rejected:
                return ("denied", None)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, (0, 1)))
    assert sorted(row[0] for row in results) == ["denied", "ok"]
    assert WebRefreshConsumedSecret.objects.count() == 1
    assert WebRefreshTransportNonce.objects.count() == 2
