"""W01/G7: all patient-facing protected routers enforce Bearer and session auth.

The logs route needed operation-level auth after mount-only auth failed in the
real PG16 HTTP test. Check the full protected router surface instead of
assuming mount-time auth automatically covers every operation.

This is a structural contract; it does not replace per-patient HTTP/IDOR tests.
"""

import pytest

from amina.vercel_session_auth import SessionAuth
from core.registry import ModuleRegistry
from diabetes.api import main as api_main
from diabetes.api.v1.security import HybridBearerAuth


PROTECTED_ROUTERS = (
    ("logs", api_main.logs_router),
    ("profile", api_main.profile_router),
    ("locale", api_main.locale_router),
    ("kpis", api_main.kpis_router),
    ("personal_response", api_main.personal_response_router),
    ("proactive", api_main.proactive_router),
    ("companion", api_main.companion_router),
    ("cgm", api_main.cgm_router),
    ("account", api_main.account_router),
    ("modules", api_main.modules_router),
    ("imports", api_main.imports_router),
    ("documents", api_main.documents_router),
    ("ai", api_main.ai_router),
    ("voice", api_main.voice_router),
    ("analytics", api_main.analytics_router),
)


@pytest.mark.django_db
def test_w01_all_explicit_protected_routes_have_bearer_and_session_auth():
    checked = 0
    errors = []
    for label, router in PROTECTED_ROUTERS:
        operations = [
            operation
            for path_view in router.path_operations.values()
            for operation in path_view.operations
        ]
        if not operations:
            errors.append(f"{label}: empty protected router")
        for operation in operations:
            checked += 1
            callbacks = operation.auth_callbacks or ()
            types = tuple(type(callback).__name__ for callback in callbacks)
            if not any(isinstance(x, HybridBearerAuth) for x in callbacks) or not any(
                isinstance(x, SessionAuth) for x in callbacks
            ):
                errors.append(f"{label}/{operation.path}: auth={types}")
    assert checked >= 15, "Protected route inventory unexpectedly empty"
    assert not errors, "Unprotected operation(s): " + "; ".join(errors)


@pytest.mark.django_db
def test_w01_all_registry_module_routes_have_bearer_and_session_auth():
    checked = 0
    errors = []
    for module in ModuleRegistry.all():
        operations = [
            operation
            for path_view in module.router.path_operations.values()
            for operation in path_view.operations
        ]
        for operation in operations:
            checked += 1
            callbacks = operation.auth_callbacks or ()
            types = tuple(type(callback).__name__ for callback in callbacks)
            if not any(isinstance(x, HybridBearerAuth) for x in callbacks) or not any(
                isinstance(x, SessionAuth) for x in callbacks
            ):
                errors.append(f"{module.manifest.name}/{operation.path}: auth={types}")
    assert checked > 0, "Registry-backed route inventory unexpectedly empty"
    assert not errors, "Unprotected registry operation(s): " + "; ".join(errors)
