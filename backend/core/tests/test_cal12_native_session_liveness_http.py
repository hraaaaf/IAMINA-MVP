"""CAL-12 bearer liveness: exact Django HTTP with synthetic accounts only."""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from core.models import BasePatientProfile
from core.native_auth import issue_native_token, revoke_native_tokens

URL = "/api/v1/auth/session/verify"


def check(token=None, *, client=None, scheme="Bearer"):
    args = {}
    if token is not None:
        args["HTTP_AUTHORIZATION"] = f"{scheme} {token}"
    return (client or Client()).get(URL, **args)


@pytest.mark.django_db
def test_cal12_bearer_only_and_minimal_noncacheable_response():
    a = User.objects.create_user(username="cal12-a", email="a@example.invalid")
    BasePatientProfile.objects.get_or_create(patient=a)
    token = issue_native_token(a)
    res = check(token)
    assert res.status_code == 200, res.content[:250]
    assert res.json() == {"active": True, "account_id": a.pk}
    assert "no-store" in res["Cache-Control"]
    assert "private" in res["Cache-Control"]
    assert "Authorization" in res["Vary"]
    assert "Cookie" in res["Vary"]
    assert "email" not in res.content.decode()
    assert token not in res.content.decode()


@pytest.mark.django_db
def test_cal12_bearer_required_even_when_valid_cookie_is_present():
    a = User.objects.create_user(username="cal12-cookie-a")
    BasePatientProfile.objects.get_or_create(patient=a)
    browser = Client()
    browser.force_login(a)
    assert check(client=browser).status_code == 401
    assert check(issue_native_token(a), scheme="Basic", client=browser).status_code == 401
    assert check("wrong-header", client=browser).status_code == 401


@pytest.mark.django_db
def test_cal12_conflicting_cookie_cannot_select_another_patient():
    a = User.objects.create_user(username="cal12-a-conflict")
    b = User.objects.create_user(username="cal12-b-conflict")
    BasePatientProfile.objects.get_or_create(patient=a)
    BasePatientProfile.objects.get_or_create(patient=b)
    browser = Client()
    browser.force_login(b)
    assert check(issue_native_token(a), client=browser).status_code == 401
    assert check(issue_native_token(b), client=browser).status_code == 200


@pytest.mark.django_db
def test_cal12_token_revocation_and_a_b_a_relogin_are_checked_in_database():
    a = User.objects.create_user(username="cal12-a-revoke")
    b = User.objects.create_user(username="cal12-b-revoke")
    BasePatientProfile.objects.get_or_create(patient=a)
    BasePatientProfile.objects.get_or_create(patient=b)
    a_old = issue_native_token(a)
    b_token = issue_native_token(b)
    assert check(a_old).status_code == 200
    assert check(b_token).status_code == 200

    # Real Django revocation increments the DB token version.
    revoke_native_tokens(a)
    assert check(a_old).status_code == 401
    assert check(b_token).status_code == 200

    a_new = issue_native_token(a)
    assert check(a_new).json() == {"active": True, "account_id": a.pk}
    assert check(a_old).status_code == 401
    revoke_native_tokens(b)
    assert check(b_token).status_code == 401
    assert check(a_new).status_code == 200


@pytest.mark.django_db
def test_cal12_login_revocation_through_actual_http_logout():
    a = User.objects.create_user(username="cal12-logout", email="logout@example.invalid")
    BasePatientProfile.objects.get_or_create(patient=a)
    token = issue_native_token(a)
    assert check(token).status_code == 200
    logout = Client().post("/api/v1/auth/logout", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert logout.status_code == 200, logout.content[:250]
    assert check(token).status_code == 401
    assert check(issue_native_token(a)).status_code == 200


@pytest.mark.django_db
def test_cal12_tampered_expired_deactivated_and_invalid_bearer_denied(settings):
    a = User.objects.create_user(username="cal12-active")
    BasePatientProfile.objects.get_or_create(patient=a)
    good = issue_native_token(a)
    assert check(good + "forgery").status_code == 401
    assert check("firebase-unlinked-token").status_code == 401
    assert check(good, scheme="NotBearer").status_code == 401
    settings.NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS = -1
    assert check(good).status_code == 401
    settings.NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS = 60 * 60
    a.is_active = False
    a.save(update_fields=["is_active"])
    assert check(good).status_code == 401


@pytest.mark.django_db
def test_cal12_endpoint_is_read_only_and_cannot_accept_post():
    a = User.objects.create_user(username="cal12-method-guard")
    BasePatientProfile.objects.get_or_create(patient=a)
    bearer = issue_native_token(a)
    assert Client().post(URL, HTTP_AUTHORIZATION=f"Bearer {bearer}").status_code == 405
    assert check(bearer).status_code == 200
