import 'dart:io';
import 'dart:typed_data';

import 'package:amina/services/synthetic_doctor_report.dart';

/// CI-only synthetic fixture generation. Never load a patient vault.
Future<void> main() async {
  final output = Directory('build/d4-synthetic-proof');
  output.createSync(recursive: true);
  final latin = ByteData.sublistView(
    File('assets/fonts/Inter.ttf').readAsBytesSync(),
  );
  final arabic = ByteData.sublistView(
    File('assets/fonts/NotoSansArabic.ttf').readAsBytesSync(),
  );
  final fixture = SyntheticDoctorReport(
    generatedAtUtc: DateTime.utc(2026, 11, 9, 18),
    periodStartUtc: DateTime.utc(2026, 11, 1),
    periodEndUtc: DateTime.utc(2026, 11, 8, 23, 59),
    observations: [
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 2, 8),
        mgDl: 142,
      ),
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 4, 14, 30),
        mgDl: null,
      ),
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 6, 19),
        mgDl: 110,
      ),
    ],
  );
  for (final languageCode in const ['fr', 'en', 'ar']) {
    final data = await SyntheticDoctorPdf.build(
      report: fixture,
      latinFontData: latin,
      arabicFontData: arabic,
      languageCode: languageCode,
    );
    final file = File('${output.path}/D4-SYNTHETIC-$languageCode.pdf');
    await file.writeAsBytes(data, flush: true);
    stdout.writeln('D4_SYNTHETIC_ONLY ${file.path} ${data.length} bytes');
  }
}
