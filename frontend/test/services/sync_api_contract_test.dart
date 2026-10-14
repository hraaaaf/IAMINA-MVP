import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/sync_api_contract.dart';

void main() {
  test('D30 journal dispatch allows only fully bound, opted-in native identity',
      () {
    const token = 'iamina.synthetic-native-token';
    expect(
      mayDispatchClinicalJournal(
        patientBoundSyncApproved: true,
        hasNativeRemoteCredential: true,
        bearerToken: token,
        requestAuthEpoch: 3,
        currentAuthEpoch: 3,
      ),
      isTrue,
    );
  });

  test('D30 journal dispatch fails closed on each individual missing proof',
      () {
    const validToken = 'iamina.synthetic-native-token';

    bool allowed({
      bool authorized = true,
      bool nativeCredential = true,
      String? token = validToken,
      int requestEpoch = 7,
      int currentEpoch = 7,
    }) =>
        mayDispatchClinicalJournal(
          patientBoundSyncApproved: authorized,
          hasNativeRemoteCredential: nativeCredential,
          bearerToken: token,
          requestAuthEpoch: requestEpoch,
          currentAuthEpoch: currentEpoch,
        );

    expect(allowed(authorized: false), isFalse);
    expect(allowed(nativeCredential: false), isFalse);
    expect(allowed(token: null), isFalse);
    expect(allowed(token: ''), isFalse);
    expect(allowed(requestEpoch: 6), isFalse);
    expect(allowed(currentEpoch: 8), isFalse);
  });

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
