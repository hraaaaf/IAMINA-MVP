"""
Test configuration: preserve synthetic force_login compatibility while
respecting the F08 absolute native-session cookie deadline.

Django Ninja's HttpBearer rejects requests without Authorization. Only
bounded cookie-only session fixtures may bypass the Bearer path: explicit
native Authorization always executes the real backend, including rejection.
Never patch runtime authorization in production.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.test import Client
from django.utils import timezone


@pytest.fixture(autouse=True)
def _patch_firebase_auth(db):
    """Keep legacy session tests, but exercise real Bearer authentication.

    This global fixture previously returned None for every request without a
    Django session. That silently disabled *all* native Bearer HTTP tests and
    masked clinical authorization behavior. Never bypass an explicit
    Authorization header, including an invalid/conflicting one.
    """
    from diabetes.api.v1.security import FirebaseAuth

    original_call = FirebaseAuth.__call__

    def _session_aware_call(self, request):
        user = getattr(request, "user", None)
        if "HTTP_AUTHORIZATION" not in request.META and user and user.is_authenticated:
            return user
        return original_call(self, request)

    # Legacy clinical unit tests use Client.force_login() instead of going
    # through the real native login endpoint. In TESTS ONLY, make those
    # synthetic cookies explicitly represent a fresh *bounded native login*
    # rather than a stale pre-F08 14-day cookie. Never inject this marker in
    # production; the real /auth/login is the only issuance authority there.
    #
    # Separate F08 adversarial tests intentionally clear this marker after
    # force_login to prove old unbounded cookies are rejected with HTTP 401.
    from core.native_auth import (
        NATIVE_SESSION_ISSUED_AT_KEY,
        native_token_max_age_seconds,
    )

    original_force_login = Client.force_login

    def _bounded_synthetic_force_login(self, user, backend=None):
        original_force_login(self, user, backend=backend)
        session = self.session
        now = timezone.now()
        session[NATIVE_SESSION_ISSUED_AT_KEY] = now.isoformat()
        session.set_expiry(
            now + timedelta(seconds=native_token_max_age_seconds())
        )
        session.save()

    with (
        patch(
            "diabetes.api.v1.security.FirebaseAuth.__call__",
            new=_session_aware_call,
        ),
        patch("django.test.client.Client.force_login", new=_bounded_synthetic_force_login),
    ):
        yield
