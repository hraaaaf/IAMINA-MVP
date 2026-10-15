import Flutter
import UIKit
import XCTest
@testable import Runner

class RunnerTests: XCTestCase {
  private func inTemporaryDirectory(_ test: (URL) throws -> Void) throws {
    let directory = FileManager.default.temporaryDirectory
      .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(
      at: directory, withIntermediateDirectories: true
    )
    defer { try? FileManager.default.removeItem(at: directory) }
    try test(directory)
  }

  func testPatientVaultDetectionIsRestrictedToSQLiteAndSidecars() {
    for name in [
      "amina_vault_v1_native_42.sqlite",
      "amina_vault_v1_native_42.sqlite-wal",
      "amina_vault_v1_native_42.sqlite-shm",
      "amina_vault_v1_device_f813.sqlite"
    ] {
      XCTAssertTrue(ClinicalVaultBackupExclusion.isPatientVaultSQLiteFile(
        URL(fileURLWithPath: name)
      ), name)
    }
    for name in [
      "amina.sqlite",
      "unrelated.sqlite",
      "amina_vault_v1_native_42.sqlite-journal",
      "backup.json",
      "amina_vault_v2_native_42.sqlite"
    ] {
      XCTAssertFalse(ClinicalVaultBackupExclusion.isPatientVaultSQLiteFile(
        URL(fileURLWithPath: name)
      ), name)
    }
  }

  func testOnlyExistingPatientSQLiteFilesGetBackupExclusion() throws {
    try inTemporaryDirectory { directory in
      let patientFiles = [
        "amina_vault_v1_native_42.sqlite",
        "amina_vault_v1_native_42.sqlite-wal",
        "amina_vault_v1_native_42.sqlite-shm"
      ]
      let otherFiles = ["personal-notes.txt", "amina.sqlite"]
      for name in patientFiles + otherFiles {
        try Data([1, 2, 3]).write(to: directory.appendingPathComponent(name))
      }
      let changed = ClinicalVaultBackupExclusion.apply(to: directory)
      XCTAssertEqual(Set(changed.map(\.lastPathComponent)), Set(patientFiles))
      for name in patientFiles {
        let values = try directory.appendingPathComponent(name)
          .resourceValues(forKeys: [.isExcludedFromBackupKey])
        XCTAssertEqual(values.isExcludedFromBackup, true, name)
      }
      for name in otherFiles {
        let values = try directory.appendingPathComponent(name)
          .resourceValues(forKeys: [.isExcludedFromBackupKey])
        XCTAssertNotEqual(values.isExcludedFromBackup, true, name)
      }
      // Reapply is safe after an ordinary update, since Apple may reset the flag.
      let repeated = ClinicalVaultBackupExclusion.apply(to: directory)
      XCTAssertEqual(Set(repeated.map(\.lastPathComponent)), Set(patientFiles))
    }
  }

  func testNoVaultIsNoOp() throws {
    try inTemporaryDirectory { directory in
      XCTAssertEqual(ClinicalVaultBackupExclusion.apply(to: directory), [])
    }
  }
}
