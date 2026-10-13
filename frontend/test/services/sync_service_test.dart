import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:amina/services/sync_service.dart';
import 'package:amina/services/auth_epoch.dart';
import 'dart:async';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import '../mocks.dart';

void main() {
  late MockAppDatabase mockDb;
  late MockApiClient mockApi;
  late SyncService syncService;

  final testLog = LogEntryData(
    id: 1,
    createdAt: DateTime.now(),
    bloodSugar: 120,
    clientUuid: 'test-uuid-1',
    syncStatus: 'pending',
    source: 'manual',
    isSick: false,
    isStressed: false,
    isTired: false,
    isActive: false,
    ramadanMode: false,
    syncAttempts: 0,
    errorSync: false,
    loggedAt: DateTime.now(),
  );

  setUp(() {
    mockDb = MockAppDatabase();
    mockApi = MockApiClient();
    syncService = SyncService(mockDb, mockApi);
  });

  test('syncPendingLogs does nothing when no pending logs', () async {
    when(() => mockDb.getPendingLogs()).thenAnswer((_) async => []);

    await syncService.syncPendingLogs();

    verifyNever(() => mockApi.batchSyncLogs(any()));
  });

  test('syncPendingLogs marks log as synced when UUID returned by server', () async {
    when(() => mockDb.getPendingLogs()).thenAnswer((_) async => [testLog]);
    when(() => mockApi.batchSyncLogs(any()))
        .thenAnswer((_) async => ['test-uuid-1']); // server confirms this UUID
    when(() => mockDb.markLogAsSynced(any())).thenAnswer((_) async => 1);

    await syncService.syncPendingLogs();

    verify(() => mockApi.batchSyncLogs(any())).called(1);
    verify(() => mockDb.markLogAsSynced(testLog.id)).called(1);
    verifyNever(() => mockDb.reportSyncFailure(any(), any()));
  });

  test('syncPendingLogs reports failure when server does not confirm UUID', () async {
    when(() => mockDb.getPendingLogs()).thenAnswer((_) async => [testLog]);
    when(() => mockApi.batchSyncLogs(any()))
        .thenAnswer((_) async => []); // empty = server rejected all
    when(() => mockDb.reportSyncFailure(any(), any())).thenAnswer((_) async => 1);

    await syncService.syncPendingLogs();

    verify(() => mockApi.batchSyncLogs(any())).called(1);
    verify(() => mockDb.reportSyncFailure(testLog.id, testLog.syncAttempts)).called(1);
    verifyNever(() => mockDb.markLogAsSynced(any()));
  });

  test('syncPendingLogs handles multiple logs — syncs matching, fails unmatched', () async {
    final log2 = LogEntryData(
      id: 2, createdAt: DateTime.now(), bloodSugar: 95,
      clientUuid: 'test-uuid-2', syncStatus: 'pending', source: 'manual',
      isSick: false, isStressed: false, isTired: false, isActive: false,
      ramadanMode: false, syncAttempts: 0, errorSync: false,
      loggedAt: DateTime.now(),
    );

    when(() => mockDb.getPendingLogs()).thenAnswer((_) async => [testLog, log2]);
    // Server only synced log1
    when(() => mockApi.batchSyncLogs(any()))
        .thenAnswer((_) async => ['test-uuid-1']);
    when(() => mockDb.markLogAsSynced(any())).thenAnswer((_) async => 1);
    when(() => mockDb.reportSyncFailure(any(), any())).thenAnswer((_) async => 1);

    await syncService.syncPendingLogs();

    verify(() => mockDb.markLogAsSynced(1)).called(1);       // log1 synced
    verify(() => mockDb.reportSyncFailure(2, 0)).called(1);  // log2 failed
  });

  test('syncPendingLogs explicitly logs its safe error fallback', () async {
    final failureEvents = <String>[];
    syncService = SyncService(
      mockDb,
      mockApi,
      failureLogger: (operation, errorType, stackTrace) {
        failureEvents.add('$operation:$errorType');
      },
    );
    when(() => mockDb.getPendingLogs()).thenAnswer((_) async => [testLog]);
    when(() => mockApi.batchSyncLogs(any())).thenThrow(StateError('synthetic'));
    when(() => mockDb.reportSyncFailure(any(), any())).thenAnswer((_) async => 1);

    await syncService.syncPendingLogs();

    expect(syncService.state.value, SyncUiState.error);
    expect(syncService.isSyncing.value, isFalse);
    expect(failureEvents, ['sync_pending_logs:StateError']);
    verify(() => mockDb.reportSyncFailure(testLog.id, testLog.syncAttempts)).called(1);
  });


  test('D7 account switch while pending-read awaits blocks cross-owner egress', () async {
    final pending = Completer<List<LogEntryData>>();
    when(() => mockDb.getPendingLogs()).thenAnswer((_) => pending.future);

    final running = syncService.syncPendingLogs();
    AuthEpoch.advance(); // synthetic A -> B before the Drift read resolves
    pending.complete([testLog]);
    await running;

    verifyNever(() => mockApi.batchSyncLogs(any()));
    verifyNever(() => mockDb.markLogAsSynced(any()));
    verifyNever(() => mockDb.reportSyncFailure(any(), any()));
  });

  test('D7 account switch during network await blocks stale local writes', () async {
    final confirmation = Completer<List<String>>();
    when(() => mockDb.getPendingLogs()).thenAnswer((_) async => [testLog]);
    when(() => mockApi.batchSyncLogs(any())).thenAnswer((_) => confirmation.future);
    final running = syncService.syncPendingLogs();
    // Let the initial Drift pending read complete and batch dispatch begin.
    await Future<void>.delayed(Duration.zero);
    AuthEpoch.advance(); // synthetic A -> B before server response
    confirmation.complete(['test-uuid-1']);
    await running;

    verifyNever(() => mockDb.markLogAsSynced(any()));
    verifyNever(() => mockDb.reportSyncFailure(any(), any()));
  });

  test('D7 stale synchronizer cannot upload after owner switch', () async {
    AuthEpoch.advance();
    await syncService.syncPendingLogs();
    verifyNever(() => mockDb.getPendingLogs());
    verifyNever(() => mockApi.batchSyncLogs(any()));
  });

  test('malformed meal JSON uses typed fallback and remains syncable', () async {
    final malformedLog = LogEntryData(
      id: 3,
      createdAt: DateTime.now(),
      bloodSugar: 110,
      clientUuid: 'test-uuid-malformed',
      syncStatus: 'pending',
      source: 'manual',
      isSick: false,
      isStressed: false,
      isTired: false,
      isActive: false,
      ramadanMode: false,
      syncAttempts: 0,
      errorSync: false,
      loggedAt: DateTime.now(),
      mealItemsJson: '{',
      mealPortionsJson: '[',
    );
    final failureEvents = <String>[];
    syncService = SyncService(
      mockDb,
      mockApi,
      failureLogger: (operation, errorType, stackTrace) {
        failureEvents.add('$operation:$errorType');
      },
    );
    var pendingReads = 0;
    when(() => mockDb.getPendingLogs()).thenAnswer((_) async {
      pendingReads += 1;
      return pendingReads == 1 ? [malformedLog] : <LogEntryData>[];
    });
    when(() => mockApi.batchSyncLogs(any()))
        .thenAnswer((_) async => ['test-uuid-malformed']);
    when(() => mockDb.markLogAsSynced(any())).thenAnswer((_) async => 1);

    await syncService.syncPendingLogs();

    final batch = verify(
      () => mockApi.batchSyncLogs(captureAny()),
    ).captured.single as List<Map<String, dynamic>>;
    expect(batch.single['meal_items'], isEmpty);
    expect(batch.single['meal_portions'], isEmpty);
    expect(
      failureEvents,
      containsAll(<String>[
        'decode_meal_items:FormatException',
        'decode_meal_portions:FormatException',
      ]),
    );
    expect(syncService.state.value, SyncUiState.upToDate);
  });
  Future<AppDatabase> nativeVault(int userId) async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(),
      PatientVaultScope.nativeDjango(userId),
    );
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: drift.Value(userId),
        updatedAt: DateTime.utc(2026, 10, 13),
      ),
    );
    return db;
  }

  test('D7 remote explicit declaration restores into own empty native vault', () async {
    final db = await nativeVault(734);
    addTearDown(db.close);
    final restoration = SyncService(db, mockApi);
    addTearDown(restoration.dispose);
    when(() => mockApi.getProfile()).thenAnswer((_) async => {
      'treatment_declaration_source': 'patient_declared',
      'treatment_declaration_version': 1,
      'treatment_declaration_state': 'declared',
      'treatment_declarations': ['insulin', 'oral_meds'],
      'treatment_declaration_updated_at': '2026-10-13T14:00:00Z',
    });
    await restoration.restorePatientTreatmentDeclaration();
    final saved = await PatientTreatmentDeclarationStore(db).read();
    expect(saved?.ownerId, 734);
    expect(saved?.codes, ['insulin', 'oral_meds']);
    verify(() => mockApi.getProfile()).called(1);
  });

  test('D7 server defaults must not invent patient-reported treatment', () async {
    final db = await nativeVault(734);
    addTearDown(db.close);
    final restoration = SyncService(db, mockApi);
    addTearDown(restoration.dispose);
    when(() => mockApi.getProfile()).thenAnswer((_) async => {
      'treatment_declaration_source': null,
      'treatment_declaration_version': 1,
      'treatment_declaration_state': 'not_answered',
      'treatment_declarations': <String>[],
      'treatment_declaration_updated_at': null,
    });
    await restoration.restorePatientTreatmentDeclaration();
    expect(await PatientTreatmentDeclarationStore(db).read(), isNull);
  });

  test('D7 a local offline declaration takes precedence over a server GET', () async {
    final db = await nativeVault(734);
    addTearDown(db.close);
    final local = PatientTreatmentDeclarationStore(db);
    await local.write(state: 'declared', codes: ['lifestyle']);
    final restoration = SyncService(db, mockApi);
    addTearDown(restoration.dispose);
    await restoration.restorePatientTreatmentDeclaration();
    verifyNever(() => mockApi.getProfile());
    expect((await local.read())?.codes, ['lifestyle']);
  });

  test('D7 auth epoch switch during remote GET prevents stale vault restoration', () async {
    final db = await nativeVault(734);
    addTearDown(db.close);
    final fetching = Completer<Map<String, dynamic>?>();
    when(() => mockApi.getProfile()).thenAnswer((_) => fetching.future);
    final restoration = SyncService(db, mockApi);
    addTearDown(restoration.dispose);
    final running = restoration.restorePatientTreatmentDeclaration();
    await Future<void>.delayed(Duration.zero);
    AuthEpoch.advance();
    fetching.complete({
      'treatment_declaration_source': 'patient_declared',
      'treatment_declaration_version': 1,
      'treatment_declaration_state': 'declared',
      'treatment_declarations': ['insulin'],
      'treatment_declaration_updated_at': '2026-10-13T14:00:00Z',
    });
    await running;
    expect(await PatientTreatmentDeclarationStore(db).read(), isNull);
  });

}
