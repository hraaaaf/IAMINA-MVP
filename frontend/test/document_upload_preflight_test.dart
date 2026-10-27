import 'dart:async';

import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

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

    test('Preview Web preflight counts the entire multipart request', () {
      http.MultipartRequest multipart(int fileBytes) {
        final request = http.MultipartRequest(
          'POST',
          Uri.parse('https://synthetic.invalid/api/v1/documents/ingest'),
        );
        // Declared stream length is enough to compute framing without
        // allocating document bytes or opening a network connection.
        request.files.add(http.MultipartFile(
          'file',
          const Stream<List<int>>.empty(),
          fileBytes,
          filename: 'synthetic.pdf',
          contentType: MediaType('application', 'pdf'),
        ));
        return request;
      }

      final framing = multipart(1).contentLength - 1;
      expect(framing, greaterThan(0));
      expect(framing, lessThan(1024));
      final fit = multipart(kMaxPreviewWebRequestBytes - framing);
      expect(fit.contentLength, kMaxPreviewWebRequestBytes);
      expect(
        isDocumentMultipartRequestAllowed(fit, sameOriginPreview: true),
        isTrue,
      );
      expect(
        isDocumentMultipartRequestAllowed(
          multipart(kMaxPreviewWebRequestBytes - framing + 1),
          sameOriginPreview: true,
        ),
        isFalse,
      );
      expect(
        isDocumentMultipartRequestAllowed(
          multipart(kMaxPreviewWebRequestBytes),
          sameOriginPreview: true,
        ),
        isFalse,
      );
      final backendMaximum = multipart(kMaxDocumentUploadBytes);
      expect(
        isDocumentMultipartRequestAllowed(
          backendMaximum, sameOriginPreview: true,
        ),
        isFalse,
      );
      expect(
        isDocumentMultipartRequestAllowed(
          backendMaximum, sameOriginPreview: false,
        ),
        isTrue,
      );
    });
  });
}
