import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/cgm_service.dart';

class _FakeAuthService extends AuthService {
  @override
  Future<String?> getIdToken() async => 'test-token';
}

void main() {
  test('getConnection uses authenticated patient endpoint', () async {
    final client = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/api/v1/cgm/connection');
      expect(request.headers['authorization'], 'Bearer test-token');
      return http.Response(
        jsonEncode({
          'connected': true,
          'source': 'dexcom',
          'base_url': 'https://nightscout.example.com',
          'auth_type': 'bearer',
          'credential_set': true,
          'enabled': true,
          'last_sync_at': '2026-08-16T12:00:00Z',
          'last_success_at': '2026-08-16T12:00:00Z',
          'last_error_code': '',
        }),
        200,
      );
    });
    final service = CgmService(
      authService: _FakeAuthService(),
      httpClient: client,
      baseUrl: 'https://iamina.test',
    );

    final state = await service.getConnection();
    expect(state.connected, isTrue);
    expect(state.source, 'dexcom');
    expect(state.credentialSet, isTrue);
  });

  test('configure sends secret but never expects it back', () async {
    final client = MockClient((request) async {
      expect(request.method, 'PUT');
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(body['source'], 'linx');
      expect(body['credential'], 'transport-secret');
      return http.Response(
        jsonEncode({
          'connected': true,
          'source': 'linx',
          'base_url': 'https://nightscout.example.com',
          'auth_type': 'api_secret',
          'credential_set': true,
          'enabled': true,
          'last_error_code': '',
        }),
        200,
      );
    });
    final service = CgmService(
      authService: _FakeAuthService(),
      httpClient: client,
      baseUrl: 'https://iamina.test',
    );

    final state = await service.configure(
      source: 'linx',
      nightscoutUrl: 'https://nightscout.example.com',
      authType: 'api_secret',
      credential: 'transport-secret',
    );
    expect(state.source, 'linx');
    expect(state.credentialSet, isTrue);
  });

  test('readings remain factual transport fields', () async {
    final client = MockClient((request) async {
      expect(request.url.path, '/api/v1/cgm/readings');
      expect(request.url.queryParameters['hours'], '24');
      return http.Response(
        jsonEncode([
          {
            'recorded_at': '2026-08-16T12:00:00Z',
            'glucose_mg_dl': 123,
            'trend': 'Flat',
            'device': 'Dexcom G7',
            'source': 'dexcom',
          },
        ]),
        200,
      );
    });
    final service = CgmService(
      authService: _FakeAuthService(),
      httpClient: client,
      baseUrl: 'https://iamina.test',
    );

    final readings = await service.getReadings();
    expect(readings, hasLength(1));
    expect(readings.single.glucoseMgDl, 123);
    expect(readings.single.trend, 'Flat');
    expect(readings.single.source, 'dexcom');
  });

  test('non-success response fails with stable client exception', () async {
    final service = CgmService(
      authService: _FakeAuthService(),
      httpClient: MockClient(
        (_) async => http.Response(jsonEncode({'detail': 'provider_unavailable'}), 503),
      ),
      baseUrl: 'https://iamina.test',
    );

    expect(
      service.sync,
      throwsA(
        isA<CgmServiceException>()
            .having((error) => error.code, 'code', 'provider_unavailable')
            .having((error) => error.statusCode, 'status', 503),
      ),
    );
  });
}
