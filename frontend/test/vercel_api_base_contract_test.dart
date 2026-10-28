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

  test('Vercel review build overrides stale project-level API_BASE_URL', () {
    final source = File('vercel_build.sh').readAsStringSync();

    expect(
      source,
      contains(
        r'if [ "${VERCEL_PROJECT_ID:-}" = "$IAMINA_REVIEW_VERCEL_PROJECT_ID" ]; then',
      ),
    );
    expect(
      source,
      contains(r'API_BASE_URL="$IAMINA_CERTIFIED_API_BASE_URL"'),
    );
    expect(
      source,
      isNot(
        contains(
          r'if [ -z "${API_BASE_URL:-}" ] && [ "${VERCEL_PROJECT_ID:-}" = "$IAMINA_REVIEW_VERCEL_PROJECT_ID" ]; then',
        ),
      ),
    );
  });

  test('Preview remote accounts default OFF; opt-in is branch- and host-scoped', () {
    final source = File('vercel_build.sh').readAsStringSync();
    final preview = source.split('    preview)\n').last.split('    production)\n').first;
    final production = source.split('    production)\n').last.split('    *)\n').first;
    expect(preview, contains('IAMINA_PREVIEW_SAME_ORIGIN_API=true'));
    expect(preview, contains('IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false'));
    expect(preview, contains('D2_WEB_SYNTHETIC_ONLY_V1'));
    expect(preview, contains('VERCEL_GIT_COMMIT_REF'));
    expect(preview, contains('integration/w01-d2-preview-only-20261027'));
    expect(preview, contains('VERCEL_URL'));
    expect(preview, contains('IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA'));
    expect(preview, contains('VERCEL_GIT_COMMIT_SHA'));
    expect(preview, contains('IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true'));
    expect(preview.indexOf('IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false'),
      lessThan(preview.indexOf('D2_WEB_SYNTHETIC_ONLY_V1')));
    expect(preview, contains('refusing unknown synthetic Preview auth mode'));
    expect(production, contains('IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true'));
    expect(production, isNot(contains('D2_WEB_SYNTHETIC_ONLY_V1')));
    expect(source,
      contains(
        r'--dart-define=IAMINA_REMOTE_ACCOUNT_ENROLLMENT="${IAMINA_REMOTE_ACCOUNT_ENROLLMENT:-false}"',
      ),
    );
  });

  test('Vercel build strips a legacy /api/v1 suffix defensively', () {
    final source = File('vercel_build.sh').readAsStringSync();

    expect(source, contains(r'API_BASE_URL="${API_BASE_URL%/}"'));
    expect(source, contains(r'API_BASE_URL="${API_BASE_URL%/api/v1}"'));
  });

  test('Vercel Flutter build fails closed outside the review project', () {
    final source = File('vercel_build.sh').readAsStringSync();

    expect(
      source,
      contains(
        r'if [ -n "${VERCEL_PROJECT_ID:-}" ] && [ "$VERCEL_PROJECT_ID" != "$IAMINA_REVIEW_VERCEL_PROJECT_ID" ]; then',
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
