// D1 clinical encrypted-vault CANDIDATE. Not wired to production admission.
// Web only. Cryptographic transport relies on native WebCrypto + sqlite3mc.
// Do not use for patients until recovery/legacy/PWA/FUE/security audit GO.
import 'dart:convert';
import 'dart:html' as html;
import 'dart:async';
import 'dart:js_interop';
import 'dart:math';

import 'package:drift/drift.dart';
import 'package:drift/wasm.dart';
import 'package:sqlite3/wasm.dart';

import 'database.dart';
import 'patient_vault_scope.dart';

@JS('IaminaD1CryptoCandidate.encrypt')
external JSPromise<JSString> _nativeSeal(
  JSString recovery, JSString key, JSString salt, JSString iv, JSString owner,
);
@JS('IaminaD1CryptoCandidate.decrypt')
external JSPromise<JSString> _nativeUnseal(
  JSString recovery, JSString ciphertext, JSString salt, JSString iv, JSString owner,
);
@JS('IaminaD1CryptoCandidate.indexedDbNames')
external JSPromise<JSString> _nativeStoreNames();


final class WebVaultEnrollment {
  final String recoveryCode;
  const WebVaultEnrollment(this.recoveryCode);
}

final class WebVaultKey {
  final String _databaseName;
  final List<int> _dataKey;
  bool _retired = false;
  WebVaultKey._(this._databaseName, this._dataKey);
  void retire() {
    _retired = true;
    for (var i = 0; i < _dataKey.length; i++) {
      _dataKey[i] = 0;
    }
  }
  String cipherPassphraseFor(PatientVaultScope scope) {
    if (_retired || _databaseName != scope.databaseName) {
      throw StateError('web_vault_key_owner_or_epoch_invalid');
    }
    return base64UrlEncode(_dataKey);
  }
}

/// Testable provisioning layer. Caller must separately prove authenticated
/// identity, app-lock authorization, secure recovery acknowledgement and an
/// old-PWA writer fence. None is silently inferred from possession of a key.
final class WebPatientVaultCipherCandidate {
  static const _metadataPrefix = 'iamina_d1_wrapped_vault_v1_';
  static const _databasePrefix = 'iamina_d1_encrypted_vault_v1_';
  static const _format = 'iamina-d1-aes-gcm-owner-bound-v1';
  static const _iterations = 310000;
  static const _wasmUrl = 'sqlite3mc.wasm';
  final String _wasmPath;

  const WebPatientVaultCipherCandidate({String wasmPath = _wasmUrl})
      : _wasmPath = wasmPath;

  static bool _validScope(PatientVaultScope scope) =>
      scope.databaseName.startsWith('amina_vault_v1_native_') ||
      scope.databaseName.startsWith('amina_vault_v1_device_');

  static String _ownerName(PatientVaultScope scope) {
    if (!_validScope(scope)) {
      throw StateError('clinical_owner_scope_required');
    }
    return scope.databaseName;
  }

  static String _metadataKey(PatientVaultScope scope) =>
      _metadataPrefix + _ownerName(scope);

  static String _cipherStore(PatientVaultScope scope) =>
      _databasePrefix + _ownerName(scope);

  // Inventory ALL historical unencrypted patient namespaces in the same
  // browser profile, not only the active owner. Another patient's stale PWA
  // could still persist plaintext while the active owner uses encryption.
  // The nonclinical audit-only namespace is deliberately excluded.
  static bool _hasLegacyPatientStore(Set<String> names) => names.any(
    (name) => name == 'amina' ||
        name.startsWith('amina_vault_v1_native_') ||
        name.startsWith('amina_vault_v1_device_'),
  );

  static List<int> _randomBytes(int length) {
    final source = Random.secure();
    return List<int>.generate(length, (_) => source.nextInt(256));
  }

  // A pending enrollment may be consumed only once by the SAME tab and
  // exact freshly-created envelope. localStorage is attacker-editable and
  // cannot authorize a replay of pending after crash, logout or reload.
  // Fail closed rather than silently create an empty replacement vault.
  static final Map<String, String> _freshPendingEnvelopes = {};
  static Future<void>? _scriptLoad;

  static Future<void> _ensureWebCrypto() =>
      _scriptLoad ??= _loadWebCrypto();

  static Future<void> _loadWebCrypto() async {
    final script = html.ScriptElement()
      ..src = 'd1_vault_crypto_candidate.js';
    final completion = Completer<void>();
    script.onLoad.first.then((_) {
      if (!completion.isCompleted) completion.complete();
    });
    script.onError.first.then((_) {
      if (!completion.isCompleted) {
        completion.completeError(StateError('web_vault_crypto_script_unavailable'));
      }
    });
    html.document.head!.append(script);
    await completion.future;
  }

  static Future<List<int>> _encryptKey(
    List<int> key, List<int> recovery, List<int> salt, List<int> iv,
    String owner,
  ) async {
    await _ensureWebCrypto();
    final result = await _nativeSeal(
      base64UrlEncode(recovery).toJS, base64UrlEncode(key).toJS,
      base64UrlEncode(salt).toJS, base64UrlEncode(iv).toJS, owner.toJS,
    ).toDart;
    return base64Url.decode(base64Url.normalize(result.toDart));
  }

  static Future<List<int>> _decryptKey(
    List<int> ciphertext, List<int> recovery, List<int> salt, List<int> iv,
    String owner,
  ) async {
    await _ensureWebCrypto();
    final result = await _nativeUnseal(
      base64UrlEncode(recovery).toJS, base64UrlEncode(ciphertext).toJS,
      base64UrlEncode(salt).toJS, base64UrlEncode(iv).toJS, owner.toJS,
    ).toDart;
    return base64Url.decode(base64Url.normalize(result.toDart));
  }

  static List<int> _decodeRecovery(String recoveryCode) {
    if (!RegExp(r'^[A-Za-z0-9_-]{43}=?$').hasMatch(recoveryCode)) {
      throw StateError('web_vault_recovery_code_invalid');
    }
    final bytes = base64Url.decode(base64Url.normalize(recoveryCode));
    if (bytes.length != 32) {
      throw StateError('web_vault_recovery_code_invalid');
    }
    return bytes;
  }

  static Map<String, dynamic> _parseEnvelope(String raw, String owner) {
    final envelope = jsonDecode(raw);
    if (envelope is! Map<String, dynamic> ||
        envelope['format'] != _format ||
        envelope['owner'] != owner ||
        envelope['iterations'] != _iterations ||
        envelope['salt'] is! String ||
        envelope['iv'] is! String ||
        envelope['ciphertext'] is! String ||
        (envelope['state'] != 'pending' && envelope['state'] != 'sealed')) {
      throw StateError('web_vault_envelope_untrusted');
    }
    return envelope;
  }

  /// Explicit fresh enrollment only. Absolutely no legacy/previous local DB
  /// is deleted, overwritten or silently assigned to this owner.
  Future<WebVaultEnrollment> enrollEmptyScope(PatientVaultScope scope) async {
    final owner = _ownerName(scope);
    if (html.window.localStorage.containsKey(_metadataKey(scope))) {
      throw StateError('web_vault_already_enrolled');
    }
    await _ensureWebCrypto();
    final serializedNames = await _nativeStoreNames().toDart;
    final names = (jsonDecode(serializedNames.toDart) as List)
        .map((value) => value.toString())
        .toSet();
    if (_hasLegacyPatientStore(names) ||
        names.contains(_cipherStore(scope))) {
      throw StateError('web_vault_legacy_data_quarantined');
    }
    final recovery = _randomBytes(32);
    final key = _randomBytes(32);
    final salt = _randomBytes(16);
    final iv = _randomBytes(12);
    try {
      final ciphertext = await _encryptKey(key, recovery, salt, iv, owner);
      final envelope = jsonEncode({
        'format': _format,
        'owner': owner,
        'iterations': _iterations,
        'state': 'pending',
        'salt': base64UrlEncode(salt),
        'iv': base64UrlEncode(iv),
        'ciphertext': base64UrlEncode(ciphertext),
      });
      if (html.window.localStorage.containsKey(_metadataKey(scope))) {
        throw StateError('web_vault_concurrent_enrollment');
      }
      html.window.localStorage[_metadataKey(scope)] = envelope;
      _freshPendingEnvelopes[owner] = envelope;
      return WebVaultEnrollment(base64UrlEncode(recovery).replaceAll('=', ''));
    } finally {
      key.fillRange(0, key.length, 0);
      recovery.fillRange(0, recovery.length, 0);
    }
  }

  /// Only accepts the recovery material independently handed to the owner.
  /// It never creates missing ciphertext or a replacement empty vault.
  Future<WebVaultKey> unlock(PatientVaultScope scope, String recoveryCode) async {
    final owner = _ownerName(scope);
    final raw = html.window.localStorage[_metadataKey(scope)];
    if (raw == null) throw StateError('web_vault_not_enrolled');
    final envelope = _parseEnvelope(raw, owner);
    final recovery = _decodeRecovery(recoveryCode);
    try {
      final key = await _decryptKey(
        base64Url.decode(base64Url.normalize(envelope['ciphertext'] as String)),
        recovery,
        base64Url.decode(base64Url.normalize(envelope['salt'] as String)),
        base64Url.decode(base64Url.normalize(envelope['iv'] as String)),
        owner,
      );
      if (key.length != 32) throw StateError('web_vault_key_invalid');
      return WebVaultKey._(owner, key);
    } catch (_) {
      throw StateError('web_vault_recovery_rejected');
    } finally {
      recovery.fillRange(0, recovery.length, 0);
    }
  }

  /// Standalone candidate for integration tests of the REAL AppDatabase
  /// schema; never wired to unauthenticated or production patient UI.
  Future<AppDatabase> openCandidateDatabase(
      PatientVaultScope scope, WebVaultKey key, {
      QueryInterceptor? admissionGuard,
  }) async {
    final owner = _ownerName(scope);
    final passphrase = key.cipherPassphraseFor(scope);
    final headerKey = _metadataKey(scope);
    final rawHeader = html.window.localStorage[headerKey];
    if (rawHeader == null) throw StateError('web_vault_not_enrolled');
    final envelope = _parseEnvelope(rawHeader, owner);
    await _ensureWebCrypto();
    final serializedNames = await _nativeStoreNames().toDart;
    final names = (jsonDecode(serializedNames.toDart) as List)
        .map((value) => value.toString()).toSet();
    // A sealed vault must NEVER be recreated as an empty database if its
    // ciphertext is missing (browser eviction, corrupted profile, rollback).
    // Historic plaintext stores also stay quarantined and untouched.
    if (_hasLegacyPatientStore(names)) {
      throw StateError('web_vault_legacy_data_quarantined');
    }
    if (envelope['state'] == 'sealed' &&
        !names.contains(_cipherStore(scope))) {
      throw StateError('web_vault_ciphertext_missing_recovery_required');
    }
    if (envelope['state'] == 'pending') {
      final freshHeader = _freshPendingEnvelopes.remove(owner);
      if (freshHeader == null || freshHeader != rawHeader) {
        throw StateError('web_vault_pending_enrollment_replay_blocked');
      }
    }

    final sqlite = await WasmSqlite3.loadFromUrl(Uri.parse(_wasmPath));
    final fs = await IndexedDbFileSystem.open(dbName: _cipherStore(scope));
    sqlite.registerVirtualFileSystem(fs, makeDefault: true);
    final literal = passphrase.replaceAll("'", "''");
    // Unlike WasmDatabase.opened, providing fileSystem here ensures IndexedDB
    // changes are durably flushed before async Drift query completion.
    final executor = WasmDatabase(
      sqlite3: sqlite,
      path: '/vault.db',
      fileSystem: fs,
      setup: (raw) {
        if (raw.select('PRAGMA cipher').isEmpty) {
          throw StateError('web_vault_encryption_unavailable');
        }
        // Pinned sqlite3MC WASM includes sqleet ChaCha20-Poly1305 with
        // authenticated per-page tags. No plaintext or weaker fallback.
        raw.execute("PRAGMA cipher = 'chacha20';");
        raw.execute('PRAGMA legacy = 0;');
        final selected = raw.select('PRAGMA cipher');
        if (selected.isEmpty ||
            selected.single.values.first.toString().toLowerCase() !=
                'chacha20') {
          throw StateError('web_vault_authenticated_cipher_unavailable');
        }
        raw.execute("PRAGMA key = '$literal';");
      },
    );
    // Production-compatible guard hook for the future authenticated
    // recovery path. The default fixture remains unchanged for isolated
    // cryptographic feasibility probes; only the explicit-admission bridge
    // installs the sticky, revocable SQL interceptor.
    final guardedExecutor = admissionGuard == null
        ? executor : executor.interceptWith(admissionGuard);
    final database = AppDatabase.testPatientVault(guardedExecutor, scope);
    try {
      await database.customSelect('SELECT 1').getSingle();
      // Race or tampering of the owner envelope invalidates this attempt.
      if (html.window.localStorage[headerKey] != rawHeader) {
        throw StateError('web_vault_concurrent_metadata_change');
      }
      if (envelope['state'] == 'pending') {
        envelope['state'] = 'sealed';
        html.window.localStorage[headerKey] = jsonEncode(envelope);
      }
      return database;
    } catch (_) {
      await database.close();
      rethrow;
    }
  }

  static String diagnosticMetadataKey(PatientVaultScope scope) =>
      _metadataKey(scope);
  static String diagnosticStoreName(PatientVaultScope scope) =>
      _cipherStore(scope);
}
