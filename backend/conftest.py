"""
Test configuration: preserve legacy force_login() compatibility.

Django Ninja's HttpBearer rejects requests without Authorization. Only
cookie-only session fixtures may bypass the Bearer path: explicit native
Authorization must always execute the real backend, including rejection.
"""
from unittest.mock import patch

import pytest


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

    with patch(
        "diabetes.api.v1.security.FirebaseAuth.__call__",
        new=_session_aware_call,
    ):
        yield
