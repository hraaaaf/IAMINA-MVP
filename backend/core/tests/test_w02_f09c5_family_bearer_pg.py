"""W02-F09-C5: isolated family-bound access bearer and revocation oracles.

PostgreSQL16 disposable accounts and clocks only. No mounted HTTP endpoint,
cookie emission, hosted Vercel/OIDC token or production key. The existing
native bearer remains a different, independent clinical auth namespace.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.db import close_old_connections, connection
from django.test import Client, override_settings
from django.utils import timezone

from core.models import BasePatientProfile, WebRefreshFamily
from core.native_auth import (
    NativeTokenError,
    issue_native_token,
    revoke_native_tokens,
    verify_native_token,
)
from core.web_refresh_c5_family_bearer import (
    WebFamilyBearerRejected,
    issue_family_bound_web_bearer,
    revoke_one_web_family_using_bearer,
    verify_family_bound_web_bearer,
)
from core.web_refresh_protocol import issue_web_refresh_family, rotate_web_refresh_family

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def _policy(settings):
    settings.F09_C5_FAMILY_ACCESS_ENABLED = True
    settings.F09_C5_ACCESS_MAX_AGE_SECONDS = 60
    settings.F09_WEB_REFRESH_ENABLED = True
    settings.F09_WEB_REFRESH_IDLE_SECONDS = 120
    settings.F09_WEB_REFRESH_ABSOLUTE_SECONDS = 540


def _session(suffix, user=None):
    if user is None:
        user = User.objects.create_user(
            username="c5-" + suffix,
            password="Synthetic-C5-Only-2026!",
        )
        BasePatientProfile.objects.get_or_create(patient=user)
    family, secret = issue_web_refresh_family(user)
    return user, family, secret


def test_c5_disabled_by_default_even_if_current_family_secret_is_valid():
    _, family, raw = _session("flag")
    with override_settings(F09_C5_FAMILY_ACCESS_ENABLED=False):
        with pytest.raises(WebFamilyBearerRejected):
            issue_family_bound_web_bearer(family.pk, raw)
    assert family.revoke_at is None


@pytest.mark.parametrize("max_age", [None, False, True, 0, -1, "60", 901])
def test_c5_invalid_or_unapproved_access_ttl_fails_closed(max_age):
    _, family, raw = _session("ttl-" + str(max_age))
    with override_settings(F09_C5_ACCESS_MAX_AGE_SECONDS=max_age):
        with pytest.raises(WebFamilyBearerRejected):
            issue_family_bound_web_bearer(family.pk, raw)


def test_c5_valid_bearer_binds_to_family_and_native_auth_never_accepts_it():
    user, family, secret = _session("valid")
    bearer = issue_family_bound_web_bearer(family.pk, secret)
    assert bearer.startswith("iamina-web.")
    assert verify_family_bound_web_bearer(bearer).pk == user.pk
    with pytest.raises(NativeTokenError):
        verify_native_token(bearer)
    assert Client().get(
        "/api/v1/logs", HTTP_AUTHORIZATION="Bearer " + bearer,
    ).status_code == 401
    assert Client().post(
        "/api/v1/auth/refresh", data="{}", content_type="application/json",
    ).status_code == 404


def test_c5_wrong_family_or_spent_refresh_secret_cannot_mint_bearer():
    _, family, secret = _session("wrong")
    _, another, other_secret = _session("other")
    with pytest.raises(WebFamilyBearerRejected):
        issue_family_bound_web_bearer(another.pk, secret)
    with pytest.raises(WebFamilyBearerRejected):
        issue_family_bound_web_bearer(999999999, secret)
    replacement = rotate_web_refresh_family(secret)
    with pytest.raises(WebFamilyBearerRejected):
        issue_family_bound_web_bearer(family.pk, secret)
    assert issue_family_bound_web_bearer(family.pk, replacement).startswith(
        "iamina-web."
    )
    assert issue_family_bound_web_bearer(another.pk, other_secret).startswith(
        "iamina-web."
    )


def test_c5_logout_one_family_revokes_its_bearers_and_refresh_only():
    user, family_a, raw_a = _session("a")
    _, family_b, raw_b = _session("b", user=user)
    bearer_a1 = issue_family_bound_web_bearer(family_a.pk, raw_a)
    bearer_a2 = issue_family_bound_web_bearer(family_a.pk, raw_a)
    bearer_b = issue_family_bound_web_bearer(family_b.pk, raw_b)
    ordinary_native = issue_native_token(user)

    revoke_one_web_family_using_bearer(bearer_a1)
    family_a.refresh_from_db()
    family_b.refresh_from_db()
    assert family_a.revoke_at is not None
    assert family_b.revoke_at is None
    for value in [bearer_a1, bearer_a2]:
        with pytest.raises(WebFamilyBearerRejected):
            verify_family_bound_web_bearer(value)
    with pytest.raises(WebFamilyBearerRejected):
        issue_family_bound_web_bearer(family_a.pk, raw_a)
    with pytest.raises(WebFamilyBearerRejected):
        revoke_one_web_family_using_bearer(bearer_a1)
    assert verify_family_bound_web_bearer(bearer_b).pk == user.pk
    assert verify_native_token(ordinary_native).pk == user.pk


def test_c5_account_global_revocation_invalidates_all_family_bearers():
    user, family_a, raw_a = _session("account")
    _, family_b, raw_b = _session("account-b", user=user)
    bearer_a = issue_family_bound_web_bearer(family_a.pk, raw_a)
    bearer_b = issue_family_bound_web_bearer(family_b.pk, raw_b)
    revoke_native_tokens(user)
    for bearer in [bearer_a, bearer_b]:
        with pytest.raises(WebFamilyBearerRejected):
            verify_family_bound_web_bearer(bearer)
    with pytest.raises(WebFamilyBearerRejected):
        issue_family_bound_web_bearer(family_a.pk, raw_a)


def test_c5_tampering_wrong_namespace_and_inactive_identity_are_denied():
    user, family, raw = _session("tamper")
    token = issue_family_bound_web_bearer(family.pk, raw)
    for candidate in [
        token + "A", "iamina." + token, "", None,
        "iamina-web.invalid", 123,
    ]:
        with pytest.raises(WebFamilyBearerRejected):
            verify_family_bound_web_bearer(candidate)
    user.is_active = False
    user.save(update_fields=["is_active"])
    with pytest.raises(WebFamilyBearerRejected):
        verify_family_bound_web_bearer(token)
    with pytest.raises(WebFamilyBearerRejected):
        issue_family_bound_web_bearer(family.pk, raw)


def test_c5_idle_and_absolute_family_windows_block_still_signed_bearer():
    _, family, raw = _session("idle")
    bearer = issue_family_bound_web_bearer(family.pk, raw)
    after_idle = family.issued_at + timedelta(seconds=130)
    with patch(
        "core.web_refresh_c5_family_bearer.timezone.now",
        return_value=after_idle,
    ):
        with pytest.raises(WebFamilyBearerRejected):
            verify_family_bound_web_bearer(bearer)

    _, family_b, raw_b = _session("absolute")
    token_b = issue_family_bound_web_bearer(family_b.pk, raw_b)
    after_absolute = family_b.issued_at + timedelta(seconds=550)
    with (
        override_settings(F09_WEB_REFRESH_IDLE_SECONDS=550,
                          F09_WEB_REFRESH_ABSOLUTE_SECONDS=600),
        patch("core.web_refresh_c5_family_bearer.timezone.now",
              return_value=after_absolute),
    ):
        with pytest.raises(WebFamilyBearerRejected):
            verify_family_bound_web_bearer(token_b)


def test_c5_access_token_short_age_enforced_even_with_live_family():
    user, family, raw = _session("bearer-age")
    token = issue_family_bound_web_bearer(family.pk, raw)
    assert verify_family_bound_web_bearer(token).pk == user.pk
    with patch("django.core.signing.time.time", return_value=time.time() + 70):
        with pytest.raises(WebFamilyBearerRejected):
            verify_family_bound_web_bearer(token)


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PG16 row-lock race")
def test_c5_concurrent_issuance_and_logout_never_leave_live_bearer():
    _, family, raw = _session("race")
    existing = issue_family_bound_web_bearer(family.pk, raw)
    barrier = Barrier(2)

    def worker(kind):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                if kind == "issue":
                    return issue_family_bound_web_bearer(family.pk, raw)
                revoke_one_web_family_using_bearer(existing)
                return None
            except WebFamilyBearerRejected:
                return None
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(worker, ["issue", "logout"]))

    family.refresh_from_db()
    assert family.revoke_at is not None
    for possible_token in [existing, outcomes[0]]:
        if possible_token:
            with pytest.raises(WebFamilyBearerRejected):
                verify_family_bound_web_bearer(possible_token)
