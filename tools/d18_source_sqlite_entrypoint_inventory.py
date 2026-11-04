#!/usr/bin/env python3
"""D18: refuse an unreviewed REAL SQLite source-open entrypoint.

Runs on the exact checked-out PR tree. This is a static inventory, NOT a
runtime proof, not a migration unlock, and not protection for stale tabs.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path("frontend/lib")
EXPECTED = {
    # Definitions of the two constructors, not additional callers.
    # These are counted explicitly so the inventory rejects new constructors.
    "data/drift/database.dart": {"defaults": 1, "forPatientVault": 1},
    "main.dart": {"defaults": 1, "forPatientVault": 2},
    "services/patient_vault_session_controller.dart": {"forPatientVault": 1},
    # Dedicated synthetic audit guest database; no clinical patient authority.
    "services/patient_vault_app_host.dart": {"forPatientVault": 1},
}
PATTERN = re.compile(r"\bAppDatabase\s*\.\s*(defaults|forPatientVault)\s*\(")
DIRECT = re.compile(r"\bdriftDatabase\s*\(")
DIRECT_APP = re.compile(r"\bAppDatabase\s*\(")
TEST_FACTORY = re.compile(r"\bAppDatabase\s*\.\s*testPatientVault\s*\(")
TEST_ENTRY_PREFIXES = ("d18_", "ui_", "d5_", "login_screenshot")

observed = []
for path in sorted(ROOT.rglob("*.dart")):
    rel = path.relative_to(ROOT).as_posix()
    if path.name.endswith(".g.dart") or "/generated/" in rel:
        continue
    if path.name != "main.dart" and path.name.startswith(TEST_ENTRY_PREFIXES):
        # Explicit stand-alone test entrypoints are NOT runtime app-shell.
        continue
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        content = line.split("//", 1)[0]
        if not content.strip() or content.lstrip().startswith(("*", "///")):
            continue
        for match in PATTERN.finditer(content):
            observed.append({"path": rel, "line": i, "kind": match.group(1)})
        if rel != "data/drift/database.dart":
            if DIRECT.search(content):
                observed.append({"path": rel, "line": i, "kind": "directDriftDatabase"})
            if DIRECT_APP.search(content):
                observed.append({"path": rel, "line": i, "kind": "directAppDatabase"})
            if TEST_FACTORY.search(content):
                observed.append({"path": rel, "line": i, "kind": "testFactoryInRuntime"})

actual = {}
for item in observed:
    counts = actual.setdefault(item["path"], {})
    counts[item["kind"]] = counts.get(item["kind"], 0) + 1

violations = {
    path: counts for path, counts in actual.items()
    if EXPECTED.get(path) != counts
}
missing = {
    path: counts for path, counts in EXPECTED.items()
    if actual.get(path) != counts
}
# Literal ordered source checks deliberately reject a new open path until
# reviewed. They are NOT runtime proof and CANNOT detect old cached clients.
CONTRACT = {
    "main.dart": [
        ("legacy", "D18SourceLockGate.legacy()", "AppDatabase.defaults()"),
        ("patient_probe", "D18SourceLockGate.patient(scope)",
         "AppDatabase.forPatientVault(scope)"),
        ("audit_guest", "D18SourceLockGate.auditGuest()",
         "AppDatabase.forPatientVault(PatientVaultScope.auditOnly())"),
    ],
    "services/patient_vault_session_controller.dart": [
        ("patient_controller", "D18SourceLockGate.patient(scope)",
         "database: AppDatabase.forPatientVault(scope)"),
        ("close_before_unlock", "await database.close();",
         "await releaseWorker?.call();"),
    ],
    "services/patient_vault_app_host.dart": [
        ("guest_close_before_unlock", "await _guestDatabase.close();",
         "await widget.guestSourceLock?.close();"),
    ],
}
contract_failures = []
for rel, checks in CONTRACT.items():
    source = (ROOT / rel).read_text(encoding="utf-8")
    for name, acquire, open_or_release in checks:
        if (acquire not in source or open_or_release not in source or
                source.index(acquire) >= source.index(open_or_release)):
            contract_failures.append(f"{rel}:{name}")
host = (ROOT / "services/patient_vault_app_host.dart").read_text(encoding="utf-8")
if "D18_GUEST_SOURCE_LOCK_REQUIRED" not in host:
    contract_failures.append("services/patient_vault_app_host.dart:guest_fail_closed")
if "defaultValue: false" not in (ROOT / "main.dart").read_text(encoding="utf-8"):
    contract_failures.append("main.dart:canary_disabled_by_default")

# An explicitly synthetic bypass must never be wired into app/runtime code.
synthetic_bypass_leaks = []
for path in sorted(ROOT.rglob("*.dart")):
    rel = path.relative_to(ROOT).as_posix()
    if rel == "data/drift/d18_pre_cutover_atomic_promotion.dart" or (
        path.name != "main.dart" and path.name.startswith(TEST_ENTRY_PREFIXES)
    ):
        continue
    src = path.read_text(encoding="utf-8")
    if re.search(r"\ballowUnfencedSyntheticFixture\s*:\s*true\b", src):
        synthetic_bypass_leaks.append(rel)

# A test-only marker/connector is not a real clinical fencing mechanism.
# Block new production wiring even when a caller leaves synthetic override false:
# a stale offline bundle remains able to modify the legacy source.
PROHIBITED_RUNTIME_REFS = re.compile(
    r"\b(?:D18PreCutoverAtomicPromotion|D18PreCutoverIndexedDbMarkerStore|"
    r"D18PreCutoverCipherAdapter|D18PreCutoverSessionCoordinator|"
    r"openD18UnpublishedCipherWorker|"
    r"D18CutoverPhase\s*\.\s*ciphertextActive)\b"
)
# Guard the guard: a malformed regex that silently matches nothing is
# itself a safety regression. Use controlled, synthetic source tokens.
for sample in (
    "final x = D18PreCutoverAtomicPromotion(",
    "D18CutoverPhase.ciphertextActive",
    "openD18UnpublishedCipherWorker(scope, intent, destination, key)",
):
    if not PROHIBITED_RUNTIME_REFS.search(sample):
        sys.exit("D18_CUTOVER_STATIC_GUARD_SELFTEST_FAIL")
if PROHIBITED_RUNTIME_REFS.search("D18SourceLockGate.patient(scope)"):
    sys.exit("D18_CUTOVER_STATIC_GUARD_FALSE_POSITIVE")

runtime_cutover_links = []
for path in sorted(ROOT.rglob("*.dart")):
    rel = path.relative_to(ROOT).as_posix()
    if path.name.endswith(".g.dart") or "/generated/" in rel:
        continue
    # Test-only entrypoints and D18 PRE-CUTOVER definitions are not product
    # providers. Any import/wiring by patient-facing code must be reviewed.
    if (
        (path.name.startswith(TEST_ENTRY_PREFIXES) and
         path.name != "main.dart")
        or rel.startswith("data/drift/d18_")
    ):
        continue
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        executable = line.split("//", 1)[0].strip()
        if not executable or executable.startswith(("*", "///")):
            continue
        if PROHIBITED_RUNTIME_REFS.search(executable) or (
            "import " in executable
            and re.search(
                r"['\"][^'\"]*d18_(?:pre_cutover_|unpublished_cipher_)",
                executable,
            )
        ):
            runtime_cutover_links.append({"path": rel, "line": i})


# Transitively reachable candidate migration code is forbidden from the
# production app shell EVEN when its filename starts with d18_ and a shallow
# source-name inventory would skip it. Examine conditional Dart imports too.
# This static graph catches package:amina and relative import/export/part
# dependencies. It is NOT a clinical proof, nor a stale-tab fence.
IMPORT_DIRECTIVE = re.compile(
    r"(?m)^\s*(?:import|export|part)\s+([^;]+);"
)
IMPORT_LITERAL = re.compile(r"['\"]([^'\"]+)['\"]")
PRODUCTION_ROOTS = (
    "main.dart",
    "data/drift/database.dart",
    "services/patient_vault_session_controller.dart",
    "services/patient_vault_app_host.dart",
)
PROHIBITED_REACHABLE = re.compile(
    r"^(?:d18_(?!source_lock_)[^/]+\.dart|"
    r"data/drift/d18_(?:pre_cutover_|unpublished_|cipher_|"
    r"keyed_|vault_key_|streaming_|full_cipher_|candidate_))"
)

def _local_import(from_path: str, uri: str) -> str | None:
    if uri.startswith("package:amina/"):
        candidate = ROOT / uri.removeprefix("package:amina/")
    elif uri.startswith("package:") or uri.startswith("dart:"):
        return None
    else:
        candidate = ROOT / from_path
        candidate = candidate.parent / uri
    resolved = candidate.resolve()
    try:
        rel = resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        raise RuntimeError("D18_IMPORT_PATH_ESCAPED_APP_ROOT")
    return rel

def _imports(from_path: str, contents: str) -> set[str]:
    result: set[str] = set()
    # Each conditional import may have more than one possible implementation.
    for directive in IMPORT_DIRECTIVE.findall(contents):
        for raw_uri in IMPORT_LITERAL.findall(directive):
            name = _local_import(from_path, raw_uri)
            if name is not None and name.endswith(".dart"):
                result.add(name)
    return result

# Self-test detection as a security property, not only the happy path.
assert _local_import("main.dart",
    "package:amina/data/drift/d18_pre_cutover_atomic_promotion.dart"
) == "data/drift/d18_pre_cutover_atomic_promotion.dart"
assert _local_import("services/patient_vault_app_host.dart",
    "../data/drift/d18_unpublished_cipher_connector_web.dart"
) == "data/drift/d18_unpublished_cipher_connector_web.dart"
assert len(_imports("main.dart",
    """import 'data/drift/d18_source_lock_stub.dart'
       if (dart.library.js_interop) 'data/drift/d18_source_lock_web.dart';"""
)) == 2
assert PROHIBITED_REACHABLE.search(
    "data/drift/d18_pre_cutover_atomic_promotion.dart")
assert PROHIBITED_REACHABLE.search("d18_unpublished_cipher_worker.dart")
assert not PROHIBITED_REACHABLE.search(
    "data/drift/d18_source_lock_gate.dart")

reachable: set[str] = set()
to_visit = list(PRODUCTION_ROOTS)
unresolved_local_imports: set[str] = set()
while to_visit:
    rel = to_visit.pop()
    if rel in reachable:
        continue
    reachable.add(rel)
    full_path = ROOT / rel
    if not full_path.is_file():
        # Generated files do not participate in importing new Dart sources.
        if rel.endswith(".g.dart") or rel.endswith(".freezed.dart"):
            continue
        unresolved_local_imports.add(rel)
        continue
    for dependency in _imports(rel, full_path.read_text(encoding="utf-8")):
        if dependency not in reachable:
            to_visit.append(dependency)

reachable_experimental = sorted(
    rel for rel in reachable if PROHIBITED_REACHABLE.search(rel)
)
# An app graph that cannot be fully resolved cannot justify release.
if unresolved_local_imports:
    sys.stderr.write("D18_UNRESOLVED_LOCAL_IMPORTS: "
                     + ", ".join(sorted(unresolved_local_imports)) + "\n")

report = {
    "kind": "D18_STATIC_WEB_APP_SQLITE_SOURCE_INVENTORY_NOT_CUTOVER",
    "allowed": EXPECTED,
    "observed": observed,
    "violations": violations,
    "missing": missing,
    "old_cached_tabs": "NOT_COVERED",
    "contract_failures": contract_failures,
    "synthetic_bypass_leaks": synthetic_bypass_leaks,
    "runtime_cutover_links": runtime_cutover_links,
    "production_dart_roots": list(PRODUCTION_ROOTS),
    "reachable_app_module_count": len(reachable),
    "reachable_experimental_migration_modules": reachable_experimental,
    "unresolved_local_imports": sorted(unresolved_local_imports),
}
print(json.dumps(report, indent=2, sort_keys=True))
if (violations or missing or contract_failures or synthetic_bypass_leaks
        or runtime_cutover_links or reachable_experimental
        or unresolved_local_imports):
    sys.exit("D18_REAL_SQLITE_ENTRYPOINT_INVENTORY_FAIL_CLOSED")
