import 'dart:convert';
import 'dart:typed_data';

/// One synthetic/local report row.
final class LocalReportLine {
  const LocalReportLine(this.label, this.value);

  final String label;
  final String value;
}

/// Minimal deterministic PDF export primitive for retained local report data.
///
/// This deliberately supports printable ASCII only. Unsupported text fails
/// explicitly instead of silently corrupting Arabic/Unicode content. It is a
/// machine-testable export primitive, not a UI sharing/printing claim.
final class LocalReportPdf {
  const LocalReportPdf._();

  static const int maxLines = 42;
  static const int maxCharsPerLine = 88;

  static Uint8List build({
    required String title,
    required DateTime generatedAtUtc,
    required List<LocalReportLine> lines,
  }) {
    if (!generatedAtUtc.isUtc) {
      throw ArgumentError.value(
        generatedAtUtc,
        'generatedAtUtc',
        'Report timestamp must be UTC for deterministic output.',
      );
    }
    if (title.trim().isEmpty) {
      throw ArgumentError.value(title, 'title', 'Report title must not be empty.');
    }
    if (lines.isEmpty) {
      throw ArgumentError.value(lines, 'lines', 'Report must contain at least one line.');
    }
    if (lines.length > maxLines) {
      throw ArgumentError.value(
        lines.length,
        'lines',
        'Report exceeds the single-page deterministic export limit.',
      );
    }

    final timestamp = generatedAtUtc.toIso8601String();
    _validateLine(title);
    _validateLine('Generated: $timestamp');
    for (final line in lines) {
      _validateLine('${line.label}: ${line.value}');
    }

    final content = StringBuffer()
      ..writeln('BT')
      ..writeln('/F1 14 Tf')
      ..writeln('50 790 Td')
      ..writeln('(${_escapePdfString(title)}) Tj')
      ..writeln('/F1 10 Tf')
      ..writeln('0 -22 Td')
      ..writeln('(Generated: ${_escapePdfString(timestamp)}) Tj');

    for (final line in lines) {
      content
        ..writeln('0 -14 Td')
        ..writeln(
          '(${_escapePdfString('${line.label}: ${line.value}')}) Tj',
        );
    }
    content.writeln('ET');

    final contentBytes = latin1.encode(content.toString());
    final stream = BytesBuilder(copy: false)
      ..add(latin1.encode('<< /Length ${contentBytes.length} >>\nstream\n'))
      ..add(contentBytes)
      ..add(latin1.encode('endstream'));

    final objects = <List<int>>[
      latin1.encode('<< /Type /Catalog /Pages 2 0 R >>'),
      latin1.encode('<< /Type /Pages /Kids [3 0 R] /Count 1 >>'),
      latin1.encode(
        '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] '
        '/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
      ),
      latin1.encode('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'),
      stream.takeBytes(),
    ];

    final pdf = BytesBuilder(copy: false)
      ..add(latin1.encode('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n'));
    final offsets = <int>[0];

    for (var index = 0; index < objects.length; index++) {
      offsets.add(pdf.length);
      pdf
        ..add(latin1.encode('${index + 1} 0 obj\n'))
        ..add(objects[index])
        ..add(latin1.encode('\nendobj\n'));
    }

    final xrefOffset = pdf.length;
    final xref = StringBuffer()
      ..writeln('xref')
      ..writeln('0 ${objects.length + 1}')
      ..writeln('0000000000 65535 f ');
    for (final offset in offsets.skip(1)) {
      xref.writeln('${offset.toString().padLeft(10, '0')} 00000 n ');
    }
    xref
      ..writeln('trailer')
      ..writeln('<< /Size ${objects.length + 1} /Root 1 0 R >>')
      ..writeln('startxref')
      ..writeln(xrefOffset)
      ..writeln('%%EOF');
    pdf.add(latin1.encode(xref.toString()));

    return pdf.takeBytes();
  }

  static void _validateLine(String text) {
    if (text.length > maxCharsPerLine) {
      throw ArgumentError.value(
        text.length,
        'text',
        'Report line exceeds the deterministic single-line width limit.',
      );
    }
    final unsupported = text.codeUnits.any(
      (unit) => unit < 0x20 || unit > 0x7e,
    );
    if (unsupported) {
      throw ArgumentError.value(
        text,
        'text',
        'Only printable ASCII is currently qualified for local PDF export.',
      );
    }
  }

  static String _escapePdfString(String value) => value
      .replaceAll('\\', '\\\\')
      .replaceAll('(', r'\(')
      .replaceAll(')', r'\)');
}
