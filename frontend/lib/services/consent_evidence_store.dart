import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'consent_notice_contract.dart';

class ConsentEvidenceStore {
  static const _versionKey = 'iamina.ai_consent.notice_version';
  static const _hashKey = 'iamina.ai_consent.notice_hash';
  static const _localeKey = 'iamina.ai_consent.notice_locale';

  final FlutterSecureStorage _storage;

  ConsentEvidenceStore({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  Future<ConsentNoticeClaim?> readCurrent() async {
    final values = await Future.wait([
      _storage.read(key: _versionKey),
      _storage.read(key: _hashKey),
      _storage.read(key: _localeKey),
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
    await _storage.write(key: _versionKey, value: claim.version);
    await _storage.write(key: _hashKey, value: claim.noticeHash);
    await _storage.write(key: _localeKey, value: claim.locale);
  }

  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: _versionKey),
      _storage.delete(key: _hashKey),
      _storage.delete(key: _localeKey),
    ]);
  }
}
