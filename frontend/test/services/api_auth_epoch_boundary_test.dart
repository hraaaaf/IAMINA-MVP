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
