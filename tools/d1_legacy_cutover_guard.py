#!/usr/bin/env python3
"""IAMINA D1 P0-A: non-destructive source guard for legacy Web vaults.

This is a build gate, NOT a runtime lock, a crypto proof or clinical clearance.
A cached old PWA can still write to its original IndexedDB database offline.
"""
from __future__ import annotations

import argparse
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
IMPORT = re.compile(r"""^\s*(?:import|export)\s+['"]([^'"]+)['"]""", re.M)
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
        for uri in IMPORT.findall(source.read_text(encoding="utf-8")):
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
    # Stable names and distinct constructors are a precondition; no implicit adoption.
    for token in ("AppDatabase.defaults()", "name: 'amina'",
                  "AppDatabase.forPatientVault(PatientVaultScope scope)",
                  "name: scope.databaseName"):
        if token not in database_source:
            errors.append(f"legacy or patient vault boundary changed: {token}")
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
        if source in {db.resolve(), (lib / "main.dart").resolve(),
                      (lib / "services/patient_vault_session_controller.dart").resolve(),
                      (lib / "services/patient_vault_app_host.dart").resolve()}:
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
