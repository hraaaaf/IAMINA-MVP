import 'dart:convert';
import 'dart:typed_data';

/// Synthetic-only Reports fixture. Never a patient export or sharing API.
enum SyntheticReportFormat { csv, json }

final class SyntheticReportLine {
  const SyntheticReportLine({
    required this.label,
    required this.value,
    required this.unit,
    required this.source,
  });

  final String label;
  final String value;
  final String unit;
  final String source;
}

/// Pure deterministic formatter, with no file, network, LLM or OS side effect.
///
/// Only synthetic test records are permitted by contract. This is deliberately
/// NOT connected to ReportsScreen, LocalReportPdf or actual patient data.
/// Patient exports require a separately approved typed/consent/privacy gate.
final class SyntheticReportFormatter {
  const SyntheticReportFormatter._();

  static const int maxLines = 200;
  static const int maxFieldLength = 1024;
  static const String fixtureScope = 'synthetic_only';

  static Uint8List build({
    required SyntheticReportFormat format,
    required DateTime generatedAtUtc,
    required String title,
    required List<SyntheticReportLine> lines,
  }) {
    if (!generatedAtUtc.isUtc) {
      throw ArgumentError.value(
        generatedAtUtc, 'generatedAtUtc', 'Must be explicitly UTC.',
      );
    }
    if (lines.isEmpty || lines.length > maxLines) {
      throw ArgumentError.value(
        lines.length, 'lines', 'Requires 1 to $maxLines synthetic lines.',
      );
    }
    _validateField(title, 'title');
    for (final line in lines) {
      _validateField(line.label, 'label');
      _validateField(line.value, 'value');
      _validateField(line.unit, 'unit');
      _validateField(line.source, 'source');
    }

    final date = generatedAtUtc.toIso8601String();
    final text = switch (format) {
      SyntheticReportFormat.json => _json(title, date, lines),
      SyntheticReportFormat.csv => _csv(title, date, lines),
    };
    return Uint8List.fromList(utf8.encode(text));
  }

  static String _json(
    String title, String date, List<SyntheticReportLine> lines,
  ) {
    return jsonEncode({
      'schema_version': 1,
      'fixture_scope': fixtureScope,
      'generated_at_utc': date,
      'title': title,
      'lines': [
        for (final line in lines)
          {
            'label': line.label,
            'value': line.value,
            'unit': line.unit,
            'source': line.source,
          },
      ],
    });
  }

  static String _csv(
    String title, String date, List<SyntheticReportLine> lines,
  ) {
    final records = <List<String>>[
      [
        'schema_version', 'fixture_scope', 'generated_at_utc',
        'title', 'label', 'value', 'unit', 'source',
      ],
      for (final line in lines)
        [
          '1', fixtureScope, date, title,
          line.label, line.value, line.unit, line.source,
        ],
    ];
    // RFC 4180's CRLF record separator and doubled embedded quotes;
    // always quote fields to preserve Unicode, commas and semicolons.
    return '${records.map((record) => record.map(_quote).join(',')).join('\r\n')}\r\n';
  }

  static String _quote(String value) => '"${value.replaceAll('"', '""')}"';

  static void _validateField(String value, String name) {
    if (value.trim().isEmpty || value.length > maxFieldLength) {
      throw FormatException('$name must be nonempty and bounded.');
    }
    // Fail closed on spreadsheet formula prefixes (including whitespace and
    // fullwidth lookalikes). Do not rely on apostrophe/quote/tab escaping:
    // spreadsheet applications differ and may re-enable formula execution.
    final trimmed = value.trimLeft();
    const formulaStarts = ['=', '+', '-', '@', '＝', '＋', '－', '＠'];
    if (formulaStarts.any(trimmed.startsWith)) {
      throw FormatException('$name contains a spreadsheet formula prefix.');
    }
    // This synthetic strict subset excludes controls and bidi overrides,
    // rather than permitting hidden cell/record or visual reordering attacks.
    for (final rune in value.runes) {
      if (rune < 0x20 || rune == 0x7f ||
          (rune >= 0x202a && rune <= 0x202e)) {
        throw FormatException('$name contains a control character.');
      }
    }
  }
}
