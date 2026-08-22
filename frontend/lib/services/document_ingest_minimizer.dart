import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:image/image.dart' as img;

import 'auth_epoch.dart';

const int kDocumentImageMaxPixels = 32000000;
const int kDocumentPngCompressionLevel = 9;

class DocumentStreamLimitExceeded implements Exception {
  const DocumentStreamLimitExceeded();

  @override
  String toString() => 'document stream exceeded configured upload limit';
}

class MinimizedDocument {
  const MinimizedDocument({
    required this.bytes,
    required this.filename,
    required this.mimeType,
    required this.sha256Digest,
    required this.originalByteLength,
    required this.transformed,
  });

  final Uint8List bytes;
  final String filename;
  final String mimeType;
  final String sha256Digest;
  final int originalByteLength;
  final bool transformed;

  int get savedBytes => originalByteLength - bytes.length;
}

class PendingDocumentDeduplicator<T> {
  PendingDocumentDeduplicator({int Function()? scopeEpoch})
    : _scopeEpoch = scopeEpoch ?? (() => AuthEpoch.value);

  final int Function() _scopeEpoch;
  final Map<String, T> _byDigest = {};
  final Map<String, String> _digestByBatch = {};
  int? _lastScopeEpoch;

  T? lookup(String digest) {
    _syncScope();
    return _byDigest[digest];
  }

  void remember({
    required String digest,
    required String batchId,
    required T value,
  }) {
    _syncScope();
    _byDigest[digest] = value;
    _digestByBatch[batchId] = digest;
  }

  void clearBatch(String batchId) {
    _syncScope();
    final digest = _digestByBatch.remove(batchId);
    if (digest != null) {
      _byDigest.remove(digest);
    }
  }

  void clear() {
    _byDigest.clear();
    _digestByBatch.clear();
    _lastScopeEpoch = _scopeEpoch();
  }

  void _syncScope() {
    final currentScopeEpoch = _scopeEpoch();
    if (_lastScopeEpoch == currentScopeEpoch) return;
    _byDigest.clear();
    _digestByBatch.clear();
    _lastScopeEpoch = currentScopeEpoch;
  }
}

bool isMinimizableDocumentImage({
  required String filename,
  required String mimeType,
}) {
  final normalizedMime = mimeType.toLowerCase().trim();
  final extension = filename.toLowerCase().split('.').last;
  if (extension == 'heic' || extension == 'heif') return false;
  return normalizedMime == 'image/jpeg' ||
      normalizedMime == 'image/png' ||
      normalizedMime == 'image/webp';
}

Future<Uint8List> readDocumentStreamBounded(
  Stream<List<int>> stream, {
  required int maxBytes,
}) async {
  if (maxBytes <= 0) {
    throw ArgumentError.value(maxBytes, 'maxBytes', 'must be positive');
  }
  final builder = BytesBuilder(copy: false);
  var total = 0;
  await for (final chunk in stream) {
    total += chunk.length;
    if (total > maxBytes) {
      throw const DocumentStreamLimitExceeded();
    }
    builder.add(chunk);
  }
  return builder.takeBytes();
}

MinimizedDocument minimizeDocumentImage(
  Uint8List source, {
  required String filename,
  required String mimeType,
}) {
  MinimizedDocument unchanged() => MinimizedDocument(
    bytes: source,
    filename: filename,
    mimeType: mimeType,
    sha256Digest: sha256.convert(source).toString(),
    originalByteLength: source.length,
    transformed: false,
  );

  if (!isMinimizableDocumentImage(filename: filename, mimeType: mimeType)) {
    return unchanged();
  }

  try {
    final decoder = _decoderForMime(mimeType);
    if (decoder == null || !decoder.isValidFile(source)) return unchanged();
    final info = decoder.startDecode(source);
    if (info == null || info.numFrames != 1) return unchanged();
    final pixelCount = info.width * info.height;
    if (pixelCount <= 0 || pixelCount > kDocumentImageMaxPixels) {
      return unchanged();
    }

    final decoded = decoder.decodeFrame(0);
    if (decoded == null || _hasTransparency(decoded)) return unchanged();

    final normalized = img.bakeOrientation(decoded)
      ..exif.clear()
      ..iccProfile = null
      ..textData = null;

    if (mimeType.toLowerCase().trim() != 'image/png') return unchanged();

    final encoded = img.encodePng(
      normalized,
      level: kDocumentPngCompressionLevel,
    );
    if (encoded.length >= source.length) return unchanged();

    return MinimizedDocument(
      bytes: encoded,
      filename: _asPngFilename(filename),
      mimeType: 'image/png',
      sha256Digest: sha256.convert(encoded).toString(),
      originalByteLength: source.length,
      transformed: true,
    );
  } catch (_) {
    return unchanged();
  }
}

bool _hasTransparency(img.Image image) {
  if (!image.hasAlpha) return false;
  for (final pixel in image) {
    if (pixel.a != pixel.maxChannelValue) return true;
  }
  return false;
}

img.Decoder? _decoderForMime(String mimeType) {
  return switch (mimeType.toLowerCase().trim()) {
    'image/jpeg' => img.JpegDecoder(),
    'image/png' => img.PngDecoder(),
    'image/webp' => img.WebPDecoder(),
    _ => null,
  };
}

String _asPngFilename(String filename) {
  final dot = filename.lastIndexOf('.');
  if (dot <= 0) return '$filename.png';
  return '${filename.substring(0, dot)}.png';
}
