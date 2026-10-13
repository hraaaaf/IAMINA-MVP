import 'dart:async';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D7 token lookup refuses a stale session before any network dispatch',
      () async {
    final pending = Completer<String?>();
    final result = readForStableAuthEpoch(() => pending.future);
    AuthEpoch.advance(); // A -> B while token resolution is suspended.
    pending.complete('synthetic-b-token');
    await expectLater(result, throwsStateError);
  });

  test('D7 patient endpoints fail closed when app-lock closes', () {
    const blocked = [
      '/api/v1/profile',
      '/api/v1/logs',
      '/api/v1/logs/batch',
    ];
    for (final path in blocked) {
      expect(
        () => requireUnlockedPatientSyncTransport(
          Uri.parse(path), () => false,
        ),
        throwsStateError,
      );
      expect(
        () => requireUnlockedPatientSyncTransport(
          Uri.parse(path), () => true,
        ),
        returnsNormally,
      );
    }
    // Authentication and enrollment must work before a device is unlocked.
    expect(() => requireUnlockedPatientSyncTransport(
      Uri.parse('/api/v1/auth/login'), () => false,
    ), returnsNormally);
  });

  test('D7 locking during async token lookup blocks profile egress', () async {
    final token = Completer<String?>();
    var unlocked = true;
    var dispatched = false;
    Future<void> issueProfileRequest() async {
      await readForStableAuthEpoch(() => token.future);
      requireUnlockedPatientSyncTransport(
        Uri.parse('/api/v1/profile'), () => unlocked,
      );
      dispatched = true;
    }
    final inFlight = issueProfileRequest();
    unlocked = false;
    token.complete('synthetic-a-token');
    await expectLater(inFlight, throwsStateError);
    expect(dispatched, isFalse);
  });

  test('D7 retry after app-lock closes cannot dispatch medical request', () {
    var unlocked = true;
    requireUnlockedPatientSyncTransport(
      Uri.parse('/api/v1/logs/batch'), () => unlocked,
    );
    unlocked = false;
    expect(() => requireUnlockedPatientSyncTransport(
      Uri.parse('/api/v1/logs/batch'), () => unlocked,
    ), throwsStateError);
  });

  test('D7 unchanged epoch preserves normal authenticated token lookup', () async {
    final result = await readForStableAuthEpoch(
      () async => 'synthetic-a-token',
    );
    expect(result, 'synthetic-a-token');
  });

  test('D7 retry boundary rejects a changed epoch', () {
    final captured = AuthEpoch.value;
    requireCurrentAuthEpoch(captured);
    AuthEpoch.advance();
    expect(() => requireCurrentAuthEpoch(captured), throwsStateError);
  });
}
