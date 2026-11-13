"""Branch-only D1-6 HTTPS Preview. Never a clinical IAMINA settings module."""
from __future__ import annotations

import os
import re

from amina.vercel_settings import *  # noqa: F403,F401

_EXPECTED_PROJECT = "prj_hnlWE6QdXtWvYVfwe2JVAqIKPUiP"
_EXPECTED_BRANCH = "research/d1-6-safari-preview-20261113"
_host = os.environ.get("VERCEL_URL", "").strip().lower()
if (
    os.environ.get("VERCEL") != "1"
    or os.environ.get("VERCEL_ENV") != "preview"
    or os.environ.get("VERCEL_PROJECT_ID") != _EXPECTED_PROJECT
    or os.environ.get("VERCEL_GIT_COMMIT_REF") != _EXPECTED_BRANCH
    or os.environ.get("IAMINA_D1_SAFARI_LAB_ONLY") != "synthetic-preview-v1"
    or not re.fullmatch(r"[a-z0-9-]+\.vercel\.app", _host)
    or os.environ.get("IAMINA_ENV") != "development"
):
    raise RuntimeError("D1_SAFARI_PREVIEW_ENVIRONMENT_DENIED")

# All URLs, sessions, passkey registrations and PRF checks on ONE immutable
# deployment hostname. Never authenticate for a different Vercel alias.
ROOT_URLCONF = "d1_safari_preview.urls"
ALLOWED_HOSTS = [_host]
CSRF_TRUSTED_ORIGINS = ["https://" + _host]
CORS_ALLOWED_ORIGINS = ["https://" + _host]
CORS_ALLOWED_ORIGIN_REGEXES = []
CORS_ALLOW_ALL_ORIGINS = False
D1_PASSKEY_RESEARCH_ENABLED = True
D1_PASSKEY_RESEARCH_RP_ID = _host
D1_PASSKEY_RESEARCH_ORIGIN = "https://" + _host

# Only auth/session and research credential tables. The clinical API,
# diabetes app, AI app and admin are deliberately unavailable.
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "core",
    "passkey_research.apps.PasskeyResearchConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "d1_safari_preview.views.SyntheticAccountOnlyMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "d1-preview-local"}}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "d1_safari_research_session"
SESSION_COOKIE_AGE = 14400
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
DEBUG = False
ENABLE_DJANGO_ADMIN = False
MEDICAL_PILOT_MODE = False
ALLOW_DIAGNOSIS = False
ALLOW_INSULIN_ADVICE = False
LLM_MEDICAL_STREAMING = False
