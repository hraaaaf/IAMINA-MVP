import 'dart:async';
import 'dart:typed_data';

import 'patient_vault_scope.dart';

/// D1-A research-only worker interface. No current runtime implementation.
/// The concrete worker MUST prove named SQLite3MC VFS, PRAGMA key before SQL,
/// successful authenticated read and reject wrong key independently. A fake
/// test port is NOT a cryptographic attestation.
abstract interface class D1EncryptedWorkerPort {
  /// Must consume/clone key synchronously before this future completes;
  /// NEVER persist/log/echo it. The caller wipes its temporary buffer.
  Future<void> openWithKey(String ownerName, Uint8List key);
  Future<bool> verifyEncryptedConnection();
  Future<void> close();
}

/// Protocol guard for a future custom Drift encrypted worker. By itself this
/// is NOT an authenticated user, encryption engine or production vault.
final class D1WorkerAdmissionProtocol {
  final String _owner;
  final int _epoch;
  final int Function() _currentEpoch;
  final PatientVaultScope? Function() _currentScope;
  bool _retired = false;
  bool _ready = false;
  int _generation = 0;
  D1EncryptedWorkerPort? _activePort;

  D1WorkerAdmissionProtocol({
    required PatientVaultScope scope,
    required int authEpoch,
    required int Function() currentEpoch,
    required PatientVaultScope? Function() currentScope,
  }) : _owner = scope.databaseName,
       _epoch = authEpoch,
       _currentEpoch = currentEpoch,
       _currentScope = currentScope {
    if (authEpoch < 0 || !(scope.nativeDjangoUserId != null ||
        scope.databaseName.startsWith('amina_vault_v1_device_'))) {
      throw StateError('D1_NO_VERIFIED_CLINICAL_SCOPE');
    }
  }

  bool get ready => _ready && !_retired && _matchesCurrentOwner();

  bool _matchesCurrentOwner() =>
      _currentEpoch() == _epoch &&
      _currentScope()?.databaseName == _owner;

  /// A future adapter must call this only after independent auth+unlock.
  /// The 32-byte material MUST originate from a reviewed, high-entropy KDF.
  /// This method does not itself authenticate the caller or derive a key.
  Future<void> admit({
    required Uint8List keyMaterial,
    required D1EncryptedWorkerPort port,
  }) async {
    if (_retired || _ready || !_matchesCurrentOwner()) {
      throw StateError('D1_WORKER_ADMISSION_DENIED');
    }
    if (keyMaterial.lengthInBytes != 32 ||
        keyMaterial.every((byte) => byte == 0)) {
      throw StateError('D1_WORKER_INVALID_KEY_MATERIAL');
    }
    final generation = ++_generation;
    _activePort = port;
    final transient = Uint8List.fromList(keyMaterial);
    try {
      await port.openWithKey(_owner, transient);
      final cipherOk = await port.verifyEncryptedConnection();
      if (!cipherOk || generation != _generation || _retired ||
          !_matchesCurrentOwner()) {
        throw StateError('D1_WORKER_CIPHER_OR_EPOCH_REJECTED');
      }
      _ready = true;
    } catch (_) {
      _ready = false;
      if (identical(_activePort, port)) _activePort = null;
      await port.close();
      rethrow;
    } finally {
      transient.fillRange(0, transient.length, 0);
    }
  }

  void assertQueryAllowed() {
    if (!ready) throw StateError('D1_WORKER_QUERY_DENIED');
  }

  /// Must be invoked synchronously when auth epoch changes, before awaits.
  void retire() {
    _retired = true;
    _ready = false;
    ++_generation;
    final port = _activePort;
    _activePort = null;
    // Revoke synchronously; release the physical worker asynchronously.
    // The implementation of close() must be idempotent.
    if (port != null) unawaited(port.close());
  }
}
