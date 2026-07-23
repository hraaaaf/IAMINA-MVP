import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:amina/services/sync_service.dart';
import 'package:amina/data/drift/database.dart';
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
}
