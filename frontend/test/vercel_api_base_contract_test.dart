import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Vercel review build injects backend origin without duplicating /api/v1', () {
    final source = File('vercel_build.sh').readAsStringSync();

    expect(
      source,
      contains(
        'IAMINA_CERTIFIED_API_BASE_URL="https://iamina-certified.vercel.app"',
      ),
    );
    expect(
      source,
      isNot(
        contains(
          'IAMINA_CERTIFIED_API_BASE_URL="https://iamina-certified.vercel.app/api/v1"',
        ),
      ),
    );
  });

  test('Vercel Flutter build fails closed outside the review project', () {
    final source = File('vercel_build.sh').readAsStringSync();

    expect(
      source,
      contains(
        'if [ -n "\${VERCEL_PROJECT_ID:-}" ] && [ "$VERCEL_PROJECT_ID" != "$IAMINA_REVIEW_VERCEL_PROJECT_ID" ]; then',
      ),
    );
    expect(
      source,
      contains('ERROR: refusing Flutter build for Vercel project'),
    );
    expect(source, contains('exit 64'));
  });

  test('CompanionService reuses the canonical frontend API origin', () {
    final source = File('lib/services/companion_service.dart').readAsStringSync();

    expect(source, contains('const String companionApiBaseUrl = kBaseUrl;'));
    expect(source, isNot(contains("String.fromEnvironment(\n  'API_BASE_URL'")));
  });
}
