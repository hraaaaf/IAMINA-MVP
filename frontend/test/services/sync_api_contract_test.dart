import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/sync_api_contract.dart';

void main() {
  test('guardSyncApiCall preserves success values', () async {
    final result = await guardSyncApiCall<int>(
      'batch_sync_logs',
      () async => 7,
    );

    expect(result, 7);
  });

  test('guardSyncApiCall wraps technical failures without payload leakage', () async {
    final future = guardSyncApiCall<bool>(
      'batch_sync_logs',
      () async => throw StateError('synthetic-sensitive-payload'),
    );

    await expectLater(
      future,
      throwsA(
        isA<SyncApiException>()
            .having((error) => error.operation, 'operation', 'batch_sync_logs')
            .having((error) => error.errorType, 'errorType', 'StateError')
            .having(
              (error) => error.toString(),
              'sanitized toString',
              isNot(contains('synthetic-sensitive-payload')),
            ),
      ),
    );
  });

  test('parseBatchSyncIds keeps ordinary empty confirmation semantics', () {
    expect(parseBatchSyncIds(null), isEmpty);
    expect(parseBatchSyncIds(<String, Object?>{}), isEmpty);
  });

  test('parseBatchSyncIds returns validated server UUIDs', () {
    expect(
      parseBatchSyncIds(<String, Object?>{
        'synced_ids': <String>['uuid-1', 'uuid-2'],
      }),
      <String>['uuid-1', 'uuid-2'],
    );
  });

  test('parseBatchSyncIds rejects malformed success payloads', () {
    expect(
      () => parseBatchSyncIds(<String, Object?>{
        'synced_ids': <Object>['uuid-1', 2],
      }),
      throwsA(isA<FormatException>()),
    );
  });
}
