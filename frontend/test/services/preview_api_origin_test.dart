import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/preview_api_origin.dart';

void main() {

  test('W01 country suggestion is public GET only, not a clinical bypass', () {
    final uri = Uri.parse('/api/v1/country/suggestion');
    expect(isPublicCountrySuggestion(uri, 'GET'), isTrue);
    for (final method in ['POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', '']) {
      expect(isPublicCountrySuggestion(uri, method), isFalse);
    }
    expect(isPublicCountrySuggestion(Uri.parse('/api/v1/profile'), 'GET'), isFalse);
    expect(isPublicCountrySuggestion(Uri.parse('/api/v1/country/suggestion?x=1'), 'GET'), isFalse);

    expect(() => requirePilotClinicalTransport(uri, () => false, method: 'GET'),
        returnsNormally);
    expect(() => requireUnlockedPatientSyncTransport(uri, () => false, method: 'GET'),
        returnsNormally);
    expect(() => requirePilotClinicalTransport(uri, () => false, method: 'POST'),
        throwsStateError);
    expect(() => requireUnlockedPatientSyncTransport(uri, () => false, method: 'POST'),
        throwsStateError);
    expect(() => requirePilotClinicalTransport(uri, () => false),
        throwsStateError);
    expect(() => requireUnlockedPatientSyncTransport(uri, () => false),
        throwsStateError);
  });

  test('Production and local-first mode preserve configured base exactly', () {
    final browser = Uri.parse('https://iamina-review-123-team.vercel.app/path');
    expect(
      resolveIaminaApiOriginForMode(
        'https://iamina-certified.vercel.app',
        sameOriginPreview: false,
        browserUri: browser,
      ),
      'https://iamina-certified.vercel.app',
    );
    expect(
      resolveIaminaApiOriginForMode(
        'http://localhost:8000',
        sameOriginPreview: false,
        browserUri: browser,
      ),
      'http://localhost:8000',
    );
  });

  test('Preview Web picks only its own HTTPS origin, not a remote API host', () {
    final browser = Uri.parse(
      'https://iamina-review-a1-achraf-benmoussa-s-projects.vercel.app'
      '/#/dashboard?foo=bar',
    );
    expect(
      resolveIaminaApiOriginForMode(
        'https://invalid.iamina-preview.invalid',
        sameOriginPreview: true,
        browserUri: browser,
      ),
      'https://iamina-review-a1-achraf-benmoussa-s-projects.vercel.app',
    );
  });

  test('Preview refuses insecure, opaque or userinfo browser URIs', () {
    for (final browser in <Uri>[
      Uri.parse('http://iamina-review.example/'),
      Uri.parse('file:///tmp/index.html'),
      Uri.parse('https://user:secret@iamina-review.example/'),
    ]) {
      expect(
        () => resolveIaminaApiOriginForMode(
          'https://invalid.iamina-preview.invalid',
          sameOriginPreview: true,
          browserUri: browser,
        ),
        throwsStateError,
      );
    }
  });
}
