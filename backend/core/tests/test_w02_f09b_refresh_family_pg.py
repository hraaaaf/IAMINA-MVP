"""W02-F09-B RED-first: non-exposed Web refresh family, PostgreSQL source-of-truth.

All credentials are random test-only bytes. NO HTTP refresh endpoint, client
cookie, Vercel deployment or patient data. Durations are test-policy fixtures,
not approved clinical expiry limits. SQLite exercises functional rules;
the adversarial transaction race runs on isolated PostgreSQL 16.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.db import close_old_connections, connection
from django.test import Client, override_settings
from django.utils import timezone

from core.models import BasePatientProfile, WebRefreshConsumedSecret, WebRefreshFamily
from core.native_auth import NativeTokenError, issue_native_token, verify_native_token
from core.web_refresh_protocol import (
    WebRefreshRejected,
    issue_web_refresh_family,
    rotate_web_refresh_family,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def _test_only_candidate_policy(settings):
    """Representative bounded fixture values, never production defaults."""
    settings.F09_WEB_REFRESH_ENABLED = True
    settings.F09_WEB_REFRESH_IDLE_SECONDS = 120
    settings.F09_WEB_REFRESH_ABSOLUTE_SECONDS = 540


def _patient(suffix):
    user = User.objects.create_user(
        username=f"f09b-{suffix}",
        email=f"f09b-{suffix}@example.invalid",
        password="Synthetic-only-Web-Refresh-2026!",
    )
    BasePatientProfile.objects.get_or_create(patient=user)
    return user


def test_f09b_disabled_by_default_cannot_mint_or_rotate_even_with_policy():
    user = _patient("feature-disabled")
    with override_settings(F09_WEB_REFRESH_ENABLED=False):
        with pytest.raises(WebRefreshRejected):
            issue_web_refresh_family(user)
    assert not WebRefreshFamily.objects.exists()


@pytest.mark.parametrize(
    ("idle", "absolute"),
    [(None, 540), (120, None), (False, 540), (120, "540"), (0, 540), (120, -1)],
)
def test_f09b_invalid_or_missing_expiry_policy_fails_closed(idle, absolute):
    user = _patient(f"bad-policy-{str(idle)}-{str(absolute)}".replace(" ", "")[:38])
    with override_settings(
        F09_WEB_REFRESH_IDLE_SECONDS=idle,
        F09_WEB_REFRESH_ABSOLUTE_SECONDS=absolute,
    ):
        with pytest.raises(WebRefreshRejected):
            issue_web_refresh_family(user)
    assert not WebRefreshFamily.objects.exists()


def test_f09b_secret_is_unpredictable_not_saved_in_plaintext_and_bounded():
    user = _patient("hash-storage")
    family, secret = issue_web_refresh_family(user)
    assert secret.startswith("iamina-wr1.")
    assert len(secret) > 60
    assert family.user_id == user.pk
    assert family.revoke_at is None
    assert family.current_digest != secret
    assert len(family.current_digest) == 64
    assert family.current_digest.isascii()
    assert family.expires_at == family.issued_at + timedelta(seconds=540)
    assert family.idle_deadline == family.issued_at + timedelta(seconds=120)
    assert WebRefreshConsumedSecret.objects.count() == 0
    assert secret not in repr(family.__dict__)


def test_f09b_one_rotation_changes_secret_and_preserves_absolute_deadline():
    user = _patient("rotate")
    family, first = issue_web_refresh_family(user)
    original_absolute = family.expires_at
    later = timezone.now() + timedelta(seconds=30)
    with patch("core.web_refresh_protocol.timezone.now", return_value=later):
        new = rotate_web_refresh_family(first)
    assert new != first
    family.refresh_from_db()
    assert family.expires_at == original_absolute
    assert family.last_rotated_at == later
    assert family.idle_deadline == later + timedelta(seconds=120)
    assert family.current_digest != first
    assert WebRefreshConsumedSecret.objects.filter(family=family).count() == 1
    assert all(first not in str(s.__dict__) for s in WebRefreshConsumedSecret.objects.all())
    assert not WebRefreshFamily.objects.filter(current_digest=first).exists()


def test_f09b_reused_spent_secret_revokes_family_and_existing_account_bearers():
    user = _patient("replay")
    stale_bearer = issue_native_token(user)
    family, old = issue_web_refresh_family(user)
    replacement = rotate_web_refresh_family(old)
    assert verify_native_token(stale_bearer).pk == user.pk
    with pytest.raises(WebRefreshRejected):
        rotate_web_refresh_family(old)
    family.refresh_from_db()
    assert family.revoke_at is not None
    with pytest.raises(WebRefreshRejected):
        rotate_web_refresh_family(replacement)
    with pytest.raises(NativeTokenError):
        verify_native_token(stale_bearer)


def test_f09b_invalid_guess_does_not_revoke_another_family():
    a = _patient("unknown-a")
    b = _patient("unknown-b")
    fam_a, secret_a = issue_web_refresh_family(a)
    fam_b, secret_b = issue_web_refresh_family(b)
    with pytest.raises(WebRefreshRejected):
        rotate_web_refresh_family("iamina-wr1." + "A" * 64)
    fam_a.refresh_from_db()
    fam_b.refresh_from_db()
    assert fam_a.revoke_at is None
    assert fam_b.revoke_at is None
    assert rotate_web_refresh_family(secret_a).startswith("iamina-wr1.")
    assert rotate_web_refresh_family(secret_b).startswith("iamina-wr1.")


def test_f09b_spent_secret_replay_revokes_only_the_affected_patient():
    a = _patient("isolated-a")
    b = _patient("isolated-b")
    bearer_b = issue_native_token(b)
    fam_a, old_a = issue_web_refresh_family(a)
    _, token_b = issue_web_refresh_family(b)
    rotate_web_refresh_family(old_a)
    with pytest.raises(WebRefreshRejected):
        rotate_web_refresh_family(old_a)
    fam_a.refresh_from_db()
    assert fam_a.revoke_at is not None
    assert verify_native_token(bearer_b).pk == b.pk
    assert rotate_web_refresh_family(token_b).startswith("iamina-wr1.")


def test_f09b_idle_and_absolute_expiry_are_independently_enforced():
    user = _patient("clock-idle")
    start = timezone.now()
    with patch("core.web_refresh_protocol.timezone.now", return_value=start):
        fam, old = issue_web_refresh_family(user)
    with patch(
        "core.web_refresh_protocol.timezone.now",
        return_value=start + timedelta(seconds=121),
    ):
        with pytest.raises(WebRefreshRejected):
            rotate_web_refresh_family(old)
    fam.refresh_from_db()
    assert fam.revoke_at is not None

    other = _patient("clock-absolute")
    with override_settings(F09_WEB_REFRESH_IDLE_SECONDS=450):
        with patch("core.web_refresh_protocol.timezone.now", return_value=start):
            fam, old = issue_web_refresh_family(other)
        with patch(
            "core.web_refresh_protocol.timezone.now",
            return_value=start + timedelta(seconds=400),
        ):
            new = rotate_web_refresh_family(old)
        with patch(
            "core.web_refresh_protocol.timezone.now",
            return_value=start + timedelta(seconds=541),
        ):
            with pytest.raises(WebRefreshRejected):
                rotate_web_refresh_family(new)
    fam.refresh_from_db()
    assert fam.revoke_at is not None


def test_f09b_runtime_shortening_limits_existing_refresh_family():
    user = _patient("shortening")
    start = timezone.now()
    with patch("core.web_refresh_protocol.timezone.now", return_value=start):
        fam, old = issue_web_refresh_family(user)
    with (
        override_settings(F09_WEB_REFRESH_IDLE_SECONDS=30),
        patch(
            "core.web_refresh_protocol.timezone.now",
            return_value=start + timedelta(seconds=45),
        ),
    ):
        with pytest.raises(WebRefreshRejected):
            rotate_web_refresh_family(old)
    fam.refresh_from_db()
    assert fam.revoke_at is not None


def test_f09b_logout_or_password_change_global_version_blocks_refresh():
    user = _patient("account-revoke")
    fam, old = issue_web_refresh_family(user)
    profile = BasePatientProfile.objects.get(patient=user)
    profile.auth_token_version += 1
    profile.save(update_fields=["auth_token_version"])
    with pytest.raises(WebRefreshRejected):
        rotate_web_refresh_family(old)
    fam.refresh_from_db()
    assert fam.revoke_at is not None


def test_f09b_inactive_account_never_renews():
    user = _patient("inactive")
    fam, old = issue_web_refresh_family(user)
    user.is_active = False
    user.save(update_fields=["is_active"])
    with pytest.raises(WebRefreshRejected):
        rotate_web_refresh_family(old)
    fam.refresh_from_db()
    assert fam.revoke_at is not None


def test_f09b_invalid_secret_format_is_rejected_without_leaking_details():
    user = _patient("invalid-format")
    issue_web_refresh_family(user)
    for value in (None, "", "iamina-wr1.", "iamina-wr1.A", "iamina." + "A" * 64, 12):
        with pytest.raises(WebRefreshRejected) as exc:
            rotate_web_refresh_family(value)
        assert "iamina-wr1." not in str(exc.value)


def test_f09b_has_no_live_http_refresh_route_or_automatic_cookie_issuance():
    response = Client().post("/api/v1/auth/refresh", data="{}", content_type="application/json")
    assert response.status_code == 404
    assert "set-cookie" not in {x.lower() for x in response.headers.keys()}
    assert not WebRefreshFamily.objects.exists()


@pytest.mark.skipif(connection.vendor != "postgresql", reason="Row-lock contention requires PostgreSQL")
def test_f09b_concurrent_rotation_one_winner_and_replay_revokes_family():
    user = _patient("pg-concurrency")
    old_bearer = issue_native_token(user)
    fam, old = issue_web_refresh_family(user)
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                return ("rotated", rotate_web_refresh_family(old))
            except WebRefreshRejected:
                return ("rejected", None)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: worker(), range(2)))
    assert sorted(x[0] for x in outcomes) == ["rejected", "rotated"]
    fam.refresh_from_db()
    assert fam.revoke_at is not None
    with pytest.raises(NativeTokenError):
        verify_native_token(old_bearer)
    with pytest.raises(WebRefreshRejected):
        rotate_web_refresh_family(next(x[1] for x in outcomes if x[1]))
