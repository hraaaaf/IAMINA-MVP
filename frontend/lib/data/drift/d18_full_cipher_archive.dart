// D18 Web stage 4/6 — sealed FULL physical ciphertext archive candidate.
// PRE-CUTOVER ONLY. No clinical integration, storage import, or migration.
// This class CANNOT attest that input bytes came from sqlite3mc. Only the
// separately audited worker can provide a consistent, authenticated snapshot.
// Do not use the D18EncryptedBackup (profile/weights only) as a vault backup.
import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:cryptography/cryptography.dart';

import 'patient_vault_scope.dart';

/// Decrypted *already encrypted* SQLite bytes plus the public DEK envelope.
/// Never write these bytes directly to the production IndexedDB store.
/// Re-import requires its own exclusive Web Lock, missing-destination proof,
/// authenticated sqlite3mc open and full schema/integrity verification.
final class D18FullCipherArchiveContents {
  final String vaultName;
  final String publicKeyEnvelopeJson;
  final Uint8List encryptedSqliteBytes;
  final int schemaVersion;

  const D18FullCipherArchiveContents({
    required this.vaultName,
    required this.publicKeyEnvelopeJson,
    required this.encryptedSqliteBytes,
    required this.schemaVersion,
  });
}

/// A second AEAD layer protects both the *existing* SQLite ciphertext and the
/// public envelope when copied away from the browser. This protects archive
/// tampering and ties it to a specific existing patient vault namespace.
/// Small, bounded pilot format: the eventual clinical export needs streaming.
abstract final class D18FullCipherArchive {
  static const String format = 'iamina-d18-whole-ciphertext-backup';
  static const int version = 1;
  static const int schemaVersion = 12;
  static const int kdfIterations = 600000;
  static const int maxCiphertextBytes = 16 * 1024 * 1024;
  static const int maxArchiveChars = 26 * 1024 * 1024;
  static const String _aadPrefix = 'IAMINA-D18-FULL-CIPHER-BACKUP-V1|';
  static final RegExp _name = RegExp(
    r'^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$',
  );

  static String _scope(PatientVaultScope scope) {
    final value = scope.databaseName;
    if (!_name.hasMatch(value) ||
        value == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('D18 full archive requires verified patient scope');
    }
    // The caller MUST separately authenticate the actual principal and epoch.
    return value;
  }

  static void _passphrase(String password) {
    if (password.runes.length < 12 || password.runes.length > 1024) {
      throw ArgumentError('Backup passphrase must have 12 to 1024 characters');
    }
  }

  static void _validateKeyEnvelope(String content) {
    if (content.isEmpty || content.length > 4096) {
      throw const FormatException('Invalid D18 public key envelope size');
    }
    final decoded = jsonDecode(content);
    const fields = {
      'format', 'version', 'kdf', 'iterations', 'salt', 'cipher',
      'passwordWrappedKey', 'recoveryWrappedKey',
    };
    if (decoded is! Map<String, dynamic> ||
        decoded.keys.toSet().difference(fields).isNotEmpty ||
        fields.difference(decoded.keys.toSet()).isNotEmpty ||
        decoded['format'] != 'iamina-d18-vault-key-envelope' ||
        decoded['version'] != 1 ||
        decoded['kdf'] != 'pbkdf2-hmac-sha256' ||
        decoded['iterations'] != kdfIterations ||
        decoded['cipher'] != 'aes-256-gcm' ||
        decoded['salt'] is! String ||
        decoded['passwordWrappedKey'] is! String ||
        decoded['recoveryWrappedKey'] is! String) {
      throw const FormatException('Invalid D18 public key envelope');
    }
    try {
      if (base64Decode(decoded['salt'] as String).length != 16 ||
          base64Decode(decoded['passwordWrappedKey'] as String).length != 60 ||
          base64Decode(decoded['recoveryWrappedKey'] as String).length != 60) {
        throw const FormatException('Invalid D18 public key envelope bytes');
      }
    } on FormatException {
      throw const FormatException('Invalid D18 public key envelope bytes');
    }
  }

  static void _validateCiphertext(List<int> raw) {
    if (raw.length < 1024 || raw.length > maxCiphertextBytes) {
      throw const FormatException('D18 physical ciphertext size invalid');
    }
    if (String.fromCharCodes(raw.take(16)) == 'SQLite format 3\u0000') {
      throw const FormatException('Plaintext SQLite may not be archived');
    }
    // This is NOT cipher attestation; reject is only a basic safety check.
    // Actual restoration must prove the key and schema using sqlite3mc.
  }

  static Future<SecretKey> _derive(String password, List<int> salt) =>
      Pbkdf2(macAlgorithm: Hmac.sha256(),
        iterations: kdfIterations, bits: 256)
        .deriveKeyFromPassword(password: password, nonce: salt);

  /// Construct only from a known-good snapshot whose writer is fully closed,
  /// and only after an off-browser backup destination has been chosen.
  static Future<String> seal({
    required PatientVaultScope scope,
    required String publicKeyEnvelopeJson,
    required Uint8List encryptedSqliteBytes,
    required String backupPassphrase,
  }) async {
    final vault = _scope(scope);
    _passphrase(backupPassphrase);
    _validateKeyEnvelope(publicKeyEnvelopeJson);
    _validateCiphertext(encryptedSqliteBytes);
    final salt = List<int>.generate(16, (_) => Random.secure().nextInt(256));
    final key = await _derive(backupPassphrase, salt);
    try {
      final payload = jsonEncode({
        'version': version,
        'vault': vault,
        'sqliteSchemaVersion': schemaVersion,
        'publicKeyEnvelope': publicKeyEnvelopeJson,
        'physicalCiphertext': base64Encode(encryptedSqliteBytes),
      });
      final sealed = await AesGcm.with256bits().encrypt(
        utf8.encode(payload), secretKey: key,
        aad: utf8.encode('$_aadPrefix$vault'),
      );
      final archive = jsonEncode({
        'format': format,
        'version': version,
        'kdf': 'pbkdf2-hmac-sha256',
        'iterations': kdfIterations,
        'salt': base64Encode(salt),
        'cipher': 'aes-256-gcm',
        'sealed': base64Encode(sealed.concatenation()),
      });
      if (archive.length > maxArchiveChars) {
        throw StateError('D18 full archive pilot size exceeded');
      }
      return archive;
    } finally {
      key.destroy();
    }
  }

  /// Decrypts in memory only. Does not touch IndexedDB, any worker, or a
  /// patient database. Must NOT re-enrol or overwrite an existing destination.
  static Future<D18FullCipherArchiveContents> open({
    required PatientVaultScope expectedScope,
    required String archive,
    required String backupPassphrase,
  }) async {
    final vault = _scope(expectedScope);
    _passphrase(backupPassphrase);
    if (archive.isEmpty || archive.length > maxArchiveChars) {
      throw const FormatException('D18 full archive size invalid');
    }
    final outer = jsonDecode(archive);
    const expectedFields = {
      'format', 'version', 'kdf', 'iterations', 'salt', 'cipher', 'sealed',
    };
    if (outer is! Map<String, dynamic> ||
        outer.keys.toSet().difference(expectedFields).isNotEmpty ||
        expectedFields.difference(outer.keys.toSet()).isNotEmpty ||
        outer['format'] != format ||
        outer['version'] != version ||
        outer['kdf'] != 'pbkdf2-hmac-sha256' ||
        outer['iterations'] != kdfIterations ||
        outer['cipher'] != 'aes-256-gcm' ||
        outer['salt'] is! String ||
        outer['sealed'] is! String) {
      throw const FormatException('Unsupported D18 full archive');
    }
    final salt = base64Decode(outer['salt'] as String);
    final cipher = base64Decode(outer['sealed'] as String);
    if (salt.length != 16 || cipher.length < 29 ||
        cipher.length > maxArchiveChars) {
      throw const FormatException('Malformed D18 full archive');
    }
    final key = await _derive(backupPassphrase, salt);
    try {
      final plaintext = await AesGcm.with256bits().decrypt(
        SecretBox.fromConcatenation(
          cipher, nonceLength: 12, macLength: 16,
        ),
        secretKey: key,
        aad: utf8.encode('$_aadPrefix$vault'),
      );
      final value = jsonDecode(utf8.decode(plaintext));
      const innerFields = {
        'version', 'vault', 'sqliteSchemaVersion',
        'publicKeyEnvelope', 'physicalCiphertext',
      };
      if (value is! Map<String, dynamic> ||
          value.keys.toSet().difference(innerFields).isNotEmpty ||
          innerFields.difference(value.keys.toSet()).isNotEmpty ||
          value['version'] != version ||
          value['vault'] != vault ||
          value['sqliteSchemaVersion'] != schemaVersion ||
          value['publicKeyEnvelope'] is! String ||
          value['physicalCiphertext'] is! String) {
        throw const FormatException('D18 full archive scope/schema mismatch');
      }
      final keyEnvelope = value['publicKeyEnvelope'] as String;
      _validateKeyEnvelope(keyEnvelope);
      final bytes = base64Decode(value['physicalCiphertext'] as String);
      _validateCiphertext(bytes);
      return D18FullCipherArchiveContents(
        vaultName: vault,
        publicKeyEnvelopeJson: keyEnvelope,
        encryptedSqliteBytes: Uint8List.fromList(bytes),
        schemaVersion: schemaVersion,
      );
    } finally {
      key.destroy();
    }
  }
}
