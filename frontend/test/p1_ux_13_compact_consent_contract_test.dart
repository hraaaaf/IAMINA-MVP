import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('P1-UX-13 keeps consent actions reachable on compact screens', () {
    final source = File(
      'lib/features/auth/consent_screen.dart',
    ).readAsStringSync();

    for (final required in <String>[
      'constraints.maxHeight <= 600',
      'vertical: compactHeight ? 14 : 28',
      'compactHeight ? 48.0 : 72.0',
      'compactHeight ? 18 : 22',
      'compactHeight ? 12 : 20',
      'compactHeight ? 11.5 : 13.25',
      'compactHeight ? 14 : 24',
      'l10n.consentAccept',
      'l10n.consentDeclineWithoutAI',
      'l10n.dataPrivacyNote',
      'OutlinedButton(',
    ]) {
      expect(
        source,
        contains(required),
        reason: 'Compact consent contract is missing: $required',
      );
    }
  });
}
