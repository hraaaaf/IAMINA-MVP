import 'dart:io';

import 'package:amina/features/dashboard/dashboard_companion_entry_screen.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('mobile companion entry uses conversation bar below 720px', () {
    expect(useMobileCompanionBar(390), isTrue);
    expect(useMobileCompanionBar(719), isTrue);
    expect(useMobileCompanionBar(720), isFalse);
    expect(useMobileCompanionBar(1280), isFalse);
  });

  test('mobile companion bar keeps the canonical chat action key and copy', () {
    final source = File(
      'lib/features/dashboard/dashboard_companion_entry_screen.dart',
    ).readAsStringSync();

    expect(source, contains("ValueKey('dashboard-companion-chat-action')"));
    expect(source, contains('Posez une question à IAmina…'));
    expect(source, contains("context.push('/companion/chat')"));
  });
}
