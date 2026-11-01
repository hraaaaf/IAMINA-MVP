import 'dart:convert';
import 'dart:math';

import 'package:cryptography/cryptography.dart';

import 'patient_vault_scope.dart';

/// D18-A: approved passphrase + independent offline recovery-code policy.
///
/// PRE-CUTOVER ONLY. This does not encrypt Drift, persist an envelope or change
/// the live database connection. Never auto-enrol an existing clinical vault.
final class D18VaultKeySession {
  SecretKeyData? _dataKey;

  D18VaultKeySession._(this._dataKey);

  bool get isLocked => _dataKey == null;

  /// Transient key for a future vetted encrypted SQLite adapter.
  /// Do not cache this reference beyond the unlocked session.
  SecretKey requireUnlockedKey() {
    final key = _dataKey;
    if (key == null) throw StateError('D18 vault session is locked');
    return key;
  }

  /// Best-effort in-process overwrite, not a browser memory-erasure guarantee.
  void lock() {
    final key = _dataKey;
    _dataKey = null;
    key?.destroy();
  }
}

/// The recovery code must be saved independently, OFF the browser/device.
/// Do not persist the code, passphrase or session in Web storage or telemetry.
final class D18VaultKeyEnrollment {
  final String publicEnvelopeJson;
  final String offlineRecoveryCode;
  final D18VaultKeySession session;

  const D18VaultKeyEnrollment._(
    this.publicEnvelopeJson,
    this.offlineRecoveryCode,
    this.session,
  );
}

/// Key wrapping only; no database data is read, exported or modified.
///
/// A random 256-bit data key has two independent AES-256-GCM wrappers:
/// 1. PBKDF2-HMAC-SHA256 derived from the patient's local passphrase.
/// 2. A separate 256-bit uniformly random recovery code, shown once.
///
/// Both wrappers authenticate the actual patient vault namespace in AAD.
/// The public JSON contains neither the namespace nor any raw secret.
abstract final class D18VaultKeyPolicy {
  static const int version = 1;
  static const int kdfIterations = 600000;
  static const int maximumEnvelopeChars = 4096;
  static const String _format = 'iamina-d18-vault-key-envelope';
  static const String _prefix = 'IAMINA-R1-';

  static void _validateScope(PatientVaultScope scope) {
    if (scope.databaseName == PatientVaultScope.auditOnly().databaseName ||
        !scope.databaseName.startsWith('amina_vault_v1_')) {
      throw StateError('An authenticated patient vault scope is required');
    }
    // The PatientVaultScope factory does not itself authenticate the user.
  }

  static void _validatePassphrase(String value) {
    if (value.runes.length < 12 || value.runes.length > 1024) {
      throw ArgumentError('Local passphrase must contain 12 to 1024 characters');
    }
  }

  static List<int> _random(int length) {
    final random = Random.secure();
    return List<int>.generate(length, (_) => random.nextInt(256));
  }

  static String _aad(PatientVaultScope scope, String role) =>
      'IAMINA-D18-VAULT-KEYS-V1|${scope.databaseName}|$role';

  static Future<SecretKey> _derive(String passphrase, List<int> salt) =>
      Pbkdf2(
        macAlgorithm: Hmac.sha256(),
        iterations: kdfIterations,
        bits: 256,
      ).deriveKeyFromPassword(password: passphrase, nonce: salt);

  static Future<String> _seal(
    List<int> keyBytes,
    SecretKey wrappingKey,
    PatientVaultScope scope,
    String role,
  ) async {
    final box = await AesGcm.with256bits().encrypt(
      keyBytes,
      secretKey: wrappingKey,
      aad: utf8.encode(_aad(scope, role)),
    );
    return base64Encode(box.concatenation());
  }

  static Future<SecretKeyData> _open(
    String encoded,
    SecretKey wrappingKey,
    PatientVaultScope scope,
    String role,
  ) async {
    final bytes = await AesGcm.with256bits().decrypt(
      SecretBox.fromConcatenation(
        base64Decode(encoded), nonceLength: 12, macLength: 16,
      ),
      secretKey: wrappingKey,
      aad: utf8.encode(_aad(scope, role)),
    );
    if (bytes.length != 32) {
      throw const FormatException('Invalid D18 data-key length');
    }
    return SecretKeyData(List<int>.of(bytes), overwriteWhenDestroyed: true);
  }

  static String _encode({
    required List<int> salt,
    required String passwordWrappedKey,
    required String recoveryWrappedKey,
  }) => jsonEncode(<String, Object>{
    'format': _format,
    'version': version,
    'kdf': 'pbkdf2-hmac-sha256',
    'iterations': kdfIterations,
    'salt': base64Encode(salt),
    'cipher': 'aes-256-gcm',
    'passwordWrappedKey': passwordWrappedKey,
    'recoveryWrappedKey': recoveryWrappedKey,
  });

  static Map<String, dynamic> _parse(String json) {
    if (json.isEmpty || json.length > maximumEnvelopeChars) {
      throw const FormatException('Invalid D18 key-envelope size');
    }
    final value = jsonDecode(json);
    const expected = {
      'format', 'version', 'kdf', 'iterations',
      'salt', 'cipher', 'passwordWrappedKey', 'recoveryWrappedKey',
    };
    if (value is! Map<String, dynamic> ||
        value.keys.toSet().difference(expected).isNotEmpty ||
        expected.difference(value.keys.toSet()).isNotEmpty ||
        value['format'] != _format ||
        value['version'] != version ||
        value['kdf'] != 'pbkdf2-hmac-sha256' ||
        value['iterations'] != kdfIterations ||
        value['cipher'] != 'aes-256-gcm' ||
        value['salt'] is! String ||
        value['passwordWrappedKey'] is! String ||
        value['recoveryWrappedKey'] is! String) {
      throw const FormatException('Unsupported D18 key envelope');
    }
    try {
      if (base64Decode(value['salt'] as String).length != 16 ||
          base64Decode(value['passwordWrappedKey'] as String).length != 60 ||
          base64Decode(value['recoveryWrappedKey'] as String).length != 60) {
        throw const FormatException('Invalid D18 key-envelope field length');
      }
    } on FormatException {
      throw const FormatException('Malformed D18 key envelope');
    }
    return value;
  }

  static String _recoveryCode(List<int> bytes) =>
      _prefix + base64UrlEncode(bytes).replaceAll('=', '');

  static SecretKeyData _decodeRecovery(String code) {
    if (!code.startsWith(_prefix)) {
      throw const FormatException('Invalid offline recovery code');
    }
    final text = code.substring(_prefix.length);
    try {
      final bytes = base64Url.decode(base64Url.normalize(text));
      if (bytes.length != 32 || _recoveryCode(bytes) != code) {
        throw const FormatException('Invalid offline recovery code');
      }
      return SecretKeyData(List<int>.of(bytes), overwriteWhenDestroyed: true);
    } on FormatException {
      throw const FormatException('Invalid offline recovery code');
    }
  }

  /// Only call after an independently verified EMPTY encrypted destination.
  /// Callers must atomically preserve this envelope; never overwrite a
  /// historical plaintext database or destroy its only backup.
  static Future<D18VaultKeyEnrollment> createForEmptyVault({
    required PatientVaultScope scope,
    required String passphrase,
  }) async {
    _validateScope(scope);
    _validatePassphrase(passphrase);
    final dataKey = SecretKeyData(_random(32), overwriteWhenDestroyed: true);
    try {
      final salt = _random(16);
      final passKey = await _derive(passphrase, salt);
      late final String passwordWrapped;
      try {
        passwordWrapped = await _seal(
          dataKey.bytes, passKey, scope, 'password',
        );
      } finally {
        passKey.destroy();
      }
      final recoveryBytes = _random(32);
      final recoveryCode = _recoveryCode(recoveryBytes);
      final recoveryKey = SecretKeyData(
        recoveryBytes, overwriteWhenDestroyed: true,
      );
      late final String recoveryWrapped;
      try {
        recoveryWrapped = await _seal(
          dataKey.bytes, recoveryKey, scope, 'recovery',
        );
      } finally {
        recoveryKey.destroy();
      }
      return D18VaultKeyEnrollment._(
        _encode(
          salt: salt,
          passwordWrappedKey: passwordWrapped,
          recoveryWrappedKey: recoveryWrapped,
        ),
        recoveryCode,
        D18VaultKeySession._(dataKey),
      );
    } catch (_) {
      dataKey.destroy();
      rethrow;
    }
  }

  static Future<D18VaultKeySession> unlockWithPassphrase({
    required PatientVaultScope scope,
    required String publicEnvelopeJson,
    required String passphrase,
  }) async {
    _validateScope(scope);
    _validatePassphrase(passphrase);
    final envelope = _parse(publicEnvelopeJson);
    final passKey = await _derive(
      passphrase, base64Decode(envelope['salt'] as String),
    );
    try {
      return D18VaultKeySession._(await _open(
        envelope['passwordWrappedKey'] as String,
        passKey, scope, 'password',
      ));
    } finally {
      passKey.destroy();
    }
  }

  static Future<D18VaultKeySession> unlockWithOfflineRecovery({
    required PatientVaultScope scope,
    required String publicEnvelopeJson,
    required String offlineRecoveryCode,
  }) async {
    _validateScope(scope);
    final envelope = _parse(publicEnvelopeJson);
    final recoveryKey = _decodeRecovery(offlineRecoveryCode);
    try {
      return D18VaultKeySession._(await _open(
        envelope['recoveryWrappedKey'] as String,
        recoveryKey, scope, 'recovery',
      ));
    } finally {
      recoveryKey.destroy();
    }
  }

  /// Rewrap the SAME data key without modifying the clinical database.
  /// A recovery event also issues a NEW independent offline code.
  /// The caller must durably commit the replacement envelope atomically.
  /// Old copies of the old envelope can still accept an old recovery code:
  /// true revocation requires clinical data-key rotation/re-encryption.
  static Future<D18VaultKeyEnrollment> resetAfterRecovery({
    required PatientVaultScope scope,
    required String publicEnvelopeJson,
    required String offlineRecoveryCode,
    required String newPassphrase,
  }) async {
    _validatePassphrase(newPassphrase);
    final original = await unlockWithOfflineRecovery(
      scope: scope,
      publicEnvelopeJson: publicEnvelopeJson,
      offlineRecoveryCode: offlineRecoveryCode,
    );
    try {
      final keyBytes = await original.requireUnlockedKey().extractBytes();
      // Keep the recovered key independent: original.lock() zeroes its buffer.
      final dataKey = SecretKeyData(List<int>.of(keyBytes), overwriteWhenDestroyed: true);
      try {
        final salt = _random(16);
        final passKey = await _derive(newPassphrase, salt);
        late final String passWrapped;
        try {
          passWrapped = await _seal(
            dataKey.bytes, passKey, scope, 'password',
          );
        } finally {
          passKey.destroy();
        }
        final recoveryBytes = _random(32);
        final code = _recoveryCode(recoveryBytes);
        final newRecoveryKey = SecretKeyData(
          recoveryBytes, overwriteWhenDestroyed: true,
        );
        late final String recoveryWrapped;
        try {
          recoveryWrapped = await _seal(
            dataKey.bytes, newRecoveryKey, scope, 'recovery',
          );
        } finally {
          newRecoveryKey.destroy();
        }
        return D18VaultKeyEnrollment._(
          _encode(
            salt: salt,
            passwordWrappedKey: passWrapped,
            recoveryWrappedKey: recoveryWrapped,
          ),
          code,
          D18VaultKeySession._(dataKey),
        );
      } catch (_) {
        dataKey.destroy();
        rethrow;
      }
    } finally {
      original.lock();
    }
  }
}
