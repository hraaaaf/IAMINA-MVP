import 'dart:io';

import 'package:amina/services/synthetic_doctor_report.dart';

/// CI-only real Chromium print-to-PDF of an offline synthetic Web document.
/// This never reads any real patient data or calls the product's share/download.
Future<void> main() async {
  final output = Directory('build/d4-synthetic-proof');
  output.createSync(recursive: true);
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
  // Render the three-row fixture and the strict 12-row maximum in all locales.
  final fixtures = <String, SyntheticDoctorReport>{
    '': fixture,
    '-MAX': SyntheticDoctorReport(
      generatedAtUtc: fixture.generatedAtUtc,
      periodStartUtc: fixture.periodStartUtc,
      periodEndUtc: fixture.periodEndUtc,
      observations: List.generate(
        SyntheticDoctorReport.maxObservations,
        (i) => SyntheticGlucoseObservation(
          recordedAtUtc: DateTime.utc(2026, 11, 2 + i ~/ 2, i.isEven ? 8 : 20),
          mgDl: i == 5 ? null : 110 + i,
        ),
      ),
    ),
  };
  final chrome = Platform.environment['CHROME_BIN'] ?? 'google-chrome';
  for (final entry in fixtures.entries) {
    for (final languageCode in const ['fr', 'en', 'ar']) {
    final name = 'D4-SYNTHETIC${entry.key}-$languageCode';
    final htmlFile = File('${output.path}/$name.html');
    final pdfFile = File('${output.path}/$name.pdf');
    await htmlFile.writeAsString(
      SyntheticDoctorHtml.build(
        report: entry.value,
        languageCode: languageCode,
      ),
      flush: true,
    );

    final result = await Process.run(chrome, [
      '--headless=new',
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--no-pdf-header-footer',
      '--virtual-time-budget=15000',
      '--print-to-pdf=${pdfFile.absolute.path}',
      htmlFile.absolute.uri.toString(),
    ]);
    if (result.exitCode != 0 || !pdfFile.existsSync() ||
        pdfFile.lengthSync() < 3000) {
      throw StateError(
        'Chromium failed to produce synthetic PDF for $languageCode: '
        '${result.exitCode}: ${result.stderr}',
      );
    }
    stdout.writeln(
      'D4_SYNTHETIC_ONLY ${pdfFile.path} ${pdfFile.lengthSync()} bytes',
    );
    }
  }
}
