import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> arb(String locale) =>
    jsonDecode(File('lib/l10n/app_$locale.arb').readAsStringSync())
        as Map<String, dynamic>;

void main() {
  test('P1-UX-13 puts plain language before CGM and AGP jargon', () {
    final fr = arb('fr');
    final en = arb('en');
    final ar = arb('ar');
    expect(fr['cgmExport'], 'Export de mesure continue du glucose (CGM)');
    expect(en['cgmExport'], 'Continuous glucose monitoring (CGM) export');
    expect(ar['cgmExport'], contains('المراقبة المستمرة للجلوكوز (CGM)'));
    expect(fr['featureRealtimeAgp'], 'Résumé des tendances du capteur (AGP)');
    expect(en['featureRealtimeAgp'], 'Sensor trend summary (AGP)');
    expect(ar['featureRealtimeAgp'], contains('(AGP)'));
    expect(fr['featureRealtimeAgp'], isNot(contains('temps réel')));
    expect(en['featureRealtimeAgp'], isNot(contains('Real-time')));
  });

  test('P1-UX-13 preserves deployment-aware privacy conditions', () {
    final required = <String, List<String>>{
      'fr': ['fournisseur', 'région', 'conservation', 'Sans consentement'],
      'en': ['provider', 'region', 'retention', 'Without consent'],
      'ar': ['المزوّد', 'المنطقة', 'الاحتفاظ', 'من دون موافقة'],
    };
    for (final locale in required.keys) {
      final data = arb(locale);
      final copy = [
        data['dataPrivacyNote'],
        data['consentHeadline'],
        data['consentBody'],
        data['documentPrivacyTitle'],
        data['documentPrivacyBody'],
      ].join(' ');
      for (final token in required[locale]!) expect(copy, contains(token));
    }
    expect(
      arb('fr')['documentPrivacyTitle'],
      'Envoi externe uniquement si autorisé',
    );
  });

  test('P1-UX-13 distinguishes reading coverage from CGM time in range', () {
    final fr = arb('fr')['targetCoverage'].toString();
    final en = arb('en')['targetCoverage'].toString();
    final ar = arb('ar')['targetCoverage'].toString();
    expect(fr, contains('capteur de glucose en continu (CGM)'));
    expect(fr, contains('pas temps dans la cible'));
    expect(en, contains('not time in range'));
    expect(en, contains('continuous glucose monitoring (CGM)'));
    expect(ar, contains('المراقبة المستمرة للجلوكوز (CGM)'));
  });
}
