import 'dart:convert';

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

  test('D4 typed fixture CSV/JSON are byte stable and sourced', () {
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

  test('D4 Web printable HTML is stable Unicode RTL with isolated numerals', () {
    final report = fixture();
    for (final locale in const ['fr', 'en', 'ar']) {
      final html = SyntheticDoctorHtml.build(
        report: report, languageCode: locale,
      );
      expect(html, SyntheticDoctorHtml.build(
        report: report, languageCode: locale,
      ));
      expect(html, startsWith('<!doctype html>'));
      expect(html, contains('SYNTHETIC ONLY - NOT FOR CLINICAL USE'));
      expect(html, contains('<html lang="$locale"'));
      expect(html, contains('2026-11-02T08:00:00.000Z'));
      expect(html, contains('142 mg/dL'));
      expect(html, contains('>N/A</td>'));
      expect(html, contains('unicode-bidi:isolate'));
      expect(html, contains('assets/fonts/NotoSansArabic.ttf'));
      expect(html, isNot(contains('<script')));
      expect(html, isNot(contains('https://')));
      expect(html, isNot(contains('patient_id')));
    }
    final ar = SyntheticDoctorHtml.build(
      report: report, languageCode: 'ar',
    );
    expect(ar, contains('<html lang="ar" dir="rtl">'));
    expect(ar, contains('تقرير متابعة'));
    expect(ar, contains('<td class="ltr" dir="ltr">142 mg/dL</td>'));
    expect(
      () => SyntheticDoctorHtml.build(
        report: report, languageCode: 'xx',
      ),
      throwsArgumentError,
    );
  });
}
