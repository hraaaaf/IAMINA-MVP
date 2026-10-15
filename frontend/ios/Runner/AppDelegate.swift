import Flutter
import UIKit
import Security
import LocalAuthentication

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  private var nativeAppLockBridge: NativeAppLockBridge?
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
    nativeAppLockBridge = NativeAppLockBridge(
      messenger: engineBridge.applicationRegistrar.messenger())
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


// D18: real cryptographic native-app-lock bridge.
//
// Secure Enclave EC P-256 private key bound to current biometric enrollment,
// ThisDeviceOnly storage, privateKeyUsage access policy. Fresh random challenge
// MUST be signed by the protected private key and verified before unlocking.
// A bare successful LAContext.evaluatePolicy() is never treated as an unlock.
// Simulators and devices without enrolled Face ID / Touch ID FAIL CLOSED.
private final class NativeAppLockBridge {
  private let channel: FlutterMethodChannel
  private let keyTagPrefix = "ma.iamina.app.native-bio-v1-"
  private let credentialPrefix = "native-bio-v1-"
  private let origin = "https://native.iamina.invalid"
  private let relyingParty = "ma.iamina.app"

  init(messenger: FlutterBinaryMessenger) {
    channel = FlutterMethodChannel(
      name: "ma.iamina.app/native_app_lock_v1", binaryMessenger: messenger)
    channel.setMethodCallHandler { [weak self] call, result in
      guard let self = self else {
        result(FlutterError(code: "bridge_unavailable", message: nil, details: nil))
        return
      }
      self.handle(call, result: result)
    }
  }

  private func supportsStrongBiometry() -> Bool {
    #if targetEnvironment(simulator)
      return false
    #else
      let context = LAContext()
      context.localizedFallbackTitle = ""
      var error: NSError?
      return context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics,
                                       error: &error)
    #endif
  }

  private func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    switch call.method {
    case "capability":
      result(["capability": supportsStrongBiometry() ? "supported" : "unavailable"])
    case "enroll":
      guard supportsStrongBiometry() else {
        fail(result, code: "strong_auth_unavailable"); return
      }
      DispatchQueue.global(qos: .userInitiated).async {
        let response = self.enroll()
        DispatchQueue.main.async {
          switch response {
          case let .success(value): result(value)
          case let .failure(error): self.fail(result, code: error.code)
          }
        }
      }
    case "unlock":
      guard supportsStrongBiometry() else {
        fail(result, code: "strong_auth_unavailable"); return
      }
      guard let args = call.arguments as? [String: Any],
            let credentialId = args["credentialId"] as? String,
            let expectedSpki = args["publicKeySpki"] as? String,
            args["origin"] as? String == origin,
            args["rpId"] as? String == relyingParty,
            let uuid = validatedUuid(credentialId) else {
        fail(result, code: "invalid_native_credential"); return
      }
      DispatchQueue.global(qos: .userInitiated).async {
        let response = self.proveKey(uuid: uuid, expectedSpki: expectedSpki)
        DispatchQueue.main.async {
          switch response {
          case let .success(value): result(value)
          case let .failure(error): self.fail(result, code: error.code)
          }
        }
      }
    default:
      result(FlutterMethodNotImplemented)
    }
  }

  private struct ProofFailure: Error {
    let code: String
    init(_ code: String) { self.code = code }
  }

  private func fail(_ result: FlutterResult, code: String) {
    result(FlutterError(code: code, message: nil, details: nil))
  }

  private func validatedUuid(_ handle: String) -> String? {
    guard handle.hasPrefix(credentialPrefix) else { return nil }
    let raw = String(handle.dropFirst(credentialPrefix.count))
    guard let uuid = UUID(uuidString: raw),
          raw == uuid.uuidString.lowercased() else { return nil }
    return raw
  }

  private func tag(for uuid: String) -> Data {
    Data((keyTagPrefix + uuid).utf8)
  }

  private func removeKey(uuid: String) {
    let query: [String: Any] = [
      kSecClass as String: kSecClassKey,
      kSecAttrApplicationTag as String: tag(for: uuid),
      kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom
    ]
    SecItemDelete(query as CFDictionary)
  }

  private func makeChallenge() throws -> Data {
    var challenge = Data(count: 32)
    let rc = challenge.withUnsafeMutableBytes { bytes -> Int32 in
      guard let base = bytes.baseAddress else { return errSecParam }
      return SecRandomCopyBytes(kSecRandomDefault, bytes.count, base)
    }
    guard rc == errSecSuccess else { throw ProofFailure("random_unavailable") }
    return challenge
  }

  private func publicKeySpki(_ key: SecKey) throws -> String {
    var error: Unmanaged<CFError>?
    guard let raw = SecKeyCopyExternalRepresentation(key, &error) as Data?,
          raw.count == 65, raw.first == 0x04 else {
      throw ProofFailure("invalid_native_public_key")
    }
    // DER SubjectPublicKeyInfo prefix for P-256 uncompressed X9.63 public key.
    let prefix: [UInt8] = [
      0x30, 0x59, 0x30, 0x13, 0x06, 0x07, 0x2a, 0x86,
      0x48, 0xce, 0x3d, 0x02, 0x01, 0x06, 0x08, 0x2a,
      0x86, 0x48, 0xce, 0x3d, 0x03, 0x01, 0x07, 0x03,
      0x42, 0x00
    ]
    return (Data(prefix) + raw).base64EncodedString()
  }

  private func protectedKey(uuid: String, context: LAContext) throws -> SecKey {
    var ref: CFTypeRef?
    let query: [String: Any] = [
      kSecClass as String: kSecClassKey,
      kSecAttrApplicationTag as String: tag(for: uuid),
      kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
      kSecReturnRef as String: true,
      kSecMatchLimit as String: kSecMatchLimitOne,
      kSecUseAuthenticationContext as String: context,
      kSecUseOperationPrompt as String: "Déverrouiller IAMINA"
    ]
    guard SecItemCopyMatching(query as CFDictionary, &ref) == errSecSuccess,
          let item = ref else { throw ProofFailure("key_unavailable") }
    return (item as! SecKey)
  }

  private func signAndVerify(privateKey: SecKey, challenge: Data) throws {
    guard let publicKey = SecKeyCopyPublicKey(privateKey) else {
      throw ProofFailure("key_unavailable")
    }
    var signingError: Unmanaged<CFError>?
    guard let signature = SecKeyCreateSignature(
      privateKey, .ecdsaSignatureMessageX962SHA256,
      challenge as CFData, &signingError) else {
      throw ProofFailure("biometric_cancelled_or_key_invalidated")
    }
    var verifyError: Unmanaged<CFError>?
    guard SecKeyVerifySignature(
      publicKey, .ecdsaSignatureMessageX962SHA256,
      challenge as CFData, signature, &verifyError) else {
      throw ProofFailure("signature_not_verified")
    }
  }

  private func enroll() -> Result<[String: Any], ProofFailure> {
    guard supportsStrongBiometry() else {
      return .failure(ProofFailure("strong_auth_unavailable"))
    }
    let uuid = UUID().uuidString.lowercased()
    var success = false
    defer { if !success { removeKey(uuid: uuid) } }
    do {
      var accessError: Unmanaged<CFError>?
      guard let access = SecAccessControlCreateWithFlags(
        kCFAllocatorDefault, kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
        [.privateKeyUsage, .biometryCurrentSet], &accessError) else {
        throw ProofFailure("secure_enclave_unavailable")
      }
      var keyError: Unmanaged<CFError>?
      let attributes: [String: Any] = [
        kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
        kSecAttrKeySizeInBits as String: 256,
        kSecAttrTokenID as String: kSecAttrTokenIDSecureEnclave,
        kSecPrivateKeyAttrs as String: [
          kSecAttrIsPermanent as String: true,
          kSecAttrApplicationTag as String: tag(for: uuid),
          kSecAttrAccessControl as String: access
        ]
      ]
      guard let key = SecKeyCreateRandomKey(attributes as CFDictionary, &keyError),
            let publicKey = SecKeyCopyPublicKey(key) else {
        throw ProofFailure("secure_enclave_unavailable")
      }
      let spki = try publicKeySpki(publicKey)
      let context = LAContext()
      context.localizedFallbackTitle = ""
      context.touchIDAuthenticationAllowableReuseDuration = 0
      defer { context.invalidate() }
      let protected = try protectedKey(uuid: uuid, context: context)
      try signAndVerify(privateKey: protected, challenge: makeChallenge())
      success = true
      return .success([
        "credentialId": credentialPrefix + uuid,
        "publicKeySpki": spki,
        "verified": true
      ])
    } catch let error as ProofFailure { return .failure(error) }
    catch { return .failure(ProofFailure("native_enroll_failed")) }
  }

  private func proveKey(uuid: String, expectedSpki: String)
      -> Result<[String: Any], ProofFailure> {
    do {
      let context = LAContext()
      context.localizedFallbackTitle = ""
      context.touchIDAuthenticationAllowableReuseDuration = 0
      defer { context.invalidate() }
      let key = try protectedKey(uuid: uuid, context: context)
      guard let publicKey = SecKeyCopyPublicKey(key) else {
        throw ProofFailure("key_unavailable")
      }
      // If secure app-lock metadata is substituted, even valid biometrics
      // must not authorize a DIFFERENT key.
      let actualSpki = try publicKeySpki(publicKey)
      guard actualSpki == expectedSpki else {
        throw ProofFailure("native_public_key_mismatch")
      }
      try signAndVerify(privateKey: key, challenge: makeChallenge())
      return .success(["verified": true])
    } catch let error as ProofFailure { return .failure(error) }
    catch { return .failure(ProofFailure("native_unlock_failed")) }
  }
}
