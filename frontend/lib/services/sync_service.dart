import 'dart:async';
import 'dart:convert';
import 'dart:developer' as developer;

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

import '../data/drift/database.dart';
import '../data/drift/patient_treatment_declaration_store.dart';
import 'auth_epoch.dart';
import 'api_client.dart';
import 'sync_api_contract.dart';

enum SyncUiState { checking, upToDate, pending, syncing, offline, error }

typedef SyncFailureLogger =
    void Function(String operation, String errorType, StackTrace stackTrace);

Map<String, Object> journalContextFieldsForSync({
  required bool isSick,
  required bool isStressed,
  required bool isActive,
  required String? sleepQuality,
  required int? fatigueLevel,
}) {
  return <String, Object>{
    if (isSick) 'is_sick': 'yes',
    if (isStressed) 'stressed': 'yes',
    if (isActive) 'exercised': 'yes',
    if (sleepQuality == 'bad') 'sleep_quality': 'bad',
    if ((fatigueLevel ?? 0) > 0) 'fatigue_level': 'tired',
  };
}

class SyncService {
  final AppDatabase _db;
  final ApiClient _apiClient;
  final SyncFailureLogger _failureLogger;
  final bool Function()? _canUseNetwork;
  final Connectivity _connectivity = Connectivity();
  // One synchronizer is bound to one auth epoch: a retired session may never
  // upload its pending medical rows under a new patient's bearer.
  final int _ownerAuthEpoch = AuthEpoch.value;
  bool _disposed = false;
  bool _treatmentSyncing = false;
  bool get _sessionActive =>
      !_disposed &&
      AuthEpoch.value == _ownerAuthEpoch &&
      (_canUseNetwork?.call() ?? true);
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;

  /// Kept for compatibility with existing consumers that only need activity.
  final ValueNotifier<bool> isSyncing = ValueNotifier<bool>(false);

  /// Authoritative patient-facing state. UI must never infer synchronization
  /// from a decorative icon or from local data existing on the device.
  final ValueNotifier<SyncUiState> state = ValueNotifier<SyncUiState>(
    SyncUiState.checking,
  );

  SyncService(
    this._db,
    this._apiClient, {
    SyncFailureLogger? failureLogger,
    bool Function()? canUseNetwork,
  }) : _failureLogger = failureLogger ?? _defaultFailureLogger,
       _canUseNetwork = canUseNetwork;

  static void _defaultFailureLogger(
    String operation,
    String errorType,
    StackTrace stackTrace,
  ) {
    developer.log(
      'Safe sync fallback invoked for $errorType.',
      name: 'iamina.sync.$operation',
      stackTrace: stackTrace,
    );
  }

  void init() {
    if (!_sessionActive) return;
    unawaited(_resumeTreatmentOnAuthenticatedStartup());
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen((
      results,
    ) {
      if (!_sessionActive) return;
      if (_isOffline(results)) {
        state.value = SyncUiState.offline;
        return;
      }
      unawaited(syncPendingLogs());
      unawaited(sendPendingTreatmentDeclaration());
    });
  }

  /// Started only by the unlocked, native-authenticated vault host.
  /// Restore never overwrites a pending local edit. Then retry any durable
  /// outbox row and check combined log/treatment status.
  /// The host calls this when an app-lock is unlocked again. Retired vaults
  /// and sessions must never resume, even if an old connectivity event fires.
  Future<void> resumeAfterUnlock() async {
    if (!_sessionActive) return;
    await _resumeTreatmentOnAuthenticatedStartup();
    if (!_sessionActive) return;
    await syncPendingLogs();
  }

  Future<void> _resumeTreatmentOnAuthenticatedStartup() async {
    await restorePatientTreatmentDeclaration();
    if (!_sessionActive) return;
    await sendPendingTreatmentDeclaration();
    if (!_sessionActive) return;
    await refreshState();
  }

  bool _isOffline(List<ConnectivityResult> results) {
    return results.isEmpty ||
        results.every((result) => result == ConnectivityResult.none);
  }

  /// Recover an explicit patient declaration on a newly authenticated device.
  /// Never treat an empty server default as a patient-reported answer.
  Future<void> restorePatientTreatmentDeclaration() async {
    if (!_sessionActive || _db.patientVaultScope?.nativeDjangoUserId == null) {
      return;
    }
    try {
      final store = PatientTreatmentDeclarationStore(_db);
      if (await store.read() != null || !_sessionActive) return;
      final profile = await _apiClient.getProfile();
      if (!_sessionActive || profile == null) return;
      if (profile['treatment_declaration_source'] != 'patient_declared' ||
          profile['treatment_declaration_version'] != 1) return;
      final status = profile['treatment_declaration_state'];
      final codes = profile['treatment_declarations'];
      final timestamp = profile['treatment_declaration_updated_at'];
      if (status is! String || codes is! List ||
          codes.any((item) => item is! String) ||
          timestamp is! String) return;
      final updatedAt = DateTime.tryParse(timestamp);
      if (updatedAt == null || !_sessionActive) return;
      await store.restoreRemoteIfAbsent(
        state: status,
        codes: codes.cast<String>(),
        updatedAtUtc: updatedAt,
      );
    } catch (error, stackTrace) {
      if (_sessionActive) {
        _failureLogger(
          'restore_treatment_declaration',
          error.runtimeType.toString(),
          stackTrace,
        );
      }
    }
  }

  /// Attempt one optimistic upload, preserving local data until a matching
  /// server receipt is observed. Call only while the native vault is unlocked.
  Future<bool> sendPendingTreatmentDeclaration() async {
    if (!_sessionActive || _treatmentSyncing ||
        _db.patientVaultScope?.nativeDjangoUserId == null) return false;
    _treatmentSyncing = true;
    try {
      final store = PatientTreatmentDeclarationStore(_db);
      final local = await store.read();
      if (!_sessionActive) return false;
      if (local == null || local.syncStatus == 'confirmed') return true;
      if (local.syncStatus == 'conflict') {
        state.value = SyncUiState.error;
        return false;
      }
      state.value = SyncUiState.syncing;
      final result = await _apiClient.mirrorTreatmentDeclaration(
        state: local.state,
        codes: local.codes,
        expectedUpdatedAtUtc: local.baseServerUpdatedAtUtc,
      );
      if (!_sessionActive) return false;
      if (result.status == TreatmentMirrorStatus.confirmed &&
          result.serverUpdatedAtUtc != null) {
        final acknowledged = await store.acknowledgeIfUnchanged(
          expectedGeneration: local.localGeneration,
          serverUpdatedAtUtc: result.serverUpdatedAtUtc!,
        );
        if (!_sessionActive) return false;
        if (!acknowledged) {
          state.value = SyncUiState.pending;
          return false;
        }
        await _refreshLocalSyncState();
        return _sessionActive;
      }
      if (result.status == TreatmentMirrorStatus.conflict) {
        final marked = await store.markConflictIfUnchanged(
          local.localGeneration,
        );
        if (!_sessionActive) return false;
        state.value = marked ? SyncUiState.error : SyncUiState.pending;
        return false;
      }
      state.value = SyncUiState.pending;
      return false;
    } catch (error, stackTrace) {
      if (_sessionActive) {
        state.value = SyncUiState.error;
        _failureLogger(
          'sync_treatment_declaration',
          error.runtimeType.toString(),
          stackTrace,
        );
      }
      return false;
    } finally {
      _treatmentSyncing = false;
    }
  }

  Future<void> refreshState() async {
    if (!_sessionActive) return;
    final connectivity = await _connectivity.checkConnectivity();
    if (!_sessionActive) return;
    if (_isOffline(connectivity)) {
      state.value = SyncUiState.offline;
      return;
    }

    await _refreshLocalSyncState();
  }

  /// Both queues contribute to the patient-facing sync state. In particular,
  /// a log-only retry must never claim 'up to date' while the treatment outbox
  /// contains pending or conflicted clinical declarations.
  Future<void> _refreshLocalSyncState({bool logsFailed = false}) async {
    if (!_sessionActive) return;
    try {
      final pendingLogs = await _db.getPendingLogs();
      if (!_sessionActive) return;
      if (_db.patientVaultScope?.nativeDjangoUserId != null) {
        final declaration = await PatientTreatmentDeclarationStore(_db).read();
        if (!_sessionActive) return;
        if (declaration?.syncStatus == 'conflict') {
          state.value = SyncUiState.error;
          return;
        }
        if (declaration?.syncStatus == 'pending') {
          state.value = logsFailed ? SyncUiState.error : SyncUiState.pending;
          return;
        }
      }
      state.value = logsFailed
          ? SyncUiState.error
          : pendingLogs.isEmpty ? SyncUiState.upToDate : SyncUiState.pending;
    } catch (error, stackTrace) {
      if (!_sessionActive) return;
      state.value = SyncUiState.error;
      _failureLogger(
        'read_combined_sync_status',
        error.runtimeType.toString(),
        stackTrace,
      );
    }
  }

  Future<void> syncPendingLogs() async {
    if (!_sessionActive || isSyncing.value) return;

    // An explicit retry must remain usable and testable without consulting a
    // platform channel first. Connectivity events set the offline state; the
    // network request itself is the source of truth for reachability.
    final pending = await _db.getPendingLogs();
    if (!_sessionActive) return;
    if (pending.isEmpty) {
      await _refreshLocalSyncState();
      return;
    }

    isSyncing.value = true;
    state.value = SyncUiState.syncing;
    if (kDebugMode) {
      print(
        'SyncService: Démarrage de la synchronisation batch '
        '(${pending.length} logs)...',
      );
    }

    var hadFailure = false;
    try {
      final batch = pending.map((log) {
        return {
          'blood_sugar': log.bloodSugar,
          'insulin_units': log.insulinUnits,
          'glycemic_context': log.glycemicContext ?? '',
          'meal_type': log.mealType ?? '',
          'meal_description': log.mealDescription ?? '',
          'meal_items': _mealItems(log.mealItemsJson),
          'meal_portions': _mealPortions(log.mealPortionsJson),
          'logged_at': (log.loggedAt ?? log.createdAt).toIso8601String(),
          'source': log.source,
          'client_uuid': log.clientUuid,
          ...journalContextFieldsForSync(
            isSick: log.isSick,
            isStressed: log.isStressed,
            isActive: log.isActive,
            sleepQuality: log.sleepQuality,
            fatigueLevel: log.fatigueLevel,
          ),
        };
      }).toList();

      // Recheck immediately before network egress, after every async read.
      if (!_sessionActive) return;
      final syncedUuids = await _apiClient.batchSyncLogs(batch);
      if (!_sessionActive) return;

      for (final log in pending) {
        if (!_sessionActive) return;
        if (syncedUuids.contains(log.clientUuid)) {
          await _db.markLogAsSynced(log.id);
        } else {
          hadFailure = true;
          await _db.reportSyncFailure(log.id, log.syncAttempts);
        }
      }

      await _refreshLocalSyncState(logsFailed: hadFailure);
    } catch (error, stackTrace) {
      if (!_sessionActive) return;
      hadFailure = true;
      state.value = SyncUiState.error;
      final errorType = error is SyncApiException
          ? error.errorType
          : error.runtimeType.toString();
      _failureLogger('sync_pending_logs', errorType, stackTrace);
      for (final log in pending) {
        if (!_sessionActive) return;
        await _db.reportSyncFailure(log.id, log.syncAttempts);
      }
    } finally {
      if (!_disposed) {
        isSyncing.value = false;
        if (!_sessionActive) {
          state.value = SyncUiState.checking;
        } else if (state.value == SyncUiState.syncing) {
          // Unknown outcome is never proof of server acknowledgement.
          state.value = SyncUiState.error;
        }
      }
    }
  }

  List<String> _mealItems(String? raw) {
    if (raw == null || raw.trim().isEmpty) return const <String>[];
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return const <String>[];
      return decoded.whereType<String>().toList(growable: false);
    } on FormatException catch (error, stackTrace) {
      _failureLogger(
        'decode_meal_items',
        error.runtimeType.toString(),
        stackTrace,
      );
      return const <String>[];
    }
  }

  List<Map<String, Object>> _mealPortions(String? raw) {
    if (raw == null || raw.trim().isEmpty) {
      return const <Map<String, Object>>[];
    }
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return const <Map<String, Object>>[];
      final result = <Map<String, Object>>[];
      for (final value in decoded) {
        if (value is! Map) continue;
        final foodId = value['food_id'];
        final portionId = value['portion_id'];
        final gramsRaw = value['grams'];
        final grams = gramsRaw is num ? gramsRaw.toDouble() : null;
        if (foodId is! String || foodId.trim().isEmpty) continue;
        if (portionId is! String? ||
            (portionId != null && portionId.trim().isEmpty)) {
          continue;
        }
        if (grams != null && (!grams.isFinite || grams <= 0 || grams > 3000)) {
          continue;
        }
        if (portionId == null && grams == null) continue;
        result.add(<String, Object>{
          'food_id': foodId,
          if (portionId != null) 'portion_id': portionId,
          if (grams != null) 'grams': grams,
        });
      }
      return result;
    } on FormatException catch (error, stackTrace) {
      _failureLogger(
        'decode_meal_portions',
        error.runtimeType.toString(),
        stackTrace,
      );
      return const <Map<String, Object>>[];
    }
  }

  void dispose() {
    _disposed = true;
    _connectivitySubscription?.cancel();
    isSyncing.dispose();
    state.dispose();
  }
}
