import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('companion conversation reuses the application AuthService', () {
    final source = File(
      'lib/features/companion/companion_conversation_screen.dart',
    ).readAsStringSync();

    expect(source, contains('context.read<AuthService>()'));
    expect(
      source,
      contains('CompanionService(\n        authService: context.read<AuthService>(),'),
    );
    expect(source, isNot(contains('widget.service ?? CompanionService();')));
  });
}
