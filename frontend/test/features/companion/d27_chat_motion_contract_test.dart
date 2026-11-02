import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D27 chat has bounded premium entry and branded Hero target', () {
    final source = File(
      'lib/features/companion/companion_conversation_screen.dart',
    ).readAsStringSync();
    expect(source, contains("Key('companion-chat-entry-motion')"));
    expect(source, contains('Duration(milliseconds: 380)'));
    expect(source, contains('Curves.easeOutCubic'));
    expect(source, contains("tag: 'dashboard-companion-chat-action'"));
    expect(source, contains('MediaQuery.disableAnimationsOf(context)'));
  });

  test('D27 waiting visual is bounded, accessible, and never fakes clinical steps', () {
    final source = File(
      'lib/features/companion/companion_conversation_screen.dart',
    ).readAsStringSync();
    expect(source, contains("Key('companion-typing-bubble')"));
    expect(source, contains('Semantics('));
    expect(source, contains('liveRegion: true'));
    expect(source, contains('IAmina prépare sa réponse…'));
    expect(source, contains('IAmina traite le message vocal…'));
    expect(source, contains('Duration(milliseconds: 960)'));
    expect(source, isNot(contains('LinearProgressIndicator(minHeight: 3)')));
    expect(source, contains('_messages.isEmpty && !waitingForReply'));
    expect(source, contains('_motion.dispose()'));
  });
}
