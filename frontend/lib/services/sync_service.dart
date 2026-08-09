import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

import '../data/drift/database.dart';
import 'api_client.dart';

enum SyncUiState { checking, upToDate, pending, syncing, offline, error }

Map<String, Object> journalContextFieldsForSync({
  required bool isSick,
  required bool isStressed,
  required bool isActive,
  required String? sleepQuality,
}) {
  return <String, Object>{
    if (isSick) 'is_sick': 'yes',
    if (isStressed) 'stressed': 'yes',
    if (isActive) 'exercised': 'yes',
    if (sleepQuality == 'bad') 'sleep_quality': 'bad',
  };
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
  final ValueNotifier<SyncUiState> state = ValueNotifier<SyncUiState>(
    SyncUiState.checking,
  );

  SyncService(this._db, this._apiClient);

  void init() {
    unawaited(refreshState());
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen((
      results,
    ) {
      if (_isOffline(results)) {
        state.value = SyncUiState.offline;
        return;
      }
      unawaited(syncPendingLogs());
    });
  }

  bool _isOffline(List<ConnectivityResult> results) {
    return results.isEmpty ||
        results.every((result) => result == ConnectivityResult.none);
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

    // An explicit retry must remain usable and testable without consulting a
    // platform channel first. Connectivity events set the offline state; the
    // network request itself is the source of truth for reachability.
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
          ),
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

  List<String> _mealItems(String? raw) {
    if (raw == null || raw.trim().isEmpty) return const <String>[];
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return const <String>[];
      return decoded.whereType<String>().toList(growable: false);
    } catch (_) {
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
    } catch (_) {
      return const <Map<String, Object>>[];
    }
  }

  void dispose() {
    _connectivitySubscription?.cancel();
    isSyncing.dispose();
    state.dispose();
  }
}
