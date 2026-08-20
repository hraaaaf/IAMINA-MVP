import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('document upload preflight', () {
    test('rejects empty payloads', () {
      expect(isDocumentUploadSizeAllowed(0), isFalse);
    });

    test('accepts the exact 15 MiB ceiling', () {
      expect(isDocumentUploadSizeAllowed(kMaxDocumentUploadBytes), isTrue);
    });

    test('rejects one byte above the ceiling', () {
      expect(isDocumentUploadSizeAllowed(kMaxDocumentUploadBytes + 1), isFalse);
    });
  });
}
