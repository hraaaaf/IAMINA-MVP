import 'package:drift/drift.dart' show QueryExecutor;

import 'd18_keyed_open_guard.dart';
import 'd18_vault_key_policy.dart';
import 'database.dart';
import 'patient_vault_scope.dart';

/// D18 Web lot 2 — PRE-CUTOVER ONLY. Not wired into AppDatabase.forPatientVault.
///
/// The connector implementation is responsible for proving in its own worker:
/// 1. sqlite3mc was loaded from the pinned audited WASM bundle;
/// 2. PRAGMA key authenticated the physical database *before* exposing SQL;
/// 3. an exclusive origin-wide lock covers the entire connection lifetime;
/// 4. the physical namespace is separate from ALL historical plaintext vaults.
///
/// Metadata below is an assertion FROM A TRUSTED WORKER, not cryptographic proof
/// in itself. Never instantiate a production connector using stock sqlite3.wasm.
/// A caller must make the opening purpose explicit. Reopening an existing
/// encrypted vault must NEVER silently replace it with an empty database.
enum D18CipherVaultOpenIntent { createFresh, reopenExisting }

/// Evidence returned by the TRUSTED encrypted worker after checking the
/// physical ciphertext namespace before any SQLite connection is created.
/// Not a substitute for auditing the worker/storage implementation.
enum D18CipherPhysicalState { absent, existingAuthenticated }

final class D18KeyedCipherWorkerLease {
  final QueryExecutor executor;
  final String authenticatedScopeName;
  final String physicalDatabaseName;
  final String cipherEngine;
  final D18CipherPhysicalState physicalState;
  final Future<void> Function() disposeWorker;

  const D18KeyedCipherWorkerLease({
    required this.executor,
    required this.authenticatedScopeName,
    required this.physicalDatabaseName,
    required this.cipherEngine,
    required this.physicalState,
    required this.disposeWorker,
  });
}

/// The trusted worker MUST receive the intent *before* inspecting/opening
/// IndexedDB. It must reject an existing destination on createFresh and reject
/// an absent or unauthenticated destination on reopenExisting. Returning a
/// lease after destructive creation is NOT a valid implementation.
typedef D18OpenKeyedCipherWorker = Future<D18KeyedCipherWorkerLease> Function(
  PatientVaultScope scope,
  D18CipherVaultOpenIntent intent,
  String expectedDestination,
  List<int> ephemeralKey,
);

/// Disposable, never-published database handle. The clinical host does not
/// consume this type and cannot accidentally switch to this candidate.
final class D18UnpublishedCipherVault {
  final AppDatabase database;
  final Future<void> Function() _disposeWorker;
  bool _closed = false;

  D18UnpublishedCipherVault._(this.database, this._disposeWorker);

  Future<void> close() async {
    if (_closed) return;
    _closed = true;
    try {
      await database.close();
    } finally {
      await _disposeWorker();
    }
  }
}

final class D18PreCutoverCipherAdapter {
  final D18KeyedOpenGuard guard;
  final D18OpenKeyedCipherWorker openVerifiedWorker;

  const D18PreCutoverCipherAdapter({
    required this.guard,
    required this.openVerifiedWorker,
  });

  static String destinationFor(PatientVaultScope scope) =>
      '${scope.databaseName}_d18_cipher_v1';

  /// Only returns an *unpublished* candidate, guarded by independent verified
  /// authentication state before and after the async worker startup.
  /// The caller must close it and may not bind it to patient-facing providers.
  Future<D18UnpublishedCipherVault> openUnpublished({
    required PatientVaultScope scope,
    required D18VaultKeySession keySession,
    required D18CipherVaultOpenIntent intent,
  }) => guard.openUnpublished<D18UnpublishedCipherVault>(
    requestedScope: scope,
    keySession: keySession,
    createUnpublished: (keyBytes) async {
      final lease = await openVerifiedWorker(
        scope, intent, destinationFor(scope), keyBytes);
      AppDatabase? db;
      try {
        // Fail-closed BEFORE any SQL call if the trusted worker reports an
        // unexpected engine or source namespace. Never use a plaintext DB.
        if (lease.authenticatedScopeName != scope.databaseName ||
            lease.physicalDatabaseName != destinationFor(scope) ||
            lease.cipherEngine != 'sqlite3mc') {
          throw StateError('D18 cipher worker identity/engine mismatch');
        }
        // Enforce a BEFORE-OPEN physical-state contract. It must be backed
        // by worker-side storage inspection, not inferred from SQL tables:
        // Drift can initialize an empty database on its first query.
        final expectedPhysicalState =
            intent == D18CipherVaultOpenIntent.createFresh
                ? D18CipherPhysicalState.absent
                : D18CipherPhysicalState.existingAuthenticated;
        if (lease.physicalState != expectedPhysicalState) {
          throw StateError('D18 ciphertext missing or already exists');
        }
        db = AppDatabase.testPatientVault(lease.executor, scope);
        // Exercise the actual Drift schema. The WORKER must already have
        // authenticated and classified this ciphertext before this point.
        final version = await db.customSelect('PRAGMA user_version').getSingle();
        if (version.read<int>('user_version') != db.schemaVersion) {
          throw StateError('D18 encrypted schema version mismatch');
        }
        // A version number alone is insufficient: a physically damaged or
        // incomplete database can advertise v12 with missing tables.
        final actualTables = (await db.customSelect(
          "SELECT name FROM sqlite_master WHERE type='table' "
          "AND name NOT LIKE 'sqlite_%'").get())
          .map((row) => row.read<String>('name')).toSet();
        if (!actualTables.containsAll(const {
          'patient_profiles', 'log_entries', 'chat_messages',
          'medication_events', 'reminders',
          'patient_treatment_declarations_v1',
        })) {
          throw StateError('D18 encrypted schema incomplete');
        }
        final integrity = await db.customSelect('PRAGMA quick_check').getSingle();
        if (integrity.data.values.single != 'ok') {
          throw StateError('D18 encrypted SQLite integrity failed');
        }
        final foreignKeys = await db.customSelect('PRAGMA foreign_key_check').get();
        if (foreignKeys.isNotEmpty) {
          throw StateError('D18 encrypted SQLite foreign key failure');
        }
        return D18UnpublishedCipherVault._(db, lease.disposeWorker);
      } catch (_) {
        try {
          if (db != null) await db.close();
        } finally {
          await lease.disposeWorker();
        }
        rethrow;
      }
    },
    discardUnpublished: (candidate) => candidate.close(),
  );
}
