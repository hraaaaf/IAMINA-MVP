"""
Diabetes Log API entry point.
"""

from ninja import NinjaAPI
from ninja.security import django_auth

from llm.errors import LLMProviderError

from .v1.security import firebase_auth_backend

# Accept Firebase Bearer (mobile/Flutter) OR Django session (web/PWA)
_auth = [firebase_auth_backend, django_auth]

# ── diabetes/ routers (capsule-shaped) ───────────────────────────────────────
# ── ai/ routers (engine-shaped — Phase 5 migration) ──────────────────────────
# NOTE: diabetes/api/v1/ai.py and voice.py are DEPRECATED (marked Phase 6 removal).
# They are no longer mounted here — ai/ routers serve the same URL paths.
from ai.api.v1.ai import router as ai_router  # noqa: E402
from ai.api.v1.voice import router as voice_router  # noqa: E402
from core.api.v1.account import router as account_router  # noqa: E402
from core.api.v1.auth import router as auth_router  # noqa: E402
from core.api.v1.health import router as health_router  # noqa: E402
from core.api.v1.locale import router as locale_router  # noqa: E402
from core.api.v1.modules import router as modules_router  # noqa: E402
from diabetes.api.v1.analytics import router as analytics_router  # noqa: E402
from diabetes.api.v1.cgm import router as cgm_router  # noqa: E402
from diabetes.api.v1.companion import router as companion_router  # noqa: E402
from diabetes.api.v1.demo import router as demo_router  # noqa: E402
from diabetes.api.v1.documents import router as documents_router  # noqa: E402
from diabetes.api.v1.imports import router as imports_router  # noqa: E402
from diabetes.api.v1.kpis import router as kpis_router  # noqa: E402
from diabetes.api.v1.logs import router as logs_router  # noqa: E402
from diabetes.api.v1.personal_response import router as personal_response_router  # noqa: E402
from diabetes.api.v1.proactive import router as proactive_router  # noqa: E402
from diabetes.api.v1.profile import router as profile_router  # noqa: E402

# Main API
api = NinjaAPI(
    title="IAmina API",
    version="1.0.0",
    description="Diabetes companion API — Flutter web/iOS/Android + 3rd party integrations",
)

_PROVIDER_ERROR_STATUS = {
    "provider_timeout": 503,
    "provider_unavailable": 503,
    "provider_quota_exceeded": 429,
    "provider_malformed_response": 502,
    "provider_internal_failure": 500,
}


@api.exception_handler(LLMProviderError)
def provider_error_handler(request, exc: LLMProviderError):
    """Expose one stable, non-sensitive provider failure contract."""
    status = _PROVIDER_ERROR_STATUS.get(exc.code, 500)
    return api.create_response(
        request,
        {
            "error": {
                "code": exc.code,
                "message": exc.safe_message,
                "retryable": exc.retryable,
            }
        },
        status=status,
    )


# v1 Public routers (no auth required)
api.add_router("/v1", auth_router)
api.add_router("/v1", demo_router)
api.add_router("/v1", health_router)

# v1 Protected routers — Bearer (mobile) OR session cookie (web/PWA)
api.add_router("/v1", logs_router, auth=_auth)
api.add_router("/v1", profile_router, auth=_auth)
api.add_router("/v1", locale_router, auth=_auth)
api.add_router("/v1", kpis_router, auth=_auth)
api.add_router("/v1", personal_response_router, auth=_auth)
api.add_router("/v1", proactive_router, auth=_auth)
api.add_router("/v1", companion_router, auth=_auth)
api.add_router("/v1", cgm_router, auth=_auth)
api.add_router("/v1", account_router, auth=_auth)
api.add_router("/v1", modules_router, auth=_auth)
api.add_router("/v1", imports_router, auth=_auth)
api.add_router("/v1", documents_router, auth=_auth)

# ── ai/ engine-shaped routes (Phase 5+) ──────────────────────────────────────
api.add_router("/v1", ai_router, auth=_auth)
api.add_router("/v1", voice_router, auth=_auth)

# ── analytics/ staff-only retention dashboard (S5 DA-03) ─────────────────────
api.add_router("/v1", analytics_router, auth=_auth)

# ── P3: Registry-driven module routes (/v1/{prefix}/...) ─────────────────────
# Old routes above remain alive until P6 (Flutter migration).
from core.registry import ModuleRegistry as _ModuleRegistry  # noqa: E402

for _mod in _ModuleRegistry.all():
    api.add_router(f"/v1{_mod.manifest.url_prefix}", _mod.router, auth=_auth)
