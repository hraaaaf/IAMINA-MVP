import 'dart:convert';
import 'dart:math';

import 'package:cryptography/cryptography.dart';
import 'package:drift/drift.dart';

import 'database.dart';
import 'patient_progressive_demographics_store.dart';
import 'patient_vault_scope.dart';
import 'patient_weight_history_store.dart';

/// D18-only export. This deliberately does NOT call LocalBackup.restoreVaultJson:
/// that older whole-vault routine deletes unrelated medical records.
final class D18BackupPreview {
  final String sourceVaultName;
  final int sourceOwner;
  final DateTime createdAtUtc;
  final List<Map<String, dynamic>> declarations;
  final List<Map<String, dynamic>> weights;

  const D18BackupPreview({
    required this.sourceVaultName,
    required this.sourceOwner,
    required this.createdAtUtc,
    required this.declarations,
    required this.weights,
  });

  bool get isDeviceOnly => sourceVaultName.startsWith('amina_vault_v1_device_');
  int get observationCount => weights.length;
  bool get hasDemographics => declarations.isNotEmpty;
}

final class D18EncryptedBackup {
  static const int formatVersion = 1;
  static const int kdfIterations = 600000;
  static const int maximumEnvelopeBytes = 4 * 1024 * 1024;
  static const _aad = 'IAMINA-D18-ENCRYPTED-BACKUP-V1';

  static PatientVaultScope _scope(AppDatabase db) {
    final scope = db.patientVaultScope;
    if (scope == null ||
        scope.databaseName == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('A verified patient vault is required');
    }
    return scope;
  }

  static void _checkPassword(String password) {
    if (password.length < 12 || password.length > 1024) {
      throw ArgumentError('A backup passphrase of at least 12 characters is required');
    }
  }

  static List<Map<String, dynamic>> _objects(Object? input, String name) {
    if (input is! List || input.length > 20000) {
      throw FormatException('Invalid D18 $name');
    }
    return input.map((item) {
      if (item is! Map<String, dynamic>) {
        throw FormatException('Invalid D18 $name row');
      }
      return item;
    }).toList(growable: false);
  }

  static D18BackupPreview _parsePayload(Object? decoded) {
    if (decoded is! Map<String, dynamic> ||
        decoded.keys.toSet().difference({
          'version', 'vault', 'owner', 'createdAtUtc',
          'declarations', 'weights',
        }).isNotEmpty ||
        decoded['version'] != formatVersion ||
        decoded['vault'] is! String ||
        decoded['owner'] is! int ||
        (decoded['owner'] as int) < 1 ||
        decoded['createdAtUtc'] is! String) {
      throw const FormatException('Invalid D18 backup payload');
    }
    final vault = decoded['vault'] as String;
    if (!RegExp(r'^amina_vault_v1_(?:native_[1-9][0-9]*|device_[0-9a-f]{32})$')
        .hasMatch(vault)) {
      throw const FormatException('Unsupported D18 vault identity');
    }
    final owner = decoded['owner'] as int;
    // Device-scoped owners use row 1, Django owners use their server patient ID.
    if (vault.startsWith('amina_vault_v1_device_') && owner != 1) {
      throw const FormatException('Incorrect device vault owner');
    }
    if (vault.startsWith('amina_vault_v1_native_') &&
        owner.toString() != vault.split('_').last) {
      throw const FormatException('Incorrect authenticated vault owner');
    }
    final created = DateTime.parse(decoded['createdAtUtc'] as String);
    if (!created.isUtc) throw const FormatException('Non-UTC backup timestamp');
    final declarations = _objects(decoded['declarations'], 'declarations');
    if (declarations.length > 1) {
      throw const FormatException('Ambiguous D18 declarations');
    }
    for (final row in declarations) {
      PatientProgressiveDemographicsStore.validateBackupRow(row, owner);
    }
    final weights = _objects(decoded['weights'], 'weight observations');
    final seen = <String>{};
    final replacementTargets = <String>{};
    for (final row in weights) {
      PatientWeightHistoryStore.validateBackupRow(row, owner);
      if (!seen.add(row['client_uuid'] as String)) {
        throw const FormatException('Duplicated weight identifier');
      }
      if (row['replaces_uuid'] case final String previous) {
        if (!replacementTargets.add(previous)) {
          throw const FormatException('Multiple corrections of one reading');
        }
      }
    }
    for (final row in weights) {
      final previous = row['replaces_uuid'];
      if (previous != null && !seen.contains(previous)) {
        throw const FormatException('Missing correction ancestor');
      }
    }
    final parents = {
      for (final row in weights)
        row['client_uuid'] as String: row['replaces_uuid'] as String?,
    };
    for (final id in seen) {
      final path = <String>{};
      String? cursor = id;
      while (cursor != null) {
        if (!path.add(cursor)) {
          throw const FormatException('Cyclic D18 correction history');
        }
        cursor = parents[cursor];
      }
    }
    return D18BackupPreview(
      sourceVaultName: vault,
      sourceOwner: owner,
      createdAtUtc: created,
      declarations: declarations,
      weights: weights,
    );
  }

  /// Only a small, versioned public wrapper is outside authenticated encryption.
  /// No patient name, weight, birth year, or patient identifier is in the header.
  static Future<String> exportEncrypted(
    AppDatabase db, {
    required String passphrase,
  }) async {
    _checkPassword(passphrase);
    final scope = _scope(db);
    final demographics = PatientProgressiveDemographicsStore(db);
    final weights = PatientWeightHistoryStore(db);
    final details = await demographics.exportOwnedRows();
    final observations = await weights.exportOwnedRows();
    final payload = <String, Object?>{
      'version': formatVersion,
      'vault': scope.databaseName,
      'owner': db.activeProfileRowId,
      'createdAtUtc': DateTime.now().toUtc().toIso8601String(),
      'declarations': details,
      'weights': observations,
    };
    // Do not let forged or contaminated local data leave in a backup.
    _parsePayload(payload);
    final random = Random.secure();
    final salt = List<int>.generate(16, (_) => random.nextInt(256));
    final key = await Pbkdf2(
      macAlgorithm: Hmac.sha256(),
      iterations: kdfIterations,
      bits: 256,
    ).deriveKeyFromPassword(password: passphrase, nonce: salt);
    final cipher = AesGcm.with256bits();
    final sealed = await cipher.encrypt(
      utf8.encode(jsonEncode(payload)),
      secretKey: key,
      aad: utf8.encode(_aad),
    );
    final envelope = jsonEncode({
      'format': 'iamina-d18-encrypted',
      'version': formatVersion,
      'kdf': 'pbkdf2-hmac-sha256',
      'iterations': kdfIterations,
      'salt': base64Encode(salt),
      'cipher': 'aes-256-gcm',
      'sealed': base64Encode(sealed.concatenation()),
    });
    if (utf8.encode(envelope).length > maximumEnvelopeBytes) {
      throw StateError('D18 backup size limit reached');
    }
    return envelope;
  }

  /// Authentication/decryption does not touch any local database or upload data.
  static Future<D18BackupPreview> open(
    String encryptedFile, {
    required String passphrase,
  }) async {
    if (utf8.encode(encryptedFile).length > maximumEnvelopeBytes ||
        encryptedFile.isEmpty) {
      throw const FormatException('Invalid D18 backup size');
    }
    final wrapper = jsonDecode(encryptedFile);
    if (wrapper is! Map<String, dynamic> ||
        wrapper.keys.toSet().difference({
          'format', 'version', 'kdf', 'iterations', 'salt', 'cipher', 'sealed',
        }).isNotEmpty ||
        wrapper['format'] != 'iamina-d18-encrypted' ||
        wrapper['version'] != formatVersion ||
        wrapper['kdf'] != 'pbkdf2-hmac-sha256' ||
        wrapper['iterations'] != kdfIterations ||
        wrapper['cipher'] != 'aes-256-gcm' ||
        wrapper['salt'] is! String ||
        wrapper['sealed'] is! String) {
      throw const FormatException('Unsupported D18 encrypted backup');
    }
    // Never let an untrusted backup choose arbitrarily expensive KDF settings.
    final salt = base64Decode(wrapper['salt'] as String);
    final bytes = base64Decode(wrapper['sealed'] as String);
    if (salt.length != 16 || bytes.length < 29) {
      throw const FormatException('Malformed D18 encrypted backup');
    }
    final key = await Pbkdf2(
      macAlgorithm: Hmac.sha256(),
      iterations: kdfIterations,
      bits: 256,
    ).deriveKeyFromPassword(password: passphrase, nonce: salt);
    final plain = await AesGcm.with256bits().decrypt(
      SecretBox.fromConcatenation(
        bytes, nonceLength: 12, macLength: 16,
      ),
      secretKey: key,
      aad: utf8.encode(_aad),
    );
    return _parsePayload(jsonDecode(utf8.decode(plain)));
  }

  /// Fail closed. Only D18 tables are touched, only when BOTH are empty.
  /// A device-to-device transfer requires a separate explicit confirmation.
  static Future<void> restoreInto(
    AppDatabase db,
    D18BackupPreview preview, {
    bool allowDeviceTransfer = false,
  }) async {
    final scope = _scope(db);
    final target = scope.databaseName;
    final sameOwner = target == preview.sourceVaultName &&
        db.activeProfileRowId == preview.sourceOwner;
    final explicitDeviceTransfer = allowDeviceTransfer &&
        preview.isDeviceOnly &&
        target.startsWith('amina_vault_v1_device_') &&
        db.activeProfileRowId == 1;
    if (!sameOwner && !explicitDeviceTransfer) {
      throw StateError('Backup owner mismatch');
    }
    // Validate again in case a caller mutated the preview after opening.
    _parsePayload({
      'version': formatVersion,
      'vault': preview.sourceVaultName,
      'owner': preview.sourceOwner,
      'createdAtUtc': preview.createdAtUtc.toUtc().toIso8601String(),
      'declarations': preview.declarations,
      'weights': preview.weights,
    });
    final demographics = PatientProgressiveDemographicsStore(db);
    final weightStore = PatientWeightHistoryStore(db);
    await demographics.prepareBackupTable();
    await weightStore.prepareBackupTable();
    final owner = db.activeProfileRowId;
    await db.transaction(() async {
      if ((await demographics.read()) != null ||
          (await weightStore.recent(limit: 1)).isNotEmpty) {
        throw StateError('Existing D18 information must never be overwritten');
      }
      for (final source in preview.declarations) {
        final row = Map<String, dynamic>.of(source)..['user_id'] = owner;
        PatientProgressiveDemographicsStore.validateBackupRow(row, owner);
        await db.customStatement('''
          INSERT INTO patient_progressive_demographics_v1
            (user_id, birth_year, gender_identity, provenance, updated_at_utc)
          VALUES (?, ?, ?, ?, ?)
        ''', [
          owner, row['birth_year'], row['gender_identity'],
          row['provenance'], row['updated_at_utc'],
        ]);
      }
      for (final source in preview.weights) {
        final row = Map<String, dynamic>.of(source)..['user_id'] = owner;
        PatientWeightHistoryStore.validateBackupRow(row, owner);
        await db.customStatement('''
          INSERT INTO patient_weight_observations_v1
            (user_id, client_uuid, value_hundredths, unit,
             kilograms_hundredths, measured_at_utc, replaces_uuid, provenance)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
          owner, row['client_uuid'], row['value_hundredths'],
          row['unit'], row['kilograms_hundredths'],
          row['measured_at_utc'], row['replaces_uuid'], row['provenance'],
        ]);
      }
      final actualDetails = await demographics.exportOwnedRows();
      final actualWeights = await weightStore.exportOwnedRows();
      if (jsonEncode(actualDetails) != jsonEncode(
            preview.declarations.map((r) => Map<String, dynamic>.of(r)
              ..['user_id'] = owner).toList(),
          ) ||
          jsonEncode(actualWeights) != jsonEncode(
            preview.weights.map((r) => Map<String, dynamic>.of(r)
              ..['user_id'] = owner).toList(),
          )) {
        throw StateError('Restored data failed verification; transaction rolled back');
      }
    });
  }
}
