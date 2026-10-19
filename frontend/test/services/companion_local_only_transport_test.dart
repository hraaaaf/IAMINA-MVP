import 'dart:typed_data';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _CountingPatientAuth extends AuthService {
  int tokenReads = 0;

  @override
  bool get isAuditSession => false;

  @override
  Future<String?> getIdToken() async {
    tokenReads += 1;
    return 'synthetic-patient-token';
  }
}

class _AuditAuth extends AuthService {
  int tokenReads = 0;

  @override
  bool get isAuditSession => true;

  @override
  Future<String?> getIdToken() async {
    tokenReads += 1;
    return 'synthetic-audit-token';
  }
}

void main() {
  test('local-only patient companion methods read no tokens and send zero HTTP', () async {
    final auth = _CountingPatientAuth();
    var requestCount = 0;
    final client = MockClient((_) async {
      requestCount++;
      return http.Response('{}', 200);
    });
    final service = CompanionService(
      authService: auth,
      httpClient: client,
      baseUrl: 'https://iamina.invalid',
    );

    expect(await service.fetchOverview(), isNull);
    expect(await service.fetchProactivePreview(), isNull);
    expect(await service.evaluateNextAction(), isNull);

    final localOnlyDenied = throwsA(
      isA<ProviderApiException>()
          .having((e) => e.code, 'code', 'clinical_transport_disabled_local_only')
          .having((e) => e.statusCode, 'statusCode', 403),
    );

    await expectLater(
      service.sendChatMessage('Ma glycémie était 126 mg/dL.'),
      localOnlyDenied,
    );
    await expectLater(
      service.sendVoiceMessage(Uint8List.fromList([1, 2, 3]), 'audio/webm'),
      localOnlyDenied,
    );

    expect(auth.tokenReads, 0);
    expect(requestCount, 0);
    service.dispose();
  });

  test('local-only audit chat uses local fallback, not unauthenticated demo HTTP', () async {
    final auth = _AuditAuth();
    var requestCount = 0;
    final service = CompanionService(
      authService: auth,
      httpClient: MockClient((_) async {
        requestCount++;
        throw StateError('No demo HTTP allowed');
      }),
      baseUrl: 'https://iamina.invalid',
    );

    final reply = await service.sendChatMessage('126 mg/dL, insuline déclarée.');
    expect(reply?.conversationId, 'demo-local');
    expect(reply?.reply, contains('mode démo local'));
    expect(auth.tokenReads, 0);
    expect(requestCount, 0);
    service.dispose();
  });

  test('explicit false synthetic permit cannot enable clinical HTTP', () async {
    final auth = _CountingPatientAuth();
    var requestCount = 0;
    final service = CompanionService(
      authService: auth,
      allowClinicalTransportForSyntheticTests: () => false,
      httpClient: MockClient((_) async {
        requestCount++;
        return http.Response('{}', 200);
      }),
    );

    await expectLater(
      service.sendChatMessage('136 mg/dL'),
      throwsA(isA<ProviderApiException>()
          .having((e) => e.code, 'code', 'clinical_transport_disabled_local_only')),
    );
    expect(auth.tokenReads, 0);
    expect(requestCount, 0);
    service.dispose();
  });
}
