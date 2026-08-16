import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Companion uncertainty copy maps governed reason codes instead of exposing raw codes', () {
    final source = File(
      'lib/features/companion/companion_uncertainty_copy.dart',
    ).readAsStringSync();

    expect(source, contains('companionPatternLimitationLabel'));
    expect(source, contains('companionMissingDataLabel'));
    expect(source, contains("'improving_descriptively_does_not_mean_treatment_response_or_outcome'"));
    expect(source, contains("'current_governed_state_missing_cannot_infer_resolution'"));
    expect(source, contains("'no_eligible_post_review_evidence'"));
    expect(source, contains('_ => null'));
  });

  test('Companion screen renders only localized non-null uncertainty labels', () {
    final screen = File(
      'lib/features/companion/companion_premium_screen.dart',
    ).readAsStringSync();

    expect(screen, contains('companionPatternLimitationLabel(context, code)'));
    expect(screen, contains('companionMissingDataLabel(context, code)'));
    expect(screen, contains('.whereType<String>()'));
    expect(screen, contains('_UncertaintyNote(text: label)'));
  });
}
