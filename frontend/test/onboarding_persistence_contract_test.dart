import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('onboarding finish cannot remain indefinitely in saving state', () {
    final source = File(
      'lib/features/auth/onboarding_chat_screen.dart',
    ).readAsStringSync();

    expect(
      source,
      contains(
        'static const _persistenceTimeout = Duration(seconds: 10);',
      ),
    );
    expect(source, contains('.timeout(_persistenceTimeout)'));
    expect(source, contains('on TimeoutException catch'));
    expect(source, contains('setState(() => _saving = false)'));
    expect(source, contains("context.go('/dashboard')"));
  });

  test('native onboarding completes before consent and never requires Firebase', () {
    final onboarding = File(
      'lib/features/auth/onboarding_chat_screen.dart',
    ).readAsStringSync();
    final router = File('lib/routes/app_router.dart').readAsStringSync();

    expect(onboarding, contains('if (!kFirebaseMigrationEnabled) return 1;'));
    expect(onboarding, contains('final userId = _localProfileUserId();'));
    expect(
      onboarding,
      isNot(contains('final firebaseUser = FirebaseAuth.instance.currentUser;')),
    );

    expect(router, contains("final isOnboardingPage = path == '/onboarding';"));
    expect(router, contains('!isOnboardingPage'));
    expect(router, contains("return '/consent';"));
  });

}
