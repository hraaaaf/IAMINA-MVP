"""Vercel-specific production settings for IAMINA backend."""
from __future__ import annotations

import os
from urllib.parse import urlparse

import dj_database_url

from .middleware.vercel_csrf import IAMINA_FRONTEND_STABLE_ORIGIN
from .settings import *  # noqa: F403,F401
from .vercel_environment import is_vercel_production

if DEBUG:  # noqa: F405
    raise ValueError("IAMINA Vercel backend requires DEBUG=False")

_database_url = os.environ.get("DATABASE_URL", "").strip()
if not _database_url:
    raise ValueError("DATABASE_URL is required on Vercel; SQLite fallback is forbidden")

_database_scheme = urlparse(_database_url).scheme.lower()
if _database_scheme not in {"postgres", "postgresql"}:
    raise ValueError("IAMINA Vercel backend requires PostgreSQL DATABASE_URL")

DATABASES = {  # noqa: F405
    "default": dj_database_url.parse(
        _database_url,
        conn_max_age=0,
    )
}


def _require_https_origins(name: str, origins: list[str]) -> None:
    if not origins:
        raise ValueError(f"{name} is required on Vercel")
    invalid = [
        origin
        for origin in origins
        if (parsed := urlparse(origin)).scheme != "https" or not parsed.netloc
    ]
    if invalid:
        raise ValueError(f"{name} must contain only valid HTTPS origins on Vercel")


# The stable frontend alias is always trusted. Deployment/preview hostnames are
# handled by narrow project/account-specific regex policy below; never trust
# all of ``*.vercel.app``.
if IAMINA_FRONTEND_STABLE_ORIGIN not in CORS_ALLOWED_ORIGINS:  # noqa: F405
    CORS_ALLOWED_ORIGINS.append(IAMINA_FRONTEND_STABLE_ORIGIN)  # noqa: F405
if IAMINA_FRONTEND_STABLE_ORIGIN not in CSRF_TRUSTED_ORIGINS:  # noqa: F405
    CSRF_TRUSTED_ORIGINS.append(IAMINA_FRONTEND_STABLE_ORIGIN)  # noqa: F405

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://iamina-review-[a-z0-9-]+-achraf-benmoussa-s-projects\.vercel\.app$",
]

_csrf_middleware = "django.middleware.csrf.CsrfViewMiddleware"
_vercel_csrf_middleware = "amina.middleware.vercel_csrf.IaminaVercelCsrfViewMiddleware"
MIDDLEWARE = [
    _vercel_csrf_middleware if item == _csrf_middleware else item
    for item in MIDDLEWARE  # noqa: F405
]
if _vercel_csrf_middleware not in MIDDLEWARE:
    raise ValueError("Django CSRF middleware is missing from IAMINA Vercel settings")

_require_https_origins("CORS_ALLOWED_ORIGINS", CORS_ALLOWED_ORIGINS)  # noqa: F405
_require_https_origins("CSRF_TRUSTED_ORIGINS", CSRF_TRUSTED_ORIGINS)  # noqa: F405

# The shared Vercel app is a hosted dev/test runtime. Keep patient text local
# unless a dedicated dev provider is explicitly selected and independently
# passes the processor-policy gate. This prevents the base Gemini default from
# attempting external patient-data egress during ordinary hosted testing.
if not is_vercel_production():
    LLM_PROVIDER = (
        os.environ.get("IAMINA_DEV_LLM_PROVIDER", "fallback").strip().lower()
        or "fallback"
    )

# Native password recovery is a production capability, so its delivery path
# must be explicit in production. Preview deployments intentionally do not need
# SMTP secrets just to boot and exercise unrelated integration paths.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "").strip()
EMAIL_HOST = os.environ.get("EMAIL_HOST", "").strip()
_email_port = os.environ.get("EMAIL_PORT", "").strip()
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "").strip()
PASSWORD_RESET_FRONTEND_URL = os.environ.get(
    "PASSWORD_RESET_FRONTEND_URL",
    "",
).strip()
EMAIL_USE_TLS = (
    os.environ.get("EMAIL_USE_TLS", "True").strip().lower() == "true"
)
EMAIL_USE_SSL = (
    os.environ.get("EMAIL_USE_SSL", "False").strip().lower() == "true"
)
EMAIL_TIMEOUT = 10

if is_vercel_production():
    if EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
        raise ValueError("IAMINA Vercel backend requires SMTP EMAIL_BACKEND")

    _required_email_settings = {
        "EMAIL_HOST": EMAIL_HOST,
        "EMAIL_PORT": _email_port,
        "EMAIL_HOST_USER": EMAIL_HOST_USER,
        "EMAIL_HOST_PASSWORD": EMAIL_HOST_PASSWORD,
        "DEFAULT_FROM_EMAIL": DEFAULT_FROM_EMAIL,
        "PASSWORD_RESET_FRONTEND_URL": PASSWORD_RESET_FRONTEND_URL,
    }
    _missing_email_settings = [
        name for name, value in _required_email_settings.items() if not value
    ]
    if _missing_email_settings:
        raise ValueError(
            "IAMINA Vercel password recovery requires: "
            + ", ".join(sorted(_missing_email_settings))
        )

    try:
        EMAIL_PORT = int(_email_port)
    except ValueError as exc:
        raise ValueError("EMAIL_PORT must be an integer") from exc
    if not 1 <= EMAIL_PORT <= 65535:
        raise ValueError("EMAIL_PORT must be between 1 and 65535")

    if EMAIL_USE_TLS == EMAIL_USE_SSL:
        raise ValueError("Exactly one of EMAIL_USE_TLS or EMAIL_USE_SSL must be enabled")

    if "@" not in DEFAULT_FROM_EMAIL:
        raise ValueError("DEFAULT_FROM_EMAIL must be a valid email-like address")

    _reset_url = urlparse(PASSWORD_RESET_FRONTEND_URL)
    if _reset_url.scheme not in {"https", "iamina"} or not (
        _reset_url.netloc or _reset_url.path
    ):
        raise ValueError("PASSWORD_RESET_FRONTEND_URL must use https:// or iamina://")

# Vercel terminates TLS before invoking the Django function.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Admit only the deployment host Vercel exposes for this exact deployment.
_vercel_url = os.environ.get("VERCEL_URL", "").strip().lower()
if _vercel_url:
    if not _vercel_url.endswith(".vercel.app"):
        raise ValueError("Unexpected VERCEL_URL host")
    if _vercel_url not in ALLOWED_HOSTS:  # noqa: F405
        ALLOWED_HOSTS.append(_vercel_url)  # noqa: F405

# The stable production alias remains explicit through ALLOWED_HOSTS env.
