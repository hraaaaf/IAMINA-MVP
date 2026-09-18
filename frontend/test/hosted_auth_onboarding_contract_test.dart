import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('hosted Vercel flow cannot treat marker-only local enrollment as backend auth', () {
    final source = File('lib/routes/app_router.dart').readAsStringSync();

    expect(source, contains('kRemoteBackendAuthRequired'));
    expect(source, contains('authService.hasRemoteCredential'));
    expect(source, contains("final isOnboardingPage = path == '/onboarding';"));
    expect(source, contains('!isOnboardingPage'));
  });

  test('server-verified consent is anchored to the native backend user locally', () {
    final consent = File(
      'lib/features/auth/consent_screen.dart',
    ).readAsStringSync();
    final database = File(
      'lib/data/drift/database.dart',
    ).readAsStringSync();

    expect(consent, contains('auth.localProfileUserId'));
    expect(consent, contains('bindSingleProfileToUser'));
    expect(consent, contains('userId: auth.localProfileUserId'));
    expect(database, contains('Future<void> bindSingleProfileToUser(int userId)'));
    expect(database, contains('int? userId'));
  });
}
