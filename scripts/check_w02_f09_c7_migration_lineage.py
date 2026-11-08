"""W02 F09-C7: read-only Django migration lineage guard.

Never connects to Neon and never runs DDL. The caller supplies only the
*names* of already applied `core` migrations from an independently scoped
read-only inventory. No user, patient, credential or DSN data is accepted.
Fail-closed when migration history and current source diverge.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "backend" / "core" / "migrations"
_NAME = re.compile(r"^([0-9]{4})_[a-z][a-z0-9_]*$")
_C7 = ("0020_web_refresh_candidate", "0021_web_refresh_transport_nonce")


def check_migration_lineage(
    available: set[str], applied: list[str],
) -> dict:
    """A pass is ONLY a lineage compatibility signal, never migration consent."""
    if any(not isinstance(x, str) or not _NAME.fullmatch(x) for x in applied):
        raise ValueError("invalid applied migration inventory")
    if len(applied) != len(set(applied)):
        raise ValueError("duplicate applied migration names")
    if any(not isinstance(x, str) or not _NAME.fullmatch(x) for x in available):
        raise ValueError("invalid repository migration inventory")
    current = sorted(available)
    unknown = sorted(set(applied) - available)
    numbered = {}
    for name in available:
        numbered.setdefault(name[:4], set()).add(name)
    collisions = sorted(
        name for name in unknown if name[:4] in numbered
    )
    missing_c7 = sorted(set(_C7) - available)
    # If a source lineage is diverged, migrations may have inconsistent
    # graph predecessors even if Django would happen to accept the names.
    safe = (
        not unknown
        and not missing_c7
        and "0019_auth_abuse_bucket" in applied
        and "0019_auth_abuse_bucket" in available
    )
    return {
        "result": "LINEAGE_COMPATIBLE_NOT_AUTHORIZED" if safe else "BLOCKED",
        "unrepresented_applied": unknown,
        "number_collisions": collisions,
        "missing_c7_source": missing_c7,
        "required_parent_applied": "0019_auth_abuse_bucket" in applied,
        "source_core_migration_count": len(current),
        "applied_core_migration_count": len(applied),
        "db_writes_performed": False,
        "hosted_c7_activation_authorized": False,
    }


def _load_applied(arg: str):
    try:
        values = json.loads(arg)
    except (TypeError, json.JSONDecodeError):
        raise ValueError("expected JSON list of migration names") from None
    if not isinstance(values, list):
        raise ValueError("expected JSON list of migration names")
    return values


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="W02 C7 read-only migration lineage compatibility gate"
    )
    parser.add_argument(
        "--applied-json", required=True,
        help="JSON list of core migration names, provided by independent read-only evidence",
    )
    parser.add_argument(
        "--source-dir", type=Path, default=MIGRATIONS,
        help="Repository core/migrations folder; test override only",
    )
    opts = parser.parse_args(argv)
    try:
        applied = _load_applied(opts.applied_json)
        if not opts.source_dir.is_dir():
            raise ValueError("source migration directory missing")
        source = {
            p.stem for p in opts.source_dir.glob("[0-9][0-9][0-9][0-9]_*.py")
        }
        result = check_migration_lineage(source, applied)
    except ValueError as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc),
                          "db_writes_performed": False}, sort_keys=True))
        return 2

    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "LINEAGE_COMPATIBLE_NOT_AUTHORIZED" else 3


if __name__ == "__main__":
    sys.exit(main())
