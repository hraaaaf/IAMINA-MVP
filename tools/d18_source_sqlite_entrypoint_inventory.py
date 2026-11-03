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
    "main.dart": {"defaults": 1, "forPatientVault": 1},
    "services/patient_vault_session_controller.dart": {"forPatientVault": 1},
    # Dedicated synthetic audit guest database; no clinical patient authority.
    "services/patient_vault_app_host.dart": {"forPatientVault": 1},
}
PATTERN = re.compile(r"\bAppDatabase\s*\.\s*(defaults|forPatientVault)\s*\(")
DIRECT = re.compile(r"\bdriftDatabase\s*\(")
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
        if rel != "data/drift/database.dart" and DIRECT.search(content):
            observed.append({"path": rel, "line": i, "kind": "directDriftDatabase"})

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
report = {
    "kind": "D18_STATIC_WEB_APP_SQLITE_SOURCE_INVENTORY_NOT_CUTOVER",
    "allowed": EXPECTED,
    "observed": observed,
    "violations": violations,
    "missing": missing,
    "old_cached_tabs": "NOT_COVERED",
}
print(json.dumps(report, indent=2, sort_keys=True))
if violations or missing:
    sys.exit("D18_REAL_SQLITE_ENTRYPOINT_INVENTORY_FAIL_CLOSED")
