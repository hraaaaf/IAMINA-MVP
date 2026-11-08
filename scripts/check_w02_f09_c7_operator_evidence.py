"""W02-F09-C7: validate an operator's REDACTED, read-only migration evidence.

This tool performs no network access, SQL or DDL. The operator obtains the
inventory from the *exact* new synthetic DB in a separately approved secure
admin context. Do not provide connection strings, passwords or patient rows.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DB = "iamina_w02_c7_synthetic"
OWNER = "iamina925_empty_owner"
APP = "iamina_w02_c7_preview_app"
C7 = {
    "0019_auth_abuse_bucket",
    "0020_web_refresh_candidate",
    "0021_web_refresh_transport_nonce",
}
TABLES = {
    "core_webrefreshfamily",
    "core_webrefreshconsumedsecret",
    "core_webrefreshtransportnonce",
}
FORBIDDEN = {
    "0020_erasure_attempt",
    "0021_erasure_attempt_claim_states",
    "0022_d2_preview_consent_receipt",
    "0023_d2_in_app_notice",
}
SHA = "259cc5c48ccdd0976fbe29b6bb9bb0bae6326991"
MIGRATION_NAME = re.compile(r"^\d{4}_[a-z][a-z0-9_]*$")


def validate(payload: object, stage: str) -> dict:
    errors = []
    if stage not in ("before", "after"):
        return {"status": "BLOCKED", "errors": ["unknown stage"]}
    if not isinstance(payload, dict):
        return {"status": "BLOCKED", "errors": ["invalid evidence object"]}
    fields = ("database", "role", "source_sha", "public_tables", "core_migrations",
              "c7_tables", "user_count", "profile_count")
    if any(field not in payload for field in fields):
        return {"status": "BLOCKED", "errors": ["incomplete evidence schema"]}

    if payload["database"] != DB:
        errors.append("unexpected database")
    if payload["role"] != OWNER:
        errors.append("operator must use migration owner, not runtime role")
    if payload["source_sha"] != SHA:
        errors.append("unexpected code commit")
    migrations = payload["core_migrations"]
    tables = payload["c7_tables"]
    if (
        not isinstance(migrations, list)
        or not all(isinstance(x, str) and MIGRATION_NAME.fullmatch(x) for x in migrations)
        or len(migrations) != len(set(migrations))
    ):
        errors.append("invalid migration inventory")
        migrations = []
    if not isinstance(tables, list) or not all(isinstance(x, str) for x in tables):
        errors.append("invalid C7 table inventory")
        tables = []
    if any(type(payload[x]) is not int or payload[x] < 0 for x in
           ("public_tables", "user_count", "profile_count")):
        errors.append("invalid nonnegative counts")
    elif payload["user_count"] != 0 or payload["profile_count"] != 0:
        errors.append("synthetic DB contains accounts/profiles; stop")
    if set(migrations) & FORBIDDEN:
        errors.append("divergent W01/D2 migration lineage")
    if stage == "before":
        if payload["public_tables"] != 0 or migrations or tables:
            errors.append("before-state must be completely empty")
    else:
        if payload["public_tables"] < len(TABLES):
            errors.append("post-state tables missing")
        if not C7.issubset(set(migrations)):
            errors.append("C7 Django migration chain missing")
        if set(tables) != TABLES:
            errors.append("C7 PostgreSQL table set not exact")
        if any(m.startswith("002") and m not in C7 for m in migrations):
            errors.append("unexpected post-0019 core migration")
    return {
        "status": "EVIDENCE_VALIDATED_NOT_AUTHORIZATION" if not errors else "BLOCKED",
        "stage": stage,
        "errors": sorted(set(errors)),
        "no_sql_executed_by_gate": True,
        "clinical_activation_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only offline evidence gate")
    parser.add_argument("--stage", required=True, choices=("before", "after"))
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        print(json.dumps({"status": "BLOCKED", "errors": ["invalid evidence file"]}))
        return 2
    result = validate(value, args.stage)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "EVIDENCE_VALIDATED_NOT_AUTHORIZATION" else 3


if __name__ == "__main__":
    raise SystemExit(main())
