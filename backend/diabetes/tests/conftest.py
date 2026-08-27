"""Scoped test policy for the dormant Firebase migration bridge.

Production and ordinary test execution keep Firebase migration disabled. Only
legacy Firebase contract classes open an explicit migration window so the
bridge remains regression-tested without weakening the default-off invariant.
"""

import pytest

_LEGACY_FIREBASE_MIGRATION_CLASSES = {
    "APIAuthTestCase",
    "APIAuthEdgeCasesTestCase",
    "LoginFlowTests",
    "FirebaseAuthEndpointTests",
}


@pytest.fixture(autouse=True)
def explicit_legacy_firebase_migration_window(request, monkeypatch):
    test_class = getattr(request.node, "cls", None)
    if test_class is not None and test_class.__name__ in _LEGACY_FIREBASE_MIGRATION_CLASSES:
        monkeypatch.setenv("ENABLE_FIREBASE_MIGRATION", "true")
