import Flutter
import UIKit

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    applyPatientVaultBackupExclusion()
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }

  override func applicationDidEnterBackground(_ application: UIApplication) {
    super.applicationDidEnterBackground(application)
    applyPatientVaultBackupExclusion()
  }

  override func applicationWillEnterForeground(_ application: UIApplication) {
    super.applicationWillEnterForeground(application)
    applyPatientVaultBackupExclusion()
  }

  private func applyPatientVaultBackupExclusion() {
    ClinicalVaultBackupExclusion.applyToDocumentsDirectory()
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
  }
}


// Drift Flutter stores legacy and patient vault SQLite files in Documents.
// Only patient-scoped databases are handled here; never apply backup exclusions
// to all Documents or accidentally suppress a user's unrelated files.
enum ClinicalVaultBackupExclusion {
  private static let vaultPrefix = "amina_vault_v1_"
  private static let sqliteSuffixes = [".sqlite", ".sqlite-wal", ".sqlite-shm"]

  static func applyToDocumentsDirectory() {
    guard let documentsDirectory = FileManager.default.urls(
      for: .documentDirectory, in: .userDomainMask
    ).first else { return }
    _ = apply(to: documentsDirectory)
  }

  static func isPatientVaultSQLiteFile(_ url: URL) -> Bool {
    let name = url.lastPathComponent
    guard name.hasPrefix(vaultPrefix) else { return false }
    return sqliteSuffixes.contains { name.hasSuffix($0) }
  }

  @discardableResult
  static func apply(to documentsDirectory: URL, fileManager: FileManager = .default) -> [URL] {
    guard let files = try? fileManager.contentsOfDirectory(
      at: documentsDirectory,
      includingPropertiesForKeys: [.isRegularFileKey],
      options: [.skipsHiddenFiles]
    ) else {
      return []
    }
    var excluded: [URL] = []
    for url in files where isPatientVaultSQLiteFile(url) {
      guard (try? url.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile) == true else {
        continue
      }
      do {
        var values = URLResourceValues()
        values.isExcludedFromBackup = true
        var mutableURL = url
        try mutableURL.setResourceValues(values)
        excluded.append(url)
      } catch {
        // Do not emit paths or medical data to logs.
        NSLog("IAMINA: unable to apply patient vault backup exclusion")
      }
    }
    return excluded
  }
}
