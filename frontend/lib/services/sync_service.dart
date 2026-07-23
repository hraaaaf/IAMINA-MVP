import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import '../data/drift/database.dart';
import 'api_client.dart';

class SyncService {
  final AppDatabase _db;
  final ApiClient _apiClient;
  final Connectivity _connectivity = Connectivity();
  StreamSubscription? _connectivitySubscription;
  
  // Feedback visuel de synchronisation
  final ValueNotifier<bool> isSyncing = ValueNotifier<bool>(false);

  SyncService(this._db, this._apiClient);

  void init() {
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen((results) {
      if (results.any((r) => r != ConnectivityResult.none)) {
        syncPendingLogs();
      }
    });
  }

  Future<void> syncPendingLogs() async {
    if (isSyncing.value) return;
    
    final pending = await _db.getPendingLogs();
    if (pending.isEmpty) return;

    isSyncing.value = true;
    if (kDebugMode) print('SyncService: Démarrage de la synchronisation batch (${pending.length} logs)...');

    try {
      // Préparation du batch
      final List<Map<String, dynamic>> batch = pending.map((log) {
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
          'stressed': log.isStressed ? 'yes' : 'no', // Fix: mapped to 'stressed' (not is_stressed)
          'sleep_quality': log.sleepQuality ?? 'good',
          'exercised': log.isActive ? 'yes' : 'no',
        };
      }).toList();

      final syncedUuids = await _apiClient.batchSyncLogs(batch);
      
      if (syncedUuids.isNotEmpty) {
        for (var log in pending) {
          if (syncedUuids.contains(log.clientUuid)) {
            await _db.markLogAsSynced(log.id);
          } else {
            await _db.reportSyncFailure(log.id, log.syncAttempts);
          }
        }
      } else {
        // En cas d'échec total du batch, on incrémente les tentatives
        for (var log in pending) {
          await _db.reportSyncFailure(log.id, log.syncAttempts);
        }
      }
    } catch (e) {
      if (kDebugMode) print('SyncService Error: $e');
    } finally {
      isSyncing.value = false;
    }
  }

  void dispose() {
    _connectivitySubscription?.cancel();
    isSyncing.dispose();
  }
}
