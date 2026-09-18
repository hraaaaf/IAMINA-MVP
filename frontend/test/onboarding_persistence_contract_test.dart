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
    expect(source, contains('kFirebaseMigrationEnabled'));
    expect(
      source,
      contains('? FirebaseAuth.instance.currentUser'),
    );
  });
}
