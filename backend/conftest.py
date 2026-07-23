"""
Test configuration: patch FirebaseAuth so force_login() works in tests.

Django Ninja's HttpBearer rejects requests without an Authorization: Bearer
header before calling authenticate(). This fixture patches __call__ so that
session-authenticated users (from force_login) bypass the Firebase token check.
"""
from unittest.mock import patch

import pytest


def _session_aware_call(self, request):
    """Accept session-authenticated users in tests; fall back to token check."""
    if request.user and request.user.is_authenticated:
        return request.user
    return None


@pytest.fixture(autouse=True)
def _patch_firebase_auth(db):
    with patch(
        "diabetes.api.v1.security.FirebaseAuth.__call__",
        new=_session_aware_call,
    ):
        yield
