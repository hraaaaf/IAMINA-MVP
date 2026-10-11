"""Shared test setup for IAMINA authentication.

Use the real Ninja auth callbacks in integration tests. The former global
FirebaseAuth.__call__ monkeypatch also changed HybridBearerAuth because
FirebaseAuth is its compatibility alias. That disabled native Bearer auth
and silently treated session users as Bearer-authenticated in all tests.

Legacy pytest suites also rely on this file to enable test database access.
Keep that separate fixture until those tests explicitly declare django_db;
it must never alter request authentication or CSRF behavior.
"""

import pytest


@pytest.fixture(autouse=True)
def _legacy_suite_db_access(db):
    """Preserve established DB fixture scope without modifying authentication."""
    yield
