import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('V1-03 profile withdrawal requires server acknowledgment before success', () {
    final source = File('lib/features/profile/profile_screen.dart')
        .readAsStringSync();
    final handlerStart = source.indexOf('void _confirmWithdrawConsent(');
    expect(handlerStart, greaterThanOrEqualTo(0));
    final handler = source.substring(handlerStart);

    final request = handler.indexOf('final withdrawn = await api.withdrawConsent();');
    final denied = handler.indexOf('if (!withdrawn) {');
    final stop = handler.indexOf('return;', denied);
    final localGate = handler.indexOf('consent.clearVerifiedConsent();');
    final localTimestamp = handler.indexOf('await db.setAiConsent(granted: false);');
    final evidence = handler.indexOf('await evidence.clear();');
    final success = handler.indexOf('l10n.consentWithdrawn');

    expect(request, greaterThanOrEqualTo(0));
    expect(denied, greaterThan(request));
    expect(stop, greaterThan(denied));
    expect(localGate, greaterThan(stop));
    expect(localTimestamp, greaterThan(localGate));
    expect(evidence, greaterThan(localGate));
    expect(success, greaterThan(evidence));

    expect(handler.substring(denied, stop), contains('l10n.syncFailed'));
    expect(handler, isNot(contains('await api.withdrawConsent().catchError')));
    expect(handler, isNot(contains('consent.declineLocally();\n                      if (mounted)')));
  });

  test('withdraw API requires explicit revoked consent in response body', () {
    final source = File('lib/services/api_client.dart').readAsStringSync();
    final start = source.indexOf('Future<bool> withdrawConsent() async');
    expect(start, greaterThanOrEqualTo(0));
    final end = source.indexOf('  // ── Modules', start);
    expect(end, greaterThan(start));
    final implementation = source.substring(start, end);
    expect(
      implementation,
      contains('!response.isSuccessful || response.body is! Map'),
    );
    expect(implementation, contains("body['ai_consent_given'] == false"));
    expect(implementation, isNot(contains('return response.isSuccessful;')));
  });

  test('V1-03 server failure never implies local withdrawal success', () {
    final source = File('lib/features/profile/profile_screen.dart')
        .readAsStringSync();
    final start = source.indexOf('if (!withdrawn) {');
    final end = source.indexOf('consent.clearVerifiedConsent();', start);
    expect(start, greaterThanOrEqualTo(0));
    expect(end, greaterThan(start));
    final rejection = source.substring(start, end);
    expect(rejection, contains('return;'));
    expect(rejection, isNot(contains('consentWithdrawn')));
    expect(rejection, isNot(contains('db.setAiConsent')));
    expect(rejection, isNot(contains('evidence.clear()')));
  });
}
