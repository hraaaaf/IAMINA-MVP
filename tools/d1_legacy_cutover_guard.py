#!/usr/bin/env python3
"""IAMINA D1 P0-A: non-destructive source guard for legacy Web vaults.

This is a build gate, NOT a runtime lock, a crypto proof or clinical clearance.
A cached old PWA can still write to its original IndexedDB database offline.
"""
from __future__ import annotations

import argparse
import hashlib
from collections import deque
from pathlib import Path
import re
import sys

ENTRYPOINTS = (
    "main.dart",
    "data/drift/database.dart",
    "services/patient_vault_app_host.dart",
    "services/patient_vault_session_controller.dart",
)
DIRECTIVE = re.compile(
    r"""^[ \t]*(?:import|export|part)[ \t]+['"]([^'"]+\.dart)['"]([^;]*);""",
    re.M,
)
CONDITIONAL = re.compile(r"""\bif\s*\([^)]*\)\s*['"]([^'"]+\.dart)['"]""")
D18_CUTOVER = re.compile(r"(?:^|/)d18_[^/]*\.dart$")
DESTRUCTIVE = re.compile(
    r"\b(?:deleteDatabase|deleteDatabaseSync|clearIndexedDb|"
    r"deletePatientVault|activateCiphertextCutover|"
    r"promoteLegacyVault|migrateLegacyVault)\s*\("
)


def _local_import(lib: Path, current: Path, uri: str) -> Path | None:
    if uri.startswith("package:amina/"):
        result = lib / uri[len("package:amina/"):]
    elif uri.startswith(("dart:", "package:")):
        return None
    elif uri.startswith(("./", "../")) or not ":" in uri:
        result = current.parent / uri
    else:
        return None
    result = result.resolve()
    try:
        result.relative_to(lib.resolve())
    except ValueError:
        raise ValueError(f"import escapes lib/: {current}: {uri}")
    return result


def reachable_sources(lib: Path, entrypoints: tuple[str, ...] = ENTRYPOINTS) -> set[Path]:
    todo = deque(lib / e for e in entrypoints)
    seen: set[Path] = set()
    while todo:
        source = todo.popleft().resolve()
        if source in seen:
            continue
        if not source.is_file():
            raise ValueError(f"missing source in production import graph: {source}")
        seen.add(source)
        content = source.read_text(encoding="utf-8")
        # Parse conditional URIs only inside a real Dart import/export/part
        # statement, never from unrelated executable code or a SQL string.
        uris: list[str] = []
        for statement in DIRECTIVE.finditer(content):
            uris.append(statement.group(1))
            uris.extend(CONDITIONAL.findall(statement.group(2)))
        for uri in uris:
            target = _local_import(lib, source, uri)
            if target is not None:
                todo.append(target)
    return seen


def check(root: Path, entrypoints: tuple[str, ...] = ENTRYPOINTS) -> list[str]:
    lib = root / "frontend" / "lib"
    db = lib / "data" / "drift" / "database.dart"
    scope = lib / "data" / "drift" / "patient_vault_scope.dart"
    errors: list[str] = []
    if not db.is_file() or not scope.is_file():
        return ["clinical vault sources unavailable — fail closed"]
    database_source = db.read_text(encoding="utf-8")
    scope_source = scope.read_text(encoding="utf-8")
    # P0 immutable namespace boundary. Any intentional change requires a
    # separately reviewed new fingerprint; loose substring checks were bypassed
    # by factories aliasing the legacy 'amina' database.
    pinned_scope_sha256 = "f60a4d1ac60f701bc4028fdd6e85ae88cf1c4a383cc14162a379430828624c02"
    if hashlib.sha256(scope_source.encode("utf-8")).hexdigest() != pinned_scope_sha256:
        errors.append("patient vault namespace source changed — independent security review required")
    # Stable names and distinct constructors are a precondition; no implicit adoption.
    # Bind invariants to active constructors instead of loose text tokens.
    constructor_invariants = (
        (r"AppDatabase\.defaults\(\).*?driftDatabase\(\s*name:\s*'amina'",
         "legacy default constructor / database name"),
        (r"AppDatabase\.forPatientVault\(PatientVaultScope scope\)"
         r".*?driftDatabase\(\s*name:\s*scope\.databaseName",
         "isolated patient constructor / database name"),
    )
    for pattern, label in constructor_invariants:
        if not re.search(pattern, database_source, re.S):
            errors.append(f"legacy or patient vault boundary changed: {label}")
    for token in ("amina_vault_v1_native_", "amina_vault_v1_device_",
                  "amina_vault_v1_audit"):
        if token not in scope_source:
            errors.append(f"owner namespace changed: {token}")
    try:
        sources = reachable_sources(lib, entrypoints)
    except ValueError as exc:
        return errors + [str(exc)]
    for source in sorted(sources):
        relative = source.relative_to(lib.resolve()).as_posix()
        if D18_CUTOVER.search(relative):
            errors.append(f"experimental D18 module reachable from app: {relative}")
        # A helper reached through a transitive import or part can be destructive.
        if DESTRUCTIVE.search(source.read_text(encoding="utf-8")):
            errors.append(f"possible destructive/cutover operation in {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    violations = check(args.root.resolve())
    for violation in violations:
        print("D1_P0A_NO_CUTOVER: FAIL:", violation, file=sys.stderr)
    if violations:
        return 1
    print("D1_P0A_NO_CUTOVER: PASS static production-import and namespace guard")
    print("D1_P0A_PHYSICAL_STALE_WRITER: NOT_RUN — cutover remains NO-GO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
