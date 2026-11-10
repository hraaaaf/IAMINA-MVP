"""Seed only fictitious identities in disposable local PostgreSQL for CAL-12."""
import os
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection

LANGUAGES = ("fr", "ar")
WIDTHS = (390, 768, 1280)


def seed():
    url = urlparse(os.environ.get("DATABASE_URL", ""))
    password = os.environ.get("CAL12_FUE_PASSWORD", "")
    if (
        os.environ.get("CAL12_FUE_TEST_ONLY") != "1"
        or url.hostname not in ("localhost", "127.0.0.1")
        or url.path != "/iamina_cal12_fue"
        or connection.vendor != "postgresql"
        or not settings.DEBUG
        or len(password) < 30
    ):
        raise RuntimeError("CAL12 seed requires isolated PG, synthetic password, test flag")
    if User.objects.exists():
        raise RuntimeError("CAL12 seed requires fresh disposable database")
    for locale in LANGUAGES:
        for width in WIDTHS:
            for actor in ("a", "b"):
                name = "cal12-fixture-" + actor + "-" + locale + "-" + str(width)
                User.objects.create_user(
                    username=name,
                    email=name + "@example.invalid",
                    password=password,
                )
    assert User.objects.count() == 12
    print("CAL12_SYNTHETIC_USERS=12 ZERO_REAL_PATIENTS=true")
