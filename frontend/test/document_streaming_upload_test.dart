import 'dart:io';

import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('document upload streaming contract', () {
    test('size guard matches backend 15 MB limit', () {
      expect(isDocumentUploadSizeAllowed(0), isFalse);
      expect(isDocumentUploadSizeAllowed(1), isTrue);
      expect(isDocumentUploadSizeAllowed(kMaxDocumentUploadBytes), isTrue);
      expect(isDocumentUploadSizeAllowed(kMaxDocumentUploadBytes + 1), isFalse);
    });

    test('oversize stream is rejected before it is consumed', () async {
      var listened = false;
      final stream = Stream<List<int>>.multi((controller) {
        listened = true;
        controller.close();
      });
      final api = ApiClient(baseUrl: 'http://127.0.0.1:9');

      final result = await api.ingestDocumentStream(
        stream,
        kMaxDocumentUploadBytes + 1,
        'oversize.pdf',
        'application/pdf',
      );

      expect(result, isNull);
      expect(listened, isFalse);
    });

    test('client rejects Preview multipart oversize before opening stream', () {
      final source = File('lib/services/api_client.dart').readAsStringSync();
      final methodStart = source.indexOf(
        'Future<PulperPreview?> _ingestDocumentStreamRaw(',
      );
      expect(methodStart, greaterThanOrEqualTo(0));
      final methodEnd = source.indexOf('/// Stage 2:', methodStart);
      expect(methodEnd, greaterThan(methodStart));
      final methodBody = source.substring(methodStart, methodEnd);

      final multipartAdded = methodBody.indexOf('request.files.add(');
      final guard = methodBody.indexOf(
        'if (!isDocumentMultipartRequestAllowed(request)) return null;',
      );
      final send = methodBody.indexOf('final streamed = await request.send()');
      expect(multipartAdded, greaterThanOrEqualTo(0));
      expect(guard, greaterThan(multipartAdded));
      expect(send, greaterThan(guard));
    });

    test('document picker requests a stream instead of eager bytes', () {
      final source = File(
        'lib/features/documents/document_import_screen.dart',
      ).readAsStringSync();

      expect(source, contains('withData: false'));
      expect(source, contains('withReadStream: true'));
      expect(source, isNot(contains('final bytes = pf.bytes')));
      expect(source, contains('api.ingestDocumentStream('));
    });
  });
}
