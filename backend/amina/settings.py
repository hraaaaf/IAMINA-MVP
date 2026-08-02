"""
Django settings for the amina project.
"""
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# BASE_DIR points to backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# PROJECT_ROOT points to the monorepo root (one level up)
PROJECT_ROOT = BASE_DIR.parent

# Load .env from PROJECT_ROOT explicitly
load_dotenv(PROJECT_ROOT / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
if not DEBUG and '*' in ALLOWED_HOSTS:
    raise ValueError("Wildcard ALLOWED_HOSTS not permitted in production (DEBUG=False)")

# Set to False in production to remove /admin/ surface area entirely.
# Default is False — admin must be opt-in via .env (ENABLE_DJANGO_ADMIN=True).
ENABLE_DJANGO_ADMIN = os.environ.get('ENABLE_DJANGO_ADMIN', 'False').lower() == 'true'

# LLM provider selection. False = Gemini (default). True = Kimi 2.5 (standby).
# Requires MOONSHOT_API_KEY when True. Zero-downtime switch: change + restart.
USE_KIMI_LLM = os.environ.get('USE_KIMI', 'False').lower() == 'true'
MEDICAL_PILOT_MODE = os.environ.get('MEDICAL_PILOT_MODE', 'False').lower() == 'true'
LLM_MEDICAL_STREAMING = os.environ.get('LLM_MEDICAL_STREAMING', 'False').lower() == 'true'
ALLOW_INSULIN_ADVICE = os.environ.get('ALLOW_INSULIN_ADVICE', 'False').lower() == 'true'
ALLOW_DIAGNOSIS = os.environ.get('ALLOW_DIAGNOSIS', 'False').lower() == 'true'

INSTALLED_APPS = [
    *(['django.contrib.admin'] if ENABLE_DJANGO_ADMIN else []),
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'core',
    'ai.apps.AiConfig',
    'diabetes.apps.DiabetesConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'amina.middleware.csrf_exempt_api.CsrfExemptApiMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # ── Diabetes Clinical Shield ──────────────────────────────
    # UnitGuard: normalises glucose units (mg/dL ↔ g/L ↔ mmol/L) on all API writes.
    'diabetes.middleware.unit_guard.UnitGuardMiddleware',
    # Emergency operating mode: truthfully decorates every emergency response.
    'core.middleware.emergency_operating_mode.EmergencyOperatingModeMiddleware',
    # TriageVital: detects medical emergencies in chat; bypasses LLM if triggered.
    'core.middleware.triage_vital.TriageVitalMiddleware',
]

CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True  # Flutter Web uses random ports in dev
else:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()]
    if not CORS_ALLOWED_ORIGINS:
        raise ValueError("CORS_ALLOWED_ORIGINS required in production (DEBUG=False)")

ROOT_URLCONF = 'amina.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'amina.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Default unless "remember me"

CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get(
    'CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:8000,http://localhost:8000'
).split(',') if o.strip()]

if DEBUG:
    CSRF_TRUSTED_ORIGINS += [
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

# Legacy login redirects — kept for admin; Flutter handles its own auth.
LOGIN_URL = '/admin/login/'

# ── HTTPS / security headers (production only) ────────────────
# All SECURE_* settings are no-ops when DEBUG=True (local dev).
# In production (DEBUG=False, behind TLS terminator) they are mandatory.
SECURE_SSL_REDIRECT         = not DEBUG   # redirect plain HTTP → HTTPS
SESSION_COOKIE_SECURE       = not DEBUG   # session cookie only over HTTPS
CSRF_COOKIE_SECURE          = not DEBUG   # CSRF cookie only over HTTPS
SECURE_HSTS_SECONDS         = 0 if DEBUG else 31536000   # 1 year in prod
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD         = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True       # always — prevents MIME-type sniffing
X_FRAME_OPTIONS             = 'DENY'     # always — clickjacking guard

# ── IAmina LLM Provider ──────────────────────────────────────
# Switch provider via .env — zero-downtime swap.
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'gemini')    # "gemini" | "claude" | "kimi"
LLM_MODEL = os.environ.get('LLM_MODEL', 'gemini-2.5-flash')

# Kimi (self-hosted only — GDPR)
KIMI_BASE_URL = os.environ.get('KIMI_BASE_URL', '')
KIMI_API_KEY = os.environ.get('KIMI_API_KEY', '')

# ── Redis ─────────────────────────────────────────────────────
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# ── Django Cache (django-redis, graceful fallback when Redis is down) ─────────
# IGNORE_EXCEPTIONS=True → every cache.get() returns None if Redis is unreachable,
# and cache.set() silently no-ops.  This ensures the app works in dev without Redis.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,   # graceful degradation — computes fresh on miss
        },
        "KEY_PREFIX": "amina",
        "TIMEOUT": 300,  # 5 min default TTL
    }
}
