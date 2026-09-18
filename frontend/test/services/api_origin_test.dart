import 'package:amina/services/api_client.dart';
import 'package:amina/services/api_origin.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('API origin normalization strips legacy v1 suffix and trailing slash', () {
    expect(
      normalizeApiOrigin('https://iamina-certified.vercel.app/api/v1/'),
      'https://iamina-certified.vercel.app',
    );
    expect(
      normalizeApiOrigin('https://iamina-certified.vercel.app/'),
      'https://iamina-certified.vercel.app',
    );
    expect(
      normalizeApiOrigin('https://iamina-certified.vercel.app'),
      'https://iamina-certified.vercel.app',
    );
  });

  test('API origin normalization does not strip unrelated paths', () {
    expect(
      normalizeApiOrigin('https://example.test/api/v10'),
      'https://example.test/api/v10',
    );
  });

  test('ApiClient normalizes an inherited legacy API base', () {
    final client = ApiClient(
      baseUrl: 'https://iamina-certified.vercel.app/api/v1',
    );

    expect(client.baseUrl, 'https://iamina-certified.vercel.app');
  });
}
