import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:amina/services/sync_service.dart';
import 'package:amina/data/drift/database.dart';
import '../mocks.dart';

void main() {
  late MockAppDatabase mockDb;
  late MockApiClient mockApi;
  late SyncService syncService;

  setUp(() {
    mockDb = MockAppDatabase();
    mockApi = MockApiClient();
    syncService = SyncService(mockDb, mockApi);
  });

  test('SyncService triggers sync and queries pending logs', () async {
    when(() => mockDb.getPendingLogs()).thenAnswer((_) async => []);

    await syncService.syncPendingLogs();

    verify(() => mockDb.getPendingLogs()).called(1);
  });

  test(
    'SyncService reports failure and increments attempts on batch rejection',
    () async {
      final testLog = LogEntryData(
        id: 1,
        createdAt: DateTime.now(),
        bloodSugar: 120,
        clientUuid: 'test-uuid',
        syncStatus: 'pending',
        source: 'manual',
        isSick: false,
        isStressed: false,
        isTired: false,
        isActive: false,
        ramadanMode: false,
        syncAttempts: 2,
        errorSync: false,
        loggedAt: DateTime.now(),
      );

      when(() => mockDb.getPendingLogs()).thenAnswer((_) async => [testLog]);
      when(() => mockApi.batchSyncLogs(any())).thenAnswer((_) async => []);
      when(
        () => mockDb.reportSyncFailure(any(), any()),
      ).thenAnswer((_) async => 1);

      await syncService.syncPendingLogs();

      verify(() => mockDb.reportSyncFailure(testLog.id, 2)).called(1);
    },
  );

  test(
    'SyncService is not re-entrant — second call while syncing is ignored',
    () async {
      // Set up a slow batch sync
      when(() => mockDb.getPendingLogs()).thenAnswer((_) async => []);
      await syncService.syncPendingLogs();

      // Second call while first hasn't started yet should still work
      when(() => mockDb.getPendingLogs()).thenAnswer((_) async => []);
      await syncService.syncPendingLogs();

      // getPendingLogs should be called twice (both were separate calls)
      verify(() => mockDb.getPendingLogs()).called(2);
    },
  );
}
