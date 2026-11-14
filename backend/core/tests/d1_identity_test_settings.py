"""D1 identity fixture: disposable Django SQLite DB, never product settings.

Tests actual core.native_auth issuance, verification and token revocation.
Only auth/contenttypes/core are loaded; no API, Firebase, Redis or network.
"""
SECRET_KEY = "iamina-d1-native-identity-ci-test-only-not-a-real-secret"
DEBUG = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "core",
)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
MIGRATION_MODULES = {"core": None}
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)
