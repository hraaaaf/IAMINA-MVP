"""Shared test setup for IAMINA authentication.

Use the real Ninja auth callbacks in integration tests. The former global
FirebaseAuth.__call__ monkeypatch also changed HybridBearerAuth because
FirebaseAuth is its compatibility alias. That disabled native Bearer auth
and silently treated session users as Bearer-authenticated in all tests.

Django session-backed test clients already use the dedicated SessionAuth
callback; tests needing a synthetic identity must mock it locally.
"""
