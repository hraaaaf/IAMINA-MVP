import 'dart:typed_data';

import 'package:amina/services/document_ingest_minimizer.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;

void main() {
  group('document ingest minimizer', () {
    test('HEIC and unsupported inputs stay byte-identical', () {
      final bytes = Uint8List.fromList([1, 2, 3, 4]);
      final result = minimizeDocumentImage(
        bytes,
        filename: 'scan.heic',
        mimeType: 'image/heic',
      );
      expect(result.transformed, isFalse);
      expect(result.bytes, orderedEquals(bytes));
      expect(result.filename, 'scan.heic');
      expect(result.sha256Digest.length, 64);
    });

    test('candidate classification is image-only and excludes HEIC', () {
      expect(isMinimizableDocumentImage(filename: 'scan.jpg', mimeType: 'image/jpeg'), isTrue);
      expect(isMinimizableDocumentImage(filename: 'scan.png', mimeType: 'image/png'), isTrue);
      expect(isMinimizableDocumentImage(filename: 'scan.webp', mimeType: 'image/webp'), isTrue);
      expect(isMinimizableDocumentImage(filename: 'scan.heic', mimeType: 'image/heic'), isFalse);
      expect(isMinimizableDocumentImage(filename: 'report.pdf', mimeType: 'application/pdf'), isFalse);
    });

    test('wasteful opaque PNG is recompressed losslessly', () {
      final source = img.Image(width: 512, height: 512);
      for (final pixel in source) {
        pixel
          ..r = (pixel.x ~/ 32) * 16
          ..g = (pixel.y ~/ 32) * 16
          ..b = ((pixel.x + pixel.y) ~/ 64) * 16;
      }
      final png = img.encodePng(source, level: 0);
      final result = minimizeDocumentImage(
        png,
        filename: 'scan.png',
        mimeType: 'image/png',
      );
      expect(result.transformed, isTrue);
      expect(result.mimeType, 'image/png');
      expect(result.bytes.length, lessThan(png.length));
      final decoded = img.decodePng(result.bytes);
      expect(decoded, isNotNull);
      expect(decoded!.width, source.width);
      expect(decoded.height, source.height);
      for (final point in <(int, int)>[(0, 0), (31, 127), (255, 255), (511, 511)]) {
        final before = source.getPixel(point.$1, point.$2);
        final after = decoded.getPixel(point.$1, point.$2);
        expect(after.r, before.r);
        expect(after.g, before.g);
        expect(after.b, before.b);
        expect(after.a, before.a);
      }
    });

    test('JPEG passes through rather than risking lossy OCR drift', () {
      final source = img.Image(width: 256, height: 256);
      for (final pixel in source) {
        pixel
          ..r = (pixel.x * 7 + pixel.y * 3) % 256
          ..g = (pixel.x * 5 + pixel.y * 11) % 256
          ..b = (pixel.x * 13 + pixel.y * 2) % 256;
      }
      final jpeg = img.encodeJpg(source, quality: 100);
      final result = minimizeDocumentImage(
        jpeg,
        filename: 'scan.jpg',
        mimeType: 'image/jpeg',
      );
      expect(result.transformed, isFalse);
      expect(result.bytes, orderedEquals(jpeg));
    });

    test('actually transparent image passes through rather than flattening', () {
      final source = img.Image(width: 64, height: 64, numChannels: 4);
      for (final pixel in source) {
        pixel.a = pixel.maxChannelValue;
      }
      source.getPixel(0, 0).a = 0;
      final png = img.encodePng(source);
      final result = minimizeDocumentImage(
        png,
        filename: 'alpha.png',
        mimeType: 'image/png',
      );
      expect(result.transformed, isFalse);
      expect(result.bytes, orderedEquals(png));
    });

    test('digest is stable for the exact bytes selected for upload', () {
      final source = Uint8List.fromList([9, 8, 7, 6]);
      final first = minimizeDocumentImage(source, filename: 'not-an-image.jpg', mimeType: 'image/jpeg');
      final second = minimizeDocumentImage(source, filename: 'not-an-image.jpg', mimeType: 'image/jpeg');
      expect(first.sha256Digest, second.sha256Digest);
      expect(first.sha256Digest.length, 64);
    });

    test('pending dedup reuses exact digest only until batch confirmation', () {
      final dedup = PendingDocumentDeduplicator<String>();
      expect(dedup.lookup('digest-a'), isNull);
      dedup.remember(digest: 'digest-a', batchId: 'batch-a', value: 'preview-a');
      expect(dedup.lookup('digest-a'), 'preview-a');
      expect(dedup.lookup('digest-b'), isNull);
      dedup.clearBatch('batch-a');
      expect(dedup.lookup('digest-a'), isNull);
    });

    test('pending dedup is cleared when authentication scope changes', () {
      var scopeEpoch = 1;
      final dedup = PendingDocumentDeduplicator<String>(scopeEpoch: () => scopeEpoch);
      dedup.remember(digest: 'digest-a', batchId: 'batch-a', value: 'preview-a');
      expect(dedup.lookup('digest-a'), 'preview-a');
      scopeEpoch = 2;
      expect(dedup.lookup('digest-a'), isNull);
    });

    test('bounded stream reader refuses actual bytes beyond the cap', () async {
      final stream = Stream<List<int>>.fromIterable([
        [1, 2],
        [3, 4],
      ]);
      expect(
        () => readDocumentStreamBounded(stream, maxBytes: 3),
        throwsA(isA<DocumentStreamLimitExceeded>()),
      );
    });
  });
}
