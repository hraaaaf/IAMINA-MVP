import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/preview_api_origin.dart';

void main() {
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
