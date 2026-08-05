import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

import '../data/drift/database.dart';
import 'api_client.dart';

enum SyncUiState {
  checking,
  upToDate,
  pending,
  syncing,
  offline,
  error,
}

class SyncService {
  final AppDatabase _db;
  final ApiClient _apiClient;
  final Connectivity _connectivity = Connectivity();
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;

  /// Kept for compatibility with existing consumers that only need activity.
  final ValueNotifier<bool> isSyncing = ValueNotifier<bool>(false);

  /// Authoritative patient-facing state. UI must never infer synchronization
  /// from a decorative icon or from local data existing on the device.
  final ValueNotifier<SyncUiState> state =
      ValueNotifier<SyncUiState>(SyncUiState.checking);

  SyncService(this._db, this._apiClient);

  void init() {
    unawaited(refreshState());
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen((results) {
      if (_isOffline(results)) {
        state.value = SyncUiState.offline;
        return;
      }
      unawaited(syncPendingLogs());
    });
  }

  bool _isOffline(List<ConnectivityResult> results) {
    return results.isEmpty || results.every((result) => result == ConnectivityResult.none);
  }

  Future<void> refreshState() async {
    final connectivity = await _connectivity.checkConnectivity();
    if (_isOffline(connectivity)) {
      state.value = SyncUiState.offline;
      return;
    }

    final pending = await _db.getPendingLogs();
    state.value = pending.isEmpty ? SyncUiState.upToDate : SyncUiState.pending;
  }

  Future<void> syncPendingLogs() async {
    if (isSyncing.value) return;

    final connectivity = await _connectivity.checkConnectivity();
    if (_isOffline(connectivity)) {
      state.value = SyncUiState.offline;
      return;
    }

    final pending = await _db.getPendingLogs();
    if (pending.isEmpty) {
      state.value = SyncUiState.upToDate;
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
          'meal_type': log.mealType ?? '',
          'meal_description': log.mealDescription ?? '',
          'logged_at': (log.loggedAt ?? log.createdAt).toIso8601String(),
          'source': log.source,
          'client_uuid': log.clientUuid,
          'fatigue_level': (log.fatigueLevel ?? 0) > 0 ? 'tired' : 'ok',
          'is_sick': log.isSick ? 'yes' : 'no',
          'stressed': log.isStressed ? 'yes' : 'no',
          'sleep_quality': log.sleepQuality ?? 'good',
          'exercised': log.isActive ? 'yes' : 'no',
        };
      }).toList();

      final syncedUuids = await _apiClient.batchSyncLogs(batch);

      for (final log in pending) {
        if (syncedUuids.contains(log.clientUuid)) {
          await _db.markLogAsSynced(log.id);
        } else {
          hadFailure = true;
          await _db.reportSyncFailure(log.id, log.syncAttempts);
        }
      }

      final stillPending = await _db.getPendingLogs();
      state.value = hadFailure || stillPending.isNotEmpty
          ? SyncUiState.error
          : SyncUiState.upToDate;
    } catch (error) {
      hadFailure = true;
      state.value = SyncUiState.error;
      for (final log in pending) {
        await _db.reportSyncFailure(log.id, log.syncAttempts);
      }
      if (kDebugMode) print('SyncService Error: $error');
    } finally {
      isSyncing.value = false;
      if (!hadFailure && state.value == SyncUiState.syncing) {
        state.value = SyncUiState.upToDate;
      }
    }
  }

  void dispose() {
    _connectivitySubscription?.cancel();
    isSyncing.dispose();
    state.dispose();
  }
}
