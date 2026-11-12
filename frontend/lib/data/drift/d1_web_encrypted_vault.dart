// D1 stage-only encrypted patient vault opener: NOT activated in app main.
// Key custody, recovery and independent security audit are release gates.
// ignore: avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:typed_data';

import 'package:drift/remote.dart';
import 'package:drift/web.dart';
import 'package:web/web.dart' as web;

import 'database.dart';
import 'patient_vault_scope.dart';

typedef D1ScopeNow = PatientVaultScope? Function();
typedef D1EpochNow = int Function();
typedef D1UnlockNow = bool Function();

/// Owns a single remote Web Worker and a generated AppDatabase schema.
/// A lease only proves the testable open/close boundary. It does NOT prove
/// policy for key custody, end-user recovery, crash safety, or multi-tab.
final class D1WebEncryptedVaultLease {
  final AppDatabase _db;
  final web.Worker _worker;
  final Future<String> _flushed;
  final String _owner;
  final int _epoch;
  final D1ScopeNow _scopeNow;
  final D1EpochNow _epochNow;
  final D1UnlockNow _unlockNow;
  bool _retired = false;
  Future<void>? _closing;

  D1WebEncryptedVaultLease._(
    this._db, this._worker, this._flushed, this._owner, this._epoch,
    this._scopeNow, this._epochNow, this._unlockNow,
  );

  bool get valid => !_retired && _unlockNow() &&
      _epochNow() == _epoch && _scopeNow()?.databaseName == _owner;

  AppDatabase get database {
    if (!valid) throw StateError('D1_VAULT_SESSION_REVOKED');
    return _db;
  }

  /// Removes publication immediately, then attempts durable flush. Caller
  /// must await this before treating the revocation as physically completed.
  Future<void> retire() {
    _retired = true;
    return _closing ??= _drain();
  }

  Future<void> _drain() async {
    try {
      await _db.close().timeout(const Duration(seconds: 12));
      if (await _flushed.timeout(const Duration(seconds: 12))
          != 'D1_CIPHER_FLUSHED') {
        throw StateError('D1_VAULT_FLUSH_NOT_PROVEN');
      }
    } finally {
      _worker.terminate();
    }
  }
}

final class D1WebEncryptedVaultAdmission {
  static final _ownerPattern = RegExp(
    r'^amina_vault_v1_(?:native_[1-9][0-9]*|device_[a-f0-9]{32})$');

  /// keyMaterial must be a fresh, authenticated 32-byte key supplied by a
  /// separately reviewed key manager AFTER successful app-lock unlock.
  /// This method consumes and zeroes keyMaterial, including on failure.
  static Future<D1WebEncryptedVaultLease> open({
    required PatientVaultScope scope,
    required int authEpoch,
    required D1ScopeNow currentScope,
    required D1EpochNow currentEpoch,
    required D1UnlockNow isUnlocked,
    required Uint8List keyMaterial,
  }) async {
    web.Worker? worker;
    AppDatabase? opened;
    try {
      if (!_ownerPattern.hasMatch(scope.databaseName) ||
          currentScope()?.databaseName != scope.databaseName ||
          authEpoch < 0 || currentEpoch() != authEpoch || !isUnlocked()) {
        throw StateError('D1_VAULT_AUTH_UNLOCK_REQUIRED');
      }
      if (keyMaterial.length != 32 ||
          keyMaterial.every((byte) => byte == 0)) {
        throw StateError('D1_VAULT_BAD_KEY');
      }
      // This worker refuses all access before key admission and MUST use
      // SQLite3MC's multipleciphers- VFS: never the regular Drift worker.
      worker = web.Worker('d1_patient_encrypted_worker.js'.toJS);
      final ready = Completer<String>();
      final flushed = Completer<String>();
      web.EventStreamProviders.messageEvent.forTarget(worker).listen((event) {
        if (event.data is! JSString) return;
        final message = (event.data as JSString).toDart;
        if (!ready.isCompleted) {
          ready.complete(message);
        } else if (!flushed.isCompleted) {
          flushed.complete(message);
        }
      });
      final ports = web.MessageChannel();
      final keyClone = Uint8List.fromList(keyMaterial);
      final jsKey = keyClone.toJS;
      final request = JSObject()
        ..['owner'] = scope.databaseName.toJS
        ..['epoch'] = authEpoch.toJS
        ..['port'] = ports.port2
        ..['key'] = jsKey;
      // Transfer key buffer, not structured-clone, so the source buffer is
      // detached in the browser. Never put key in URL or localStorage.
      worker.postMessage(request, <JSAny>[
        ports.port2, jsKey['buffer'] as JSArrayBuffer,
      ].toJS);
      keyClone.fillRange(0, keyClone.length, 0);
      final status = await ready.future.timeout(const Duration(seconds: 25));
      if (status != 'D1_CIPHER_READY') {
        throw StateError('D1_VAULT_KEY_OR_CIPHER_REFUSED');
      }
      if (!isUnlocked() || currentEpoch() != authEpoch ||
          currentScope()?.databaseName != scope.databaseName) {
        throw StateError('D1_VAULT_SESSION_CHANGED_DURING_OPEN');
      }
      final remote = await connectToRemoteAndInitialize(
        ports.port1.channel(explicitClose: true), singleClientMode: false,
      );
      opened = AppDatabase.testPatientVault(remote, scope);
      await opened.customSelect('SELECT 1').getSingle();
      if (!isUnlocked() || currentEpoch() != authEpoch ||
          currentScope()?.databaseName != scope.databaseName) {
        throw StateError('D1_VAULT_SESSION_CHANGED_DURING_SCHEMA');
      }
      return D1WebEncryptedVaultLease._(opened, worker, flushed.future,
          scope.databaseName, authEpoch, currentScope, currentEpoch, isUnlocked);
    } catch (_) {
      try { await opened?.close(); } catch (_) { /* refuse */ }
      worker?.terminate();
      rethrow;
    } finally {
      keyMaterial.fillRange(0, keyMaterial.length, 0);
    }
  }
}
