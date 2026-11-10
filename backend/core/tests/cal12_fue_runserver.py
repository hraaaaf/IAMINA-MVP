"""Launch CAL-12 fixture-only Django on loopback and disposable PG16.

No production URLConf is modified. Fails closed if pointed at remote DB.
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse


def main():
    if os.environ.get("CAL12_FUE_TEST_ONLY") != "1":
        raise RuntimeError("Explicit synthetic FUE gate required")
    database = urlparse(os.environ.get("DATABASE_URL", ""))
    if (
        database.scheme not in ("postgres", "postgresql")
        or database.hostname not in ("127.0.0.1", "localhost")
        or database.path != "/iamina_cal12_fue"
    ):
        raise RuntimeError("CAL12 FUE permits only disposable loopback PG database")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amina.settings")
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    import django
    django.setup()
    from django.conf import settings
    from django.core.management import execute_from_command_line
    from django.db import connection

    if not settings.DEBUG or connection.vendor != "postgresql":
        raise RuntimeError("CAL12 FUE requires DEBUG and test PostgreSQL")
    if any(host not in ("localhost", "127.0.0.1") for host in settings.ALLOWED_HOSTS):
        raise RuntimeError("CAL12 FUE must be restricted to loopback hosts")

    settings.CAL12_SYNTHETIC_EXPORT_LEDGER_ENABLED = True
    settings.ROOT_URLCONF = "core.tests.cal12_fue_urls"
    execute_from_command_line([
        "manage.py", "runserver", "127.0.0.1:8000", "--noreload",
    ])


if __name__ == "__main__":
    main()
