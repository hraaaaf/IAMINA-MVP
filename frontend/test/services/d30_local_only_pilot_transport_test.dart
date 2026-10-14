import 'dart:typed_data';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class _Auth extends Mock implements AuthService {}

void main() {
  test('Pilot A defaults to local only and preserves synthetic data in memory',
      () async {
    final auth = _Auth();
    final api = ApiClient(authService: auth);
    expect(api.canSyncClinicalData, isFalse);

    expect(await api.getProfile(), isNull);
    expect(await api.patchProfile({'ramadan_start_date': '2026-10-14'}), isFalse);
    expect(await api.syncLogEntry({'blood_sugar': 123}), isFalse);
    expect(await api.batchSyncLogs([{'blood_sugar': 123}]), isEmpty);
    expect((await api.mirrorTreatmentDeclaration(
      state: 'declared', codes: ['insulin'], expectedUpdatedAtUtc: null,
    )).status, TreatmentMirrorStatus.unavailable);
    expect(await api.chatStream('synthetic private message').toList(), isEmpty);
    expect(await api.sendVoiceMessage(Uint8List.fromList([1]), 'audio/webm'), isNull);
    expect(await api.analyzeGlucometerImage('synthetic-base64', 'image/png'), isNull);
    expect(await api.transcribeAudio(Uint8List.fromList([1]), 'audio/webm'), isNull);

    var readInput = false;
    final stream = Stream<List<int>>.fromIterable([[1, 2, 3]]).map((x) {
      readInput = true;
      return x;
    });
    expect(await api.ingestDocumentStream(
      stream, 3, 'synthetic-report.pdf', 'application/pdf',
    ), isNull);
    expect(readInput, isFalse, reason: 'No clinical file byte read in pilot A');
    verifyNever(() => auth.getIdToken());
  });

  test('Pilot A policy guards clinical API paths while allowing login', () {
    for (final path in [
      '/api/v1/profile', '/api/v1/logs', '/api/v1/logs/batch',
      '/api/v1/ai/chat', '/api/v1/documents/ingest',
    ]) {
      expect(
        () => requirePilotClinicalTransport(Uri.parse(path), () => false),
        throwsStateError,
        reason: path,
      );
    }
    expect(
      () => requirePilotClinicalTransport(
        Uri.parse('/api/v1/auth/login'), () => false,
      ),
      returnsNormally,
    );
  });
}
