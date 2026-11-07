"""W02-F09-C6: genuine Django-Ninja HTTP test-only authentication boundary.

This test URLconf does NOT appear in amina.urls or diabetes.api.main.
It verifies the C6 HttpBearer candidate using Django Client/Ninja dispatch
and disposable PostgreSQL16 family/account records. Real clinical routes must
still reject the experimental C5 token as HTTP 401.
"""

import json

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.urls import path
from ninja import NinjaAPI

from core.models import BasePatientProfile
from core.native_auth import issue_native_token, revoke_native_tokens
from core.web_refresh_c5_family_bearer import (
    issue_family_bound_web_bearer,
    revoke_one_web_family_using_bearer,
)
from core.web_refresh_c6_http_auth_candidate import CandidateWebFamilyHttpBearer
from core.web_refresh_protocol import issue_web_refresh_family

pytestmark = pytest.mark.django_db(transaction=True)
_api = NinjaAPI(title="C6 synthetic-only auth contract", version="1", urls_namespace="c6-synthetic")
_candidate_auth = CandidateWebFamilyHttpBearer()


@_api.get("/private", auth=_candidate_auth)
def candidate_private_view(request):
    return {"owner_id": request.auth.pk, "authentication": "test-only-c6"}


urlpatterns = [path("__c6_synthetic_only__/", _api.urls)]
_URL = "/__c6_synthetic_only__/private"


@pytest.fixture(autouse=True)
def _synthetic_limits(settings):
    settings.F09_WEB_REFRESH_ENABLED = True
    settings.F09_WEB_REFRESH_IDLE_SECONDS = 120
    settings.F09_WEB_REFRESH_ABSOLUTE_SECONDS = 540
    settings.F09_C5_FAMILY_ACCESS_ENABLED = True
    settings.F09_C5_ACCESS_MAX_AGE_SECONDS = 60
    settings.F09_C6_HTTP_AUTH_ENABLED = True
    settings.ALLOWED_HOSTS = ["testserver"]


def _new_user(label):
    user = User.objects.create_user(
        username=f"c6-{label}", password="C6-Synthetic-Only-Password-2026!"
    )
    BasePatientProfile.objects.get_or_create(patient=user)
    return user


def _issue(user):
    family, refresh = issue_web_refresh_family(user)
    bearer = issue_family_bound_web_bearer(family.pk, refresh)
    return family, refresh, bearer


def _get(bearer=None, *, client=None, **kwargs):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {bearer}"} if bearer else {}
    return (client or Client()).get(_URL, **headers, **kwargs)


def test_c6_test_only_ninja_http_accepts_valid_family_token_and_never_mints_cookies():
    user = _new_user("real-route")
    _, _, bearer = _issue(user)
    with override_settings(ROOT_URLCONF=__name__):
        response = _get(bearer)
    assert response.status_code == 200
    assert response.json() == {
        "owner_id": user.pk, "authentication": "test-only-c6",
    }
    assert "Set-Cookie" not in response.headers
    assert not response.cookies


def test_c6_rejects_no_bearer_native_bearer_and_malformed_auth_header():
    user = _new_user("only-family")
    _, _, bearer = _issue(user)
    native = issue_native_token(user)
    with override_settings(ROOT_URLCONF=__name__):
        assert _get().status_code == 401
        assert _get(native).status_code == 401
        assert Client().get(_URL, HTTP_AUTHORIZATION="Basic abc").status_code == 401
        assert Client().get(
            _URL, HTTP_AUTHORIZATION=f"Bearer {bearer}, Bearer {native}"
        ).status_code == 401
        assert Client().get(
            _URL, HTTP_AUTHORIZATION="bearer " + bearer
        ).status_code in (200, 401)
    # This test-only URL is NEVER available in the real URLconf.
    assert Client().get(_URL, HTTP_AUTHORIZATION=f"Bearer {bearer}").status_code == 404


def test_c6_mixed_django_session_cookie_and_family_token_never_falls_back():
    user_a = _new_user("account-a")
    user_b = _new_user("account-b")
    _, _, bearer_a = _issue(user_a)
    _, _, bearer_b = _issue(user_b)
    browser = Client()
    browser.force_login(user_b)
    assert settings.SESSION_COOKIE_NAME in browser.cookies

    with override_settings(ROOT_URLCONF=__name__):
        assert _get(bearer_a, client=browser).status_code == 401
        assert _get(bearer_b, client=browser).status_code == 401
        assert _get(client=browser).status_code == 401
        assert Client().get(
            _URL,
            HTTP_AUTHORIZATION=f"Bearer {bearer_a}",
            HTTP_COOKIE=f"{settings.SESSION_COOKIE_NAME}=invalid",
        ).status_code == 401
        assert _get(bearer_a).json()["owner_id"] == user_a.pk


def test_c6_family_logout_denies_previously_valid_http_bearer_without_cross_family_logout():
    user = _new_user("two-devices")
    _, _, a = _issue(user)
    _, _, b = _issue(user)
    with override_settings(ROOT_URLCONF=__name__):
        assert _get(a).status_code == 200
        assert _get(b).status_code == 200
        revoke_one_web_family_using_bearer(a)
        assert _get(a).status_code == 401
        assert _get(b).status_code == 200
        revoke_native_tokens(user)
        assert _get(b).status_code == 401


def test_c6_disabled_flag_wins_over_valid_token_and_optional_headers():
    user = _new_user("flag")
    _, _, bearer = _issue(user)
    with (
        override_settings(ROOT_URLCONF=__name__),
        override_settings(F09_C6_HTTP_AUTH_ENABLED=False),
    ):
        assert _get(bearer).status_code == 401
    with override_settings(ROOT_URLCONF=__name__):
        response = Client().get(
            _URL,
            HTTP_X_IAMINA_BFF_PROOF="v1." + "a" * 64,
            HTTP_X_VERCEL_TRUSTED_OIDC_IDP_TOKEN="forged",
        )
        assert response.status_code == 401


def test_c6_live_clinical_and_refresh_routes_stay_unmodified():
    user = _new_user("live-401")
    _, _, bearer = _issue(user)
    assert Client().get(
        "/api/v1/logs", HTTP_AUTHORIZATION=f"Bearer {bearer}"
    ).status_code == 401
    assert Client().post(
        "/api/v1/auth/refresh", data=json.dumps({}), content_type="application/json"
    ).status_code == 404
    assert Client().get(_URL).status_code == 404
