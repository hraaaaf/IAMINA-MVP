import 'dart:convert';

import 'package:amina/services/local_report_pdf.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final generatedAt = DateTime.utc(2026, 9, 1, 12, 0);
  const lines = <LocalReportLine>[
    LocalReportLine('Fixture', 'SYNTHETIC-P5-5'),
    LocalReportLine('Glucose source', 'synthetic manual entry'),
    LocalReportLine('Context', r'meal (synthetic) \ rehearsal'),
  ];

  test('builds deterministic structurally indexed PDF bytes', () {
    final first = LocalReportPdf.build(
      title: 'IAMINA P5-5 Synthetic Report',
      generatedAtUtc: generatedAt,
      lines: lines,
    );
    final second = LocalReportPdf.build(
      title: 'IAMINA P5-5 Synthetic Report',
      generatedAtUtc: generatedAt,
      lines: lines,
    );

    expect(first, orderedEquals(second));

    final text = latin1.decode(first);
    expect(text, startsWith('%PDF-1.4\n'));
    expect(text, endsWith('%%EOF\n'));
    expect(text, contains('(Fixture: SYNTHETIC-P5-5) Tj'));
    expect(
      text,
      contains(r'(Context: meal \(synthetic\) \\ rehearsal) Tj'),
    );

    final startXref = RegExp(r'startxref\n(\d+)\n%%EOF').firstMatch(text);
    expect(startXref, isNotNull);
    final xrefOffset = int.parse(startXref!.group(1)!);
    expect(text.substring(xrefOffset), startsWith('xref\n'));

    final xrefBlock = text.substring(xrefOffset);
    final entries = RegExp(r'(\d{10}) 00000 n ').allMatches(xrefBlock).toList();
    expect(entries, hasLength(5));
    for (var index = 0; index < entries.length; index++) {
      final offset = int.parse(entries[index].group(1)!);
      expect(text.substring(offset), startsWith('${index + 1} 0 obj\n'));
    }
  });

  test('fails explicitly for unqualified Unicode instead of corrupting it', () {
    expect(
      () => LocalReportPdf.build(
        title: 'IAMINA synthetic report',
        generatedAtUtc: generatedAt,
        lines: const <LocalReportLine>[
          LocalReportLine('Arabic', 'تقرير تجريبي'),
        ],
      ),
      throwsArgumentError,
    );
  });

  test('fails explicitly when single-page export limits would be exceeded', () {
    expect(
      () => LocalReportPdf.build(
        title: 'IAMINA synthetic report',
        generatedAtUtc: generatedAt,
        lines: List<LocalReportLine>.generate(
          LocalReportPdf.maxLines + 1,
          (index) => LocalReportLine('Row', 'synthetic-$index'),
        ),
      ),
      throwsArgumentError,
    );

    final tooLongValue = List<String>.filled(
      LocalReportPdf.maxCharsPerLine,
      'x',
    ).join();
    expect(
      () => LocalReportPdf.build(
        title: 'IAMINA synthetic report',
        generatedAtUtc: generatedAt,
        lines: <LocalReportLine>[LocalReportLine('Row', tooLongValue)],
      ),
      throwsArgumentError,
    );
  });

  test('requires UTC timestamp for deterministic evidence', () {
    expect(
      () => LocalReportPdf.build(
        title: 'IAMINA synthetic report',
        generatedAtUtc: DateTime(2026, 9, 1, 12),
        lines: lines,
      ),
      throwsArgumentError,
    );
  });
}
