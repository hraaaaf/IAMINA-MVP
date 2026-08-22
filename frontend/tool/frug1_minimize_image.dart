import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:amina/services/document_ingest_minimizer.dart';

Future<void> main(List<String> args) async {
  if (args.length != 4 && args.length != 5) {
    stderr.writeln(
      'usage: dart run tool/frug1_minimize_image.dart INPUT OUTPUT FILENAME MIME [METRICS_JSON]',
    );
    exitCode = 64;
    return;
  }

  final input = File(args[0]);
  final output = File(args[1]);
  final source = Uint8List.fromList(await input.readAsBytes());
  final result = minimizeDocumentImage(
    source,
    filename: args[2],
    mimeType: args[3],
  );
  await output.writeAsBytes(result.bytes, flush: true);
  final metrics = jsonEncode({
    'transformed': result.transformed,
    'original_bytes': result.originalByteLength,
    'upload_bytes': result.bytes.length,
    'filename': result.filename,
    'mime_type': result.mimeType,
    'sha256': result.sha256Digest,
  });
  if (args.length == 5) {
    await File(args[4]).writeAsString(metrics, flush: true);
  } else {
    stdout.writeln(metrics);
  }
}
