"""W02-F09-C7 isolated Neon Django migration runner.

This is an OPERATOR-EXECUTED tool, never a Vercel HTTP function and never
invoked by an untrusted CI pull request. DATABASE_URL is read ONLY from the
operator's secret environment and is never echoed, logged, sent to another
app or persisted to disk.

--plan opens a read-only DB connection and Django's read-only migrate plan.
--apply additionally requires a fresh empty database and an explicit exact
target confirmation. No production DB, existing W01 DB or patient record
is accepted. A successful schema migration is NOT a clinical/hosted E2E GO.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, unquote

BASE = Path(__file__).resolve().parents[1]
BACKEND = BASE / "backend"
NEW_DB = "iamina_w02_c7_synthetic"
MIGRATION_OWNER = "iamina925_empty_owner"
NEON_POOL_HOST = "ep-old-art-b9sy0oo4-pooler.c-7.eu-central-1.aws.neon.tech"
EXPECTED_MIGRATIONS = {
    "0020_web_refresh_candidate": "b04f79f06b4faac1109f86816a07aac26136328a05257b788acba57ea80bf5b3",
    "0021_web_refresh_transport_nonce": "8b10ca03a37d3d95a040d8d581e5790def1229c3ba1ccf7aff9023300152b65c",
}
EXPECTED_PREFIX = ("0019_auth_abuse_bucket", *EXPECTED_MIGRATIONS)


class MigrationDenied(Exception):
    """Refusal without any secret or account information."""


def validate_target(value: str) -> None:
    if not isinstance(value, str) or len(value) > 2000 or "\n" in value:
        raise MigrationDenied("C7_DENY_CONNECTION")
    try:
        u = urlsplit(value)
        opts = parse_qs(u.query, strict_parsing=True)
        valid = (
            u.scheme in {"postgresql", "postgres"}
            and unquote(u.username or "") == MIGRATION_OWNER
            and unquote(u.path) == "/" + NEW_DB
            and u.hostname == NEON_POOL_HOST
            and u.port in (None, 5432)
            and u.password is not None
            and opts.get("sslmode") == ["require"]
            and opts.get("channel_binding") == ["require"]
            and set(opts) == {"sslmode", "channel_binding"}
            and not u.fragment
        )
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise MigrationDenied("C7_DENY_CONNECTION")


def verify_source() -> None:
    migration_dir = BACKEND / "core" / "migrations"
    for name, expected_digest in EXPECTED_MIGRATIONS.items():
        target = migration_dir / (name + ".py")
        if not target.is_file():
            raise MigrationDenied("C7_DENY_MIGRATION_FILES")
        got = hashlib.sha256(target.read_bytes()).hexdigest()
        if got != expected_digest:
            raise MigrationDenied("C7_DENY_MIGRATION_SOURCE_DRIFT")
    tail = {p.stem for p in migration_dir.glob("00[2-9][0-9]_*.py")}
    if tail != set(EXPECTED_MIGRATIONS):
        raise MigrationDenied("C7_DENY_MIGRATION_GRAPH_DRIFT")


def snapshot(dsn: str, *, before: bool):
    import psycopg2  # import only in operator runtime
    with psycopg2.connect(
        dsn, connect_timeout=12,
        options="-c default_transaction_read_only=on",
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_database(), current_user,"
                "(SELECT count(*)::int FROM pg_catalog.pg_tables "
                " WHERE schemaname='public'),"
                "to_regclass('public.django_migrations') IS NOT NULL"
            )
            db, owner, count, has_migrations = cur.fetchone()
            if (db, owner) != (NEW_DB, MIGRATION_OWNER):
                raise MigrationDenied("C7_DENY_DB_IDENTITY")
            if before:
                if count != 0 or has_migrations:
                    raise MigrationDenied("C7_DENY_NOT_EMPTY")
                return {"tables": count, "migrations": False}

            if count == 0 or not has_migrations:
                raise MigrationDenied("C7_DENY_POST_MIGRATION_MISSING")
            cur.execute(
                "SELECT name FROM django_migrations "
                "WHERE app = 'core' AND name >= '0019' ORDER BY name"
            )
            core = tuple(row[0] for row in cur.fetchall())
            if core != tuple(sorted(EXPECTED_PREFIX)):
                raise MigrationDenied("C7_DENY_APPLIED_MIGRATION_GRAPH")
            cur.execute("SELECT count(*)::int FROM auth_user")
            users = cur.fetchone()[0]
            cur.execute("SELECT count(*)::int FROM core_basepatientprofile")
            profiles = cur.fetchone()[0]
            if users or profiles:
                raise MigrationDenied("C7_DENY_NON_SYNTHETIC_USER_DATA")
            return {"tables": count, "core": len(core), "users": 0, "profiles": 0}


def django_command(dsn: str, *args: str, read_only: bool, timeout: int) -> str:
    env = os.environ.copy()
    env["DATABASE_URL"] = dsn
    env["DEBUG"] = "True"
    env["ALLOWED_HOSTS"] = "localhost,127.0.0.1"
    env["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000"
    env.setdefault("SECRET_KEY", "w02-c7-migration-temporary-synthetic-no-patients")
    env["FIREBASE_CREDENTIALS_PATH"] = ""
    for name in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY"):
        env[name] = ""
    if read_only:
        env["PGOPTIONS"] = "-c default_transaction_read_only=on"
    else:
        env.pop("PGOPTIONS", None)
    completed = subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=BACKEND, env=env, capture_output=True, text=True,
        timeout=timeout, check=False,
    )
    if completed.returncode:
        # Never relay raw exception traces; some DB drivers include a DSN.
        raise MigrationDenied("C7_DENY_DJANGO_COMMAND_" + str(completed.returncode))
    return completed.stdout


def run(dsn: str, *, apply: bool, confirmation: str) -> dict:
    validate_target(dsn)
    verify_source()
    if os.environ.get("VERCEL_ENV") == "production":
        raise MigrationDenied("C7_DENY_PRODUCTION")
    if apply and (
        confirmation != NEW_DB
        or os.environ.get("IAMINA_W02_C7_MIGRATION_APPROVED") != "yes"
    ):
        raise MigrationDenied("C7_DENY_EXPLICIT_APPLY_CONFIRMATION")
    pre = snapshot(dsn, before=True)
    plan = django_command(
        dsn, "migrate", "--plan", "--database=default",
        read_only=True, timeout=90,
    )
    if (
        "core.0020_web_refresh_candidate" not in plan
        or "core.0021_web_refresh_transport_nonce" not in plan
        or "core.0020_erasure_attempt" in plan
    ):
        raise MigrationDenied("C7_DENY_UNEXPECTED_DJANGO_PLAN")
    if not apply:
        return {"status": "PLAN_VALIDATED_NO_WRITE", **pre}
    django_command(
        dsn, "migrate", "--noinput", "--database=default",
        read_only=False, timeout=240,
    )
    django_command(
        dsn, "makemigrations", "--check", "--dry-run",
        read_only=True, timeout=90,
    )
    return {"status": "MIGRATED_NEW_SYNTHETIC_DB", **snapshot(dsn, before=False)}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-target", default="")
    args = parser.parse_args()
    try:
        result = run(
            os.environ.get("DATABASE_URL", ""),
            apply=args.apply, confirmation=args.confirm_target,
        )
        print("W02_C7", result)
        return 0
    except (MigrationDenied, OSError, subprocess.TimeoutExpired):
        print("W02_C7_DENIED_OR_INCOMPLETE")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
