import 'dart:typed_data';

import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import 'synthetic_report_formatter.dart';

/// Only a non-patient fixture. Do not wire this type to a patient vault,
/// a download, printing, OS sharing or ReportsScreen before CAL-12 approval.
enum SyntheticGlucoseOrigin { manual }

final class SyntheticGlucoseObservation {
  const SyntheticGlucoseObservation({
    required this.recordedAtUtc,
    required this.mgDl,
    this.origin = SyntheticGlucoseOrigin.manual,
  });

  final DateTime recordedAtUtc;

  /// Null = an explicitly unavailable value, never zero or an estimate.
  final int? mgDl;
  final SyntheticGlucoseOrigin origin;
}

final class SyntheticDoctorReport {
  SyntheticDoctorReport({
    required this.generatedAtUtc,
    required this.periodStartUtc,
    required this.periodEndUtc,
    required List<SyntheticGlucoseObservation> observations,
  }) : observations = List.unmodifiable(observations) {
    _validate();
  }

  static const int maxObservations = 12;
  static const String scope = 'synthetic_only';
  final DateTime generatedAtUtc;
  final DateTime periodStartUtc;
  final DateTime periodEndUtc;
  final List<SyntheticGlucoseObservation> observations;

  void _validate() {
    if (!generatedAtUtc.isUtc ||
        !periodStartUtc.isUtc ||
        !periodEndUtc.isUtc) {
      throw ArgumentError('All report instants must be explicitly UTC.');
    }
    if (periodStartUtc.isAfter(periodEndUtc)) {
      throw ArgumentError('Report period must not be inverted.');
    }
    if (observations.isEmpty || observations.length > maxObservations) {
      throw ArgumentError('Requires 1 to $maxObservations synthetic observations.');
    }
    DateTime? previous;
    for (final row in observations) {
      final at = row.recordedAtUtc;
      if (!at.isUtc ||
          at.isBefore(periodStartUtc) ||
          at.isAfter(periodEndUtc)) {
        throw ArgumentError('Observation must be UTC and within the report period.');
      }
      if (previous != null && !at.isAfter(previous)) {
        throw ArgumentError('Observations must be strictly ordered and unique.');
      }
      // This is a formatting sanity bound, NOT an approved clinical target.
      if (row.mgDl != null && (row.mgDl! <= 0 || row.mgDl! > 1000)) {
        throw ArgumentError('A measured value must be positive and bounded.');
      }
      if (row.origin != SyntheticGlucoseOrigin.manual) {
        throw ArgumentError('Only synthetic manual readings are in scope.');
      }
      previous = at;
    }
  }

  /// The CSV/JSON fixture encoder is not authorized for real patient data.
  Uint8List format(SyntheticReportFormat format) =>
      SyntheticReportFormatter.build(
        format: format,
        generatedAtUtc: generatedAtUtc,
        title: 'SYNTHETIC ONLY - NOT A PATIENT REPORT',
        lines: [
          SyntheticReportLine(
            label: 'period_start_utc',
            value: periodStartUtc.toIso8601String(),
            unit: 'UTC',
            source: scope,
          ),
          SyntheticReportLine(
            label: 'period_end_utc',
            value: periodEndUtc.toIso8601String(),
            unit: 'UTC',
            source: scope,
          ),
          for (final row in observations)
            SyntheticReportLine(
              label: row.recordedAtUtc.toIso8601String(),
              value: row.mgDl?.toString() ?? 'not_available',
              unit: 'mg/dL',
              source: 'synthetic_manual',
            ),
        ],
      );
}

/// Proof-of-concept PDF template with embedded offline fonts, no I/O or sharing.
/// A clinician-facing *real* export is strictly blocked until CAL-12 review.
/// Date and numerical spans stay LTR even in the Arabic version: never reverse
/// numbers to simulate Arabic text shaping.
final class SyntheticDoctorPdf {
  const SyntheticDoctorPdf._();

  static Future<Uint8List> build({
    required SyntheticDoctorReport report,
    required ByteData latinFontData,
    required ByteData arabicFontData,
    required String languageCode,
  }) async {
    if (languageCode != 'fr' &&
        languageCode != 'en' &&
        languageCode != 'ar') {
      throw ArgumentError.value(languageCode, 'languageCode');
    }
    final latin = pw.Font.ttf(latinFontData);
    final arabic = pw.Font.ttf(arabicFontData);
    final rtl = languageCode == 'ar';
    final pdf = pw.Document(compress: false);

    pw.Widget label(String fr, String en, String ar, {double size = 10}) {
      return pw.Text(
        rtl ? ar : (languageCode == 'en' ? en : fr),
        textAlign: rtl ? pw.TextAlign.right : pw.TextAlign.left,
        textDirection: rtl ? pw.TextDirection.rtl : pw.TextDirection.ltr,
        style: pw.TextStyle(font: rtl ? arabic : latin, fontSize: size),
      );
    }

    pw.Widget ltrValue(String value) => pw.Text(
      value,
      textDirection: pw.TextDirection.ltr,
      style: pw.TextStyle(font: latin, fontSize: 9),
    );

    pdf.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(36),
        build: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.stretch,
          children: [
            label(
              'Rapport de suivi - SYNTHETIQUE',
              'Follow-up report - SYNTHETIC',
              'تقرير متابعة تجريبي',
              size: 17,
            ),
            pw.SizedBox(height: 6),
            label(
              'Document de démonstration - NON CLINIQUE',
              'Demonstration document - NOT FOR CLINICAL USE',
              'وثيقة تجريبية - غير صالحة للاستخدام الطبي',
              size: 11,
            ),
            pw.SizedBox(height: 18),
            label('Début de période (UTC)', 'Period start (UTC)',
                'بداية الفترة (UTC)'),
            ltrValue(report.periodStartUtc.toIso8601String()),
            pw.SizedBox(height: 7),
            label('Fin de période (UTC)', 'Period end (UTC)',
                'نهاية الفترة (UTC)'),
            ltrValue(report.periodEndUtc.toIso8601String()),
            pw.SizedBox(height: 7),
            label('Généré à (UTC)', 'Generated at (UTC)',
                'تاريخ الإنشاء (UTC)'),
            ltrValue(report.generatedAtUtc.toIso8601String()),
            pw.SizedBox(height: 14),
            pw.Divider(),
            label('Mesures manuelles synthétiques', 'Synthetic manual readings',
                'قياسات يدوية تجريبية', size: 12),
            pw.SizedBox(height: 8),
            for (final row in report.observations)
              pw.Container(
                padding: const pw.EdgeInsets.symmetric(vertical: 5),
                child: pw.Row(
                  children: [
                    pw.Expanded(
                      flex: 5,
                      child: ltrValue(row.recordedAtUtc.toIso8601String()),
                    ),
                    pw.Expanded(
                      flex: 2,
                      child: ltrValue(
                        row.mgDl == null
                            ? 'N/A'
                            : '${row.mgDl} mg/dL',
                      ),
                    ),
                    pw.Expanded(
                      flex: 3,
                      child: label('Manuel / synthétique',
                          'Manual / synthetic', 'يدوي / تجريبي', size: 9),
                    ),
                  ],
                ),
              ),
            pw.SizedBox(height: 16),
            label(
              'Aucune conclusion, prédiction ou cible clinique.',
              'No clinical conclusion, prediction or target.',
              'لا يحتوي على استنتاجات أو توقعات أو أهداف طبية.',
              size: 10,
            ),
          ],
        ),
      ),
    );
    return pdf.save();
  }
}
