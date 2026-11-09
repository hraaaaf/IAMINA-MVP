import 'dart:typed_data';

import 'synthetic_report_formatter.dart';

/// Only a non-patient fixture. Never connect to a vault or download/share UI
/// before the independently signed CAL-12 clinical and privacy gate.
enum SyntheticGlucoseOrigin { manual }

final class SyntheticGlucoseObservation {
  const SyntheticGlucoseObservation({
    required this.recordedAtUtc,
    required this.mgDl,
    this.origin = SyntheticGlucoseOrigin.manual,
  });

  final DateTime recordedAtUtc;
  /// Null means missing, never zero or an estimated/CGM value.
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
      // A formatting sanity bound, not an approved clinical target.
      if (row.mgDl != null && (row.mgDl! <= 0 || row.mgDl! > 1000)) {
        throw ArgumentError('A measured value must be positive and bounded.');
      }
      if (row.origin != SyntheticGlucoseOrigin.manual) {
        throw ArgumentError('Only synthetic manual readings are in scope.');
      }
      previous = at;
    }
  }

  /// Byte-stable synthetic fixture; no names, IDs or patient datasource.
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

/// Local-first Web print layout *prototype* only, not a patient PDF generator.
/// A separate CI script prints this self-contained HTML to an actual PDF using
/// headless Chromium; no PDF/printing dependency or clinical product path.
///
/// Numeric/date spans are explicitly LTR, while Arabic labels flow RTL.
final class SyntheticDoctorHtml {
  const SyntheticDoctorHtml._();

  static String build({
    required SyntheticDoctorReport report,
    required String languageCode,
  }) {
    if (!const ['fr', 'en', 'ar'].contains(languageCode)) {
      throw ArgumentError.value(languageCode, 'languageCode');
    }
    final rtl = languageCode == 'ar';
    String label(String fr, String en, String ar) =>
        rtl ? ar : (languageCode == 'en' ? en : fr);

    // No patient-supplied strings, HTML injection, network imports, scripts or
    // external assets. The ONLY fonts are bundled locally inside IAMINA.
    final html = StringBuffer()
      ..writeln('<!doctype html>')
      ..writeln('<html lang="$languageCode" dir="${rtl ? 'rtl' : 'ltr'}">')
      ..writeln('<head><meta charset="utf-8">')
      ..writeln('<meta name="viewport" content="width=device-width">')
      ..writeln('<title>D4 SYNTHETIC ONLY</title>')
      ..writeln('<style>')
      ..writeln('@font-face{font-family:Inter;src:url("../../assets/fonts/Inter.ttf") format("truetype")}')
      ..writeln('@font-face{font-family:NotoArabic;src:url("../../assets/fonts/NotoSansArabic.ttf") format("truetype")}')
      ..writeln('@page{size:A4;margin:20mm}')
      ..writeln('html,body{padding:0;margin:0;color:#173b34;background:white}')
      ..writeln('body{font-family:Inter,Arial,sans-serif;font-size:11pt;line-height:1.5}')
      ..writeln('html[dir=rtl] body{font-family:NotoArabic,Inter,sans-serif}')
      ..writeln('.masthead{border-bottom:3px solid #1d7565;padding-bottom:14px}')
      ..writeln('h1{font-size:19pt;margin:0 0 9px}')
      ..writeln('.banner{color:#813b2e;font-weight:bold;font-size:12pt;margin:0}')
      ..writeln('.facts{padding:15px 0 10px}')
      ..writeln('.label{font-weight:600;margin:0 0 2px}')
      ..writeln('.date{font-family:Inter,monospace;font-size:9pt}')
      ..writeln('.ltr{direction:ltr;unicode-bidi:isolate;text-align:left;font-family:Inter,monospace}')
      ..writeln('table{border-collapse:collapse;width:100%;margin-top:12px}')
      ..writeln('th,td{border-bottom:1px solid #c5d9d2;padding:8px 6px;vertical-align:top}')
      ..writeln('th{background:#e8f4f0}')
      ..writeln('.missing{font-weight:bold;color:#814337}')
      ..writeln('.footer{margin-top:23px;border-top:1px solid #a0bcb4;padding-top:13px}')
      ..writeln('</style></head><body>')
      ..writeln('<header class="masthead">')
      ..writeln('<h1>${label('Rapport de suivi', 'Follow-up report', 'تقرير متابعة')}</h1>')
      ..writeln('<p class="banner">${label('DONNÉES SYNTHÉTIQUES UNIQUEMENT - NON CLINIQUE', 'SYNTHETIC ONLY - NOT FOR CLINICAL USE', 'بيانات تجريبية فقط - غير صالحة للاستخدام الطبي')}</p>')
      ..writeln('<p>${label('Exemple fictif pour validation technique', 'Fictitious example for technical verification', 'مثال افتراضي للتحقق التقني')}</p>')
      ..writeln('</header>')
      ..writeln('<section class="facts">')
      ..writeln('<p class="label">${label('Période (UTC)', 'Period (UTC)', 'الفترة الزمنية (UTC)')}</p>')
      ..writeln('<p class="date ltr" dir="ltr">${report.periodStartUtc.toIso8601String()} / ${report.periodEndUtc.toIso8601String()}</p>')
      ..writeln('<p class="label">${label('Généré à (UTC)', 'Generated at (UTC)', 'تاريخ الإنشاء (UTC)')}</p>')
      ..writeln('<p class="date ltr" dir="ltr">${report.generatedAtUtc.toIso8601String()}</p>')
      ..writeln('</section>')
      ..writeln('<h2>${label('Mesures manuelles synthétiques', 'Synthetic manual readings', 'قياسات يدوية تجريبية')}</h2>')
      ..writeln('<table><thead><tr>')
      ..writeln('<th>${label('Date UTC', 'UTC date', 'التاريخ UTC')}</th>')
      ..writeln('<th>${label('Valeur', 'Value', 'القيمة')}</th>')
      ..writeln('<th>${label('Source', 'Source', 'المصدر')}</th>')
      ..writeln('</tr></thead><tbody>');

    for (final row in report.observations) {
      html
        ..writeln('<tr>')
        ..writeln('<td class="ltr" dir="ltr">${row.recordedAtUtc.toIso8601String()}</td>')
        ..writeln(row.mgDl == null
            ? '<td class="ltr missing" dir="ltr">N/A</td>'
            : '<td class="ltr" dir="ltr">${row.mgDl} mg/dL</td>')
        ..writeln('<td>${label('Manuel / synthétique', 'Manual / synthetic', 'يدوي / تجريبي')}</td>')
        ..writeln('</tr>');
    }
    html
      ..writeln('</tbody></table>')
      ..writeln('<section class="footer">')
      ..writeln('<p>${label('N/A = mesure absente. Aucun calcul, cible ou diagnostic clinique.', 'N/A = missing reading. No clinical calculation, target or diagnosis.', 'N/A = قياس غير متوفر. لا توجد حسابات أو أهداف أو تشخيصات طبية.')}</p>')
      ..writeln('</section>')
      ..writeln('</body></html>');
    return html.toString();
  }
}
