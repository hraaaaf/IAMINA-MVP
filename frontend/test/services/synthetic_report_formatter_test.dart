import 'dart:convert';

import 'package:amina/services/synthetic_report_formatter.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final generatedAt = DateTime.utc(2026, 10, 12, 18, 0);
  const rows = [
    SyntheticReportLine(
      label: 'Glycémie, "test" / سكر',
      value: '142', unit: 'mg/dL', source: 'synthetic manual',
    ),
    SyntheticReportLine(
      label: 'Interprétation; تجريبي',
      value: 'Descriptif فقط', unit: 'text', source: 'synthetic source',
    ),
  ];

  test('synthetic-only CSV is deterministic, Unicode and RFC4180 quoted', () {
    final a = SyntheticReportFormatter.build(
      format: SyntheticReportFormat.csv,
      generatedAtUtc: generatedAt, title: 'SYNTHETIC, Example', lines: rows,
    );
    final b = SyntheticReportFormatter.build(
      format: SyntheticReportFormat.csv,
      generatedAtUtc: generatedAt, title: 'SYNTHETIC, Example', lines: rows,
    );
    expect(a, orderedEquals(b));
    final csv = utf8.decode(a);
    expect(csv, startsWith('"schema_version","fixture_scope",'));
    expect(csv, contains('"synthetic_only"'));
    expect(csv, contains('"Glycémie, ""test"" / سكر"'));
    expect(csv, contains('"Interprétation; تجريبي"'));
    expect(csv, contains('"2026-10-12T18:00:00.000Z"'));
    expect(csv, endsWith('\r\n'));
    expect('\r\n'.allMatches(csv).length, 3); // header + two rows
  });

  test('synthetic-only JSON is stable, explicit and lossless for Arabic', () {
    final a = SyntheticReportFormatter.build(
      format: SyntheticReportFormat.json,
      generatedAtUtc: generatedAt, title: 'SYNTHETIC', lines: rows,
    );
    final b = SyntheticReportFormatter.build(
      format: SyntheticReportFormat.json,
      generatedAtUtc: generatedAt, title: 'SYNTHETIC', lines: rows,
    );
    expect(a, orderedEquals(b));
    final payload = jsonDecode(utf8.decode(a)) as Map<String, dynamic>;
    expect(payload['schema_version'], 1);
    expect(payload['fixture_scope'], 'synthetic_only');
    expect(payload['generated_at_utc'], '2026-10-12T18:00:00.000Z');
    final decoded = payload['lines'] as List;
    expect((decoded[0] as Map<String, dynamic>)['label'],
        'Glycémie, "test" / سكر');
    expect((decoded[1] as Map<String, dynamic>)['value'], 'Descriptif فقط');
  });

  for (final dangerous in [
    '=HYPERLINK("https://example.invalid")',
    '+SUM(1,2)', '-1+2', '@EVAL()', '  =1+2',
    '＝1+2', '＋1+2', '－1+2', '＠EVAL()',
    '\t=1+2', 'part\n=1+2', 'abc\u202edef',
  ]) {
    test('rejects unsafe spreadsheet text $dangerous in both formats', () {
      for (final format in SyntheticReportFormat.values) {
        expect(
          () => SyntheticReportFormatter.build(
            format: format, generatedAtUtc: generatedAt,
            title: 'SYNTHETIC',
            lines: [
              SyntheticReportLine(
                label: 'Synthetic', value: dangerous,
                unit: 'text', source: 'synthetic only',
              ),
            ],
          ),
          throwsFormatException,
        );
      }
    });
  }

  test('rejects naive timestamps, absent provenance and absent lines', () {
    expect(
      () => SyntheticReportFormatter.build(
        format: SyntheticReportFormat.csv,
        generatedAtUtc: DateTime(2026, 10, 12),
        title: 'SYNTHETIC', lines: rows,
      ),
      throwsArgumentError,
    );
    expect(
      () => SyntheticReportFormatter.build(
        format: SyntheticReportFormat.json,
        generatedAtUtc: generatedAt, title: 'SYNTHETIC',
        lines: const [
          SyntheticReportLine(
            label: 'SYNTHETIC', value: '142',
            unit: 'mg/dL', source: ' ',
          ),
        ],
      ),
      throwsFormatException,
    );
    expect(
      () => SyntheticReportFormatter.build(
        format: SyntheticReportFormat.csv,
        generatedAtUtc: generatedAt, title: 'SYNTHETIC',
        lines: const [],
      ),
      throwsArgumentError,
    );
  });
}
