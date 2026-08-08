import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('P1-UX-13 keeps consent actions reachable on compact screens', () {
    final source = File(
      'lib/features/auth/consent_screen.dart',
    ).readAsStringSync();

    for (final required in <String>[
      'constraints.maxHeight <= 600',
      'compactHeight ? 14 : 40',
      'compactHeight ? 48.0 : 72.0',
      'compactHeight ? 18 : 22',
      'compactHeight ? 12 : 20',
      'compactHeight ? 11.5 : 13.5',
      'compactHeight ? 14 : 36',
      'l10n.consentAccept',
      'l10n.consentDeclineWithoutAI',
      'l10n.dataPrivacyNote',
    ]) {
      expect(
        source,
        contains(required),
        reason: 'Compact consent contract is missing: $required',
      );
    }
  });
}
