#!/usr/bin/env python3
"""Compile and test the exact Foundation-only backup helper shipped in Runner.

Host macOS smoke test, NOT iOS Simulator XCTest or iCloud backup verification.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "frontend/ios/Runner/AppDelegate.swift"
SCENE = ROOT / "frontend/ios/Runner/SceneDelegate.swift"

HARNESS = r"""
import Foundation

func require(_ condition: @autoclosure () -> Bool, _ message: String) {
  if !condition() {
    fputs("FAIL: \(message)\n", stderr)
    exit(1)
  }
}

let matching = [
  "amina_vault_v1_native_42.sqlite",
  "amina_vault_v1_native_42.sqlite-wal",
  "amina_vault_v1_native_42.sqlite-shm",
  "amina_vault_v1_device_43.sqlite",
]
let unrelated = [
  "amina.sqlite", "other.sqlite", "personal-notes.txt",
  "amina_vault_v1_native_42.sqlite-journal",
  "amina_vault_v2_native_42.sqlite",
]
for name in matching {
  require(ClinicalVaultBackupExclusion.isPatientVaultSQLiteFile(
    URL(fileURLWithPath: name)), "must match \(name)")
}
for name in unrelated {
  require(!ClinicalVaultBackupExclusion.isPatientVaultSQLiteFile(
    URL(fileURLWithPath: name)), "must reject \(name)")
}
print("PASS matching and nonmatching database names")

let fm = FileManager.default
let directory = fm.temporaryDirectory.appendingPathComponent(
  UUID().uuidString, isDirectory: true)
try fm.createDirectory(at: directory, withIntermediateDirectories: true)
defer { try? fm.removeItem(at: directory) }
for name in matching + unrelated {
  try Data([1, 2, 3]).write(to: directory.appendingPathComponent(name))
}
let result = ClinicalVaultBackupExclusion.apply(to: directory)
require(Set(result.map(\.lastPathComponent)) == Set(matching),
        "only vault SQLite and sidecars must be marked")
print("PASS patient-only exclusion selection")

let again = ClinicalVaultBackupExclusion.apply(to: directory)
require(Set(again.map(\.lastPathComponent)) == Set(matching),
        "reapplication must be idempotent")
print("PASS repeated application")

#if os(macOS)
for name in matching {
  let values = try directory.appendingPathComponent(name)
    .resourceValues(forKeys: [.isExcludedFromBackupKey])
  require(values.isExcludedFromBackup == true, "macOS resource flag for \(name)")
}
for name in unrelated {
  let values = try directory.appendingPathComponent(name)
    .resourceValues(forKeys: [.isExcludedFromBackupKey])
  require(values.isExcludedFromBackup != true, "unrelated file flagged: \(name)")
}
print("PASS macOS Foundation backup flag readback")
#else
print("SKIP native backup flag readback: not a macOS host")
#endif

let noVault = fm.temporaryDirectory.appendingPathComponent(
  UUID().uuidString, isDirectory: true)
try fm.createDirectory(at: noVault, withIntermediateDirectories: true)
defer { try? fm.removeItem(at: noVault) }
require(ClinicalVaultBackupExclusion.apply(to: noVault).isEmpty,
        "empty directory must be no-op")
print("PASS empty-directory behavior")
"""

def main() -> None:
    app = APP.read_text(encoding="utf-8")
    scene = SCENE.read_text(encoding="utf-8")
    anchor = "enum ClinicalVaultBackupExclusion {"
    if app.count(anchor) != 1:
        raise AssertionError("AppDelegate backup helper must be unique")
    if "ClinicalVaultBackupExclusion.applyToDocumentsDirectory()" not in scene:
        raise AssertionError("SceneDelegate must reapply on scene transitions")
    if not (
        "sceneDidEnterBackground" in scene
        and "sceneWillEnterForeground" in scene
    ):
        raise AssertionError("Missing scene lifecycle reapplication")
    helper = app[app.index(anchor):].strip()
    if not helper.endswith("}"):
        raise AssertionError("Backup helper must end at source file EOF")
    with tempfile.TemporaryDirectory(prefix="iamina-d10-ios-") as directory:
        out = Path(directory)
        (out / "ClinicalVaultBackupExclusion.swift").write_text(
            "import Foundation\n\n" + helper + "\n", encoding="utf-8"
        )
        (out / "main.swift").write_text(HARNESS, encoding="utf-8")
        binary = out / "backup-helper-tests"
        subprocess.run(
            ["swiftc", str(out / "ClinicalVaultBackupExclusion.swift"),
             str(out / "main.swift"), "-o", str(binary)],
            check=True,
        )
        subprocess.run([str(binary)], check=True)
    print("PASS actual Runner Swift backup helper compiled and smoke-tested.")
    print("LIMIT: macOS Foundation, not iOS Simulator XCTest or iCloud restore.")

if __name__ == "__main__":
    main()
