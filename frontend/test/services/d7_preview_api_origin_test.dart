
import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const configured = 'https://iamina-review-git-cert-d7-we-5e65d5-achraf-benmoussa-s-projects.vercel.app';
  final deployed = Uri.parse('https://iamina-review-ao58p4rey-achraf-benmoussa-s-projects.vercel.app/consent');

  test('remote Web API resolves to immutable deployment origin, never branch alias', () {
    expect(resolvePatientApiOrigin(
      isWeb: true,
      remoteAccountLogin: true,
      pageUri: deployed,
      configuredBaseUrl: configured,
    ), 'https://iamina-review-ao58p4rey-achraf-benmoussa-s-projects.vercel.app');
  });

  test('local-first and non-Web keep their configured API transport', () {
    for (final pair in [(false, true), (true, false), (false, false)]) {
      expect(resolvePatientApiOrigin(
        isWeb: pair.$1,
        remoteAccountLogin: pair.$2,
        pageUri: deployed,
        configuredBaseUrl: configured,
      ), configured);
    }
  });

  test('remote Web rejects insecure unrelated origins', () {
    expect(() => resolvePatientApiOrigin(
      isWeb: true,
      remoteAccountLogin: true,
      pageUri: Uri.parse('http://example.invalid/consent'),
      configuredBaseUrl: configured,
    ), throwsStateError);
    expect(resolvePatientApiOrigin(
      isWeb: true,
      remoteAccountLogin: true,
      pageUri: Uri.parse('http://localhost:7378/consent'),
      configuredBaseUrl: configured,
    ), 'http://localhost:7378');
  });
}
