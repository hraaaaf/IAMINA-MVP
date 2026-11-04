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

report = {
    "kind": "D18_STATIC_WEB_APP_SQLITE_SOURCE_INVENTORY_NOT_CUTOVER",
    "allowed": EXPECTED,
    "observed": observed,
    "violations": violations,
    "missing": missing,
    "old_cached_tabs": "NOT_COVERED",
    "contract_failures": contract_failures,
    "synthetic_bypass_leaks": synthetic_bypass_leaks,
}
print(json.dumps(report, indent=2, sort_keys=True))
if violations or missing or contract_failures or synthetic_bypass_leaks:
    sys.exit("D18_REAL_SQLITE_ENTRYPOINT_INVENTORY_FAIL_CLOSED")
