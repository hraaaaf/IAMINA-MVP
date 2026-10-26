#!/usr/bin/env python3
"""W01 GitHub Actions ONLY: actual HTTP Django + PG16, synthetic A-B-A, no Redis.

The only allowed target is loopback. Do not execute against cloud/Vercel/Neon.
No real patient information, no logged tokens or response bodies.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

import psycopg2

ORIGIN = "http://127.0.0.1:8000"
DATABASE = "postgresql://postgres:postgres@127.0.0.1:5432/iamina_w01b"
CHECKS: list[str] = []


def require(condition: bool, name: str) -> None:
    if not condition:
        raise RuntimeError("W01_FAILED_" + name)
    CHECKS.append(name)


def http(path: str, method: str = "GET", *, token: str | None = None, data: dict | None = None):
    if not path.startswith("/api/v1/") or "//" in path:
        raise ValueError("invalid fixed API path")
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    payload = None if data is None else json.dumps(data).encode("utf-8")
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(ORIGIN + path, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=18) as response:
            status = response.status
            body = response.read(524288)
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read(524288)
    try:
        parsed = json.loads(body) if body else {}
    except (ValueError, TypeError):
        parsed = {}
    return status, parsed


def count_users() -> int:
    with psycopg2.connect(DATABASE) as db, db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        return cursor.fetchone()[0]


def main() -> int:
    require(os.environ.get("IAMINA_NO_REDIS") == "true", "NO_REDIS_ENV")
    require(os.environ.get("DATABASE_URL") == DATABASE, "EPHEMERAL_PG16_ONLY")
    require(urlparse(ORIGIN).hostname == "127.0.0.1", "LOOPBACK_ONLY")
    require(count_users() == 0, "INITIAL_EMPTY_DB")
    users = {}
    cleanup = {"A": "not_created", "B": "not_created"}
    suffix = secrets.token_hex(7)
    try:
        for label in ("A", "B"):
            email = f"w01-{label.lower()}-{suffix}@example.invalid"
            password = "W01!Synthetic-" + secrets.token_hex(16)
            # No credentials ever printed to the workflow log.
            status, body = http("/api/v1/auth/register", "POST", data={
                "email": email, "password": password,
                "first_name": "Synthetic", "last_name": label,
            })
            require(status == 200, f"{label}_REGISTER")
            bearer = body.get("access_token")
            user = body.get("user", {})
            require(isinstance(bearer, str) and bearer.startswith("iamina.") and
                    isinstance(user.get("id"), int), f"{label}_TOKEN")
            users[label] = {"email": email, "password": password, "token": bearer,
                            "id": user["id"]}
            cleanup[label] = "pending"
        require(count_users() == 2, "TWO_ACCOUNTS_EXIST")
        require(users["A"]["id"] != users["B"]["id"], "UNIQUE_ID")
        status, _ = http("/api/v1/auth/me", token="iamina.invalid.token")
        require(status in (401, 403), "INVALID_BEARER_DENIED")
        for label in ("A", "B", "A"):
            status, body = http("/api/v1/auth/me", token=users[label]["token"])
            require(status == 200 and body.get("id") == users[label]["id"],
                    f"{label}_AUTH_SCOPE")
        status, _ = http("/api/v1/auth/logout", "POST", token=users["A"]["token"])
        require(status == 200, "A_LOGOUT")
        status, _ = http("/api/v1/auth/me", token=users["A"]["token"])
        require(status in (401, 403), "A_REVOKED")
        status, body = http("/api/v1/auth/me", token=users["B"]["token"])
        require(status == 200 and body.get("id") == users["B"]["id"],
                "B_UNAFFECTED_BY_A_LOGOUT")
        status, body = http("/api/v1/auth/login", "POST", data={
            "email": users["A"]["email"], "password": users["A"]["password"]
        })
        require(status == 200 and body.get("user", {}).get("id") == users["A"]["id"],
                "A_RELOGIN")
        users["A"]["token"] = body["access_token"]
        require(count_users() == 2, "NO_UNEXPECTED_USERS")
    finally:
        # Always attempt app-level cleanup. NEVER use a direct SQL DELETE here.
        for label in ("A", "B"):
            u = users.get(label)
            if not u:
                continue
            try:
                status, _ = http("/api/v1/account", "DELETE", token=u["token"],
                                 data={"confirm": "DELETE MY ACCOUNT"})
                cleanup[label] = "api_delete_reported" if status == 200 else "api_delete_failed"
            except Exception:
                cleanup[label] = "api_delete_failed"
    require(cleanup["A"] == "api_delete_reported" and
            cleanup["B"] == "api_delete_reported", "APP_ERASURE")
    require(count_users() == 0, "INDEPENDENT_PG16_ZERO_USERS")
    print(json.dumps({"result": "PASS", "proof": "synthetic local Django HTTP / PostgreSQL 16",
                      "no_redis": True, "checks": CHECKS,
                      "cleanup": cleanup, "auth_user_count": 0,
                      "out_of_scope": ["hosted_SSO", "hosted_Neon", "network_IP_429", "Pulper_pending_enabled"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Never disclose email/password/Bearer, SQL details or response bodies.
        print("W01 E2E FAIL " + type(exc).__name__ + ": " +
              (str(exc) if str(exc).startswith("W01_FAILED_") else "internal"), file=sys.stderr)
        raise SystemExit(1) from exc
