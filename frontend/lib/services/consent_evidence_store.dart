import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../data/drift/patient_vault_scope.dart';
import 'consent_notice_contract.dart';

class ConsentEvidenceStore {
  static const _versionKey = 'iamina.ai_consent.notice_version';
  static const _hashKey = 'iamina.ai_consent.notice_hash';
  static const _localeKey = 'iamina.ai_consent.notice_locale';
  static const _withdrawalPendingKey = 'iamina.ai_consent.withdrawal_pending';

  final FlutterSecureStorage _storage;
  final String? _vaultNamespace;

  // Legacy only: unscoped notice evidence is never implicitly assigned to a
  // future native Django account or new local-device vault.
  ConsentEvidenceStore({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage(),
      _vaultNamespace = null;

  ConsentEvidenceStore.forPatientVault(
    PatientVaultScope scope, {
    FlutterSecureStorage? storage,
  }) : _storage = storage ?? const FlutterSecureStorage(),
       _vaultNamespace = scope.databaseName;

  String _key(String legacyKey) {
    final vault = _vaultNamespace;
    return vault == null ? legacyKey : '$legacyKey.v2.$vault';
  }

  // Persist an owner-scoped stop marker before contacting the remote API:
  // an offline/failed DELETE must not resurrect AI processing on next reload.
  Future<bool> hasWithdrawalPending() async =>
      await _storage.read(key: _key(_withdrawalPendingKey)) == 'true';

  Future<void> markWithdrawalPending() async =>
      _storage.write(key: _key(_withdrawalPendingKey), value: 'true');

  Future<void> clearWithdrawalPending() async =>
      _storage.delete(key: _key(_withdrawalPendingKey));

  Future<ConsentNoticeClaim?> readCurrent() async {
    if (await hasWithdrawalPending()) return null;
    final values = await Future.wait([
      _storage.read(key: _key(_versionKey)),
      _storage.read(key: _key(_hashKey)),
      _storage.read(key: _key(_localeKey)),
    ]);
    final version = values[0];
    final hash = values[1];
    final locale = values[2];
    if (!ConsentNoticeContract.isCurrent(
      versionValue: version,
      noticeHash: hash,
      locale: locale,
    )) {
      return null;
    }
    return ConsentNoticeClaim(
      version: version!,
      noticeHash: hash!,
      locale: ConsentNoticeContract.normalizeLocale(locale!),
    );
  }

  Future<bool> hasCurrentEvidence() async => (await readCurrent()) != null;

  Future<void> write(ConsentNoticeClaim claim) async {
    if (!ConsentNoticeContract.isCurrent(
      versionValue: claim.version,
      noticeHash: claim.noticeHash,
      locale: claim.locale,
    )) {
      throw ArgumentError('Consent evidence does not match the current notice');
    }
    await _storage.write(key: _key(_versionKey), value: claim.version);
    await _storage.write(key: _key(_hashKey), value: claim.noticeHash);
    await _storage.write(key: _key(_localeKey), value: claim.locale);
  }

  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: _key(_versionKey)),
      _storage.delete(key: _key(_hashKey)),
      _storage.delete(key: _key(_localeKey)),
    ]);
  }
}
