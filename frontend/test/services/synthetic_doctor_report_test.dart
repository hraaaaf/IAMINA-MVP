import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:amina/services/synthetic_doctor_report.dart';
import 'package:amina/services/synthetic_report_formatter.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final start = DateTime.utc(2026, 11, 1);
  final end = DateTime.utc(2026, 11, 8, 23, 59);
  final generated = DateTime.utc(2026, 11, 9, 20);
  SyntheticDoctorReport fixture() => SyntheticDoctorReport(
    generatedAtUtc: generated,
    periodStartUtc: start,
    periodEndUtc: end,
    observations: [
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 2, 8),
        mgDl: 142,
      ),
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 3, 11),
        mgDl: null,
      ),
    ],
  );

  test('D4 typed fixture CSV/JSON are byte stable, sourced and not patient data', () {
    final report = fixture();
    for (final format in SyntheticReportFormat.values) {
      final first = report.format(format);
      final second = report.format(format);
      expect(first, orderedEquals(second));
      final text = utf8.decode(first);
      expect(text, contains('synthetic_only'));
      expect(text, contains('2026-11-02T08:00:00.000Z'));
      expect(text, contains('142'));
      expect(text, contains('not_available'));
      expect(text, contains('synthetic_manual'));
      expect(text, isNot(contains('patient_id')));
    }
    final json = jsonDecode(utf8.decode(
      report.format(SyntheticReportFormat.json),
    )) as Map<String, dynamic>;
    expect(json['fixture_scope'], 'synthetic_only');
    expect((json['lines'] as List).length, 4);
    final csv = utf8.decode(report.format(SyntheticReportFormat.csv));
    expect(csv, startsWith('"schema_version","fixture_scope"'));
    expect(csv, endsWith('\r\n'));
    expect('\r\n'.allMatches(csv).length, 5);
  });

  test('D4 rejects missing UTC, reversed periods and untrusted readings', () {
    expect(
      () => SyntheticDoctorReport(
        generatedAtUtc: DateTime(2026, 11, 9),
        periodStartUtc: start, periodEndUtc: end,
        observations: fixture().observations,
      ),
      throwsArgumentError,
    );
    expect(
      () => SyntheticDoctorReport(
        generatedAtUtc: generated,
        periodStartUtc: end, periodEndUtc: start,
        observations: fixture().observations,
      ),
      throwsArgumentError,
    );
    for (final invalid in [0, -1, 1001]) {
      expect(
        () => SyntheticDoctorReport(
          generatedAtUtc: generated,
          periodStartUtc: start, periodEndUtc: end,
          observations: [
            SyntheticGlucoseObservation(
              recordedAtUtc: DateTime.utc(2026, 11, 2),
              mgDl: invalid,
            ),
          ],
        ),
        throwsArgumentError,
      );
    }
    expect(
      () => SyntheticDoctorReport(
        generatedAtUtc: generated,
        periodStartUtc: start, periodEndUtc: end,
        observations: const [],
      ),
      throwsArgumentError,
    );
    expect(
      () => SyntheticDoctorReport(
        generatedAtUtc: generated,
        periodStartUtc: start, periodEndUtc: end,
        observations: [
          SyntheticGlucoseObservation(
            recordedAtUtc: DateTime.utc(2026, 11, 3),
            mgDl: 120,
          ),
          SyntheticGlucoseObservation(
            recordedAtUtc: DateTime.utc(2026, 11, 2),
            mgDl: 140,
          ),
        ],
      ),
      throwsArgumentError,
    );
    expect(
      () => SyntheticDoctorReport(
        generatedAtUtc: generated,
        periodStartUtc: start, periodEndUtc: end,
        observations: [
          SyntheticGlucoseObservation(
            recordedAtUtc: DateTime.utc(2026, 10, 30),
            mgDl: 120,
          ),
        ],
      ),
      throwsArgumentError,
    );
  });

  test('D4 PDF FR/EN/AR uses embedded offline fonts and marks synthetic scope',
      () async {
    final latin = ByteData.sublistView(
      File('assets/fonts/Inter.ttf').readAsBytesSync(),
    );
    final arabic = ByteData.sublistView(
      File('assets/fonts/NotoSansArabic.ttf').readAsBytesSync(),
    );
    for (final locale in const ['fr', 'en', 'ar']) {
      final bytes = await SyntheticDoctorPdf.build(
        report: fixture(),
        latinFontData: latin,
        arabicFontData: arabic,
        languageCode: locale,
      );
      expect(bytes.length, greaterThan(3000));
      expect(utf8.decode(bytes.take(5).toList()), '%PDF-');
      final raw = latin1.decode(bytes);
      expect(raw, contains('%%EOF'));
      expect(raw, contains('/FontFile2'));
      expect(raw, contains('/ToUnicode'));
      // This is a synthetic template test, not a visual/clinical qualification.
    }
    expect(
      () => SyntheticDoctorPdf.build(
        report: fixture(),
        latinFontData: latin,
        arabicFontData: arabic,
        languageCode: 'xx',
      ),
      throwsArgumentError,
    );
  });
}
