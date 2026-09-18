import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('onboarding reuses injected AuthService instead of raw FirebaseAuth', () {
    final source = File(
      'lib/features/auth/onboarding_chat_screen.dart',
    ).readAsStringSync();

    expect(source, contains('context.read<AuthService>()'));
    expect(source, contains('auth.firebaseUser?.uid.hashCode.abs() ?? 1'));
    expect(source, isNot(contains('FirebaseAuth.instance')));
    expect(source, isNot(contains("package:firebase_auth/firebase_auth.dart")));
  });
}
