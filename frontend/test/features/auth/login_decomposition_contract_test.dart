import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Certified login keeps auth orchestration out of presentation part', () {
    final state = File(
      'lib/features/auth/login_screen_fr_certified.dart',
    ).readAsStringSync();
    final presentation = File(
      'lib/features/auth/login_screen_fr_certified_presentation.dart',
    ).readAsStringSync();

    expect(state, contains("part 'login_screen_fr_certified_presentation.dart';"));
    expect(state, contains('class _LoginScreenState'));
    expect(state, contains('Future<void> _handleLogin()'));
    expect(state, contains('Future<void> _handleForgotPassword()'));
    expect(state, contains('void _handleSignup()'));
    expect(state, contains('AuthService'));
    expect(state, isNot(contains('class _LoginBackdrop')));
    expect(state, isNot(contains('class _LoginCard')));
    expect(state, isNot(contains('class _PrimaryLoginButton')));

    expect(presentation, contains('class _LoginBackdrop'));
    expect(presentation, contains('class _LoginCard'));
    expect(presentation, contains('class _PrimaryLoginButton'));
    expect(presentation, isNot(contains('Future<void> _handleLogin()')));
    expect(presentation, isNot(contains('AuthService')));
    expect(presentation, isNot(contains("import 'package:")));
  });
}
