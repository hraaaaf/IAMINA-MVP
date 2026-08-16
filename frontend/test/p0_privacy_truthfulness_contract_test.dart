import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _arb(String path) =>
    jsonDecode(File(path).readAsStringSync()) as Map<String, dynamic>;

String _read(String path) => File(path).readAsStringSync();

void main() {
  final localeFiles = <String, String>{
    'fr': 'lib/l10n/app_fr.arb',
    'en': 'lib/l10n/app_en.arb',
    'ar': 'lib/l10n/app_ar.arb',
  };

  test('privacy wording is deployment-aware in every supported locale', () {
    final requiredEvidence = <String, List<String>>{
      'fr': ['fournisseur', 'région', 'conservation', 'Sans consentement'],
      'en': ['provider', 'region', 'retention', 'Without consent'],
      'ar': ['المزوّد', 'المنطقة', 'الاحتفاظ', 'من دون موافقة'],
    };

    for (final entry in localeFiles.entries) {
      final values = _arb(entry.value);
      final combined = <String>[
        values['dataPrivacyNote'] as String,
        values['consentHeadline'] as String,
        values['consentBody'] as String,
        values['documentPrivacyTitle'] as String,
        values['documentPrivacyBody'] as String,
      ].join(' ');

      for (final required in requiredEvidence[entry.key]!) {
        expect(
          combined,
          contains(required),
          reason:
              '${entry.key} is missing deployment evidence wording: $required',
        );
      }

      for (final forbidden in <String>[
        'Gemini',
        'pseudonymised',
        'pseudonymized',
        'pseudonymisées',
        'مجهولة الهوية',
        'never sold',
        'jamais vendues',
        'لا تُباع',
        'zero retention',
        'no retention',
        'never trains',
      ]) {
        expect(
          combined.toLowerCase(),
          isNot(contains(forbidden.toLowerCase())),
          reason:
              '${entry.key} contains an unsupported privacy claim: $forbidden',
        );
      }
    }
  });

  test(
    'document import displays the fail-closed privacy gate before selection',
    () {
      final source = _read(
        'lib/features/documents/document_import_screen.dart',
      );

      for (final required in <String>[
        'document-privacy-gate',
        'l10n.documentPrivacyTitle',
        'l10n.privacyProcessingBody',
        'const _PrivacyGateNotice()',
        "key: const ValueKey('choose-document-button')",
      ]) {
        expect(
          source,
          contains(required),
          reason: 'Document privacy gate is incomplete: $required',
        );
      }

      expect(
        source.indexOf('const _PrivacyGateNotice()'),
        lessThan(
          source.indexOf("key: const ValueKey('choose-document-button')"),
        ),
        reason: 'Privacy notice must be visible before the file chooser.',
      );
    },
  );

  test('generated localization sources contain the approved wording', () {
    final generated = <String, String>{
      'fr': _read('lib/l10n/app_localizations_fr.dart'),
      'en': _read('lib/l10n/app_localizations_en.dart'),
      'ar': _read('lib/l10n/app_localizations_ar.dart'),
    };

    expect(generated['fr'], contains('Envoi externe uniquement si autorisé'));
    expect(generated['en'], contains('External sending only when authorised'));
    expect(generated['ar'], contains('إرسال خارجي فقط عند السماح به'));

    expect(generated['fr'], isNot(contains('Traitement externe contrôlé')));
    expect(generated['en'], isNot(contains('Controlled external processing')));
    expect(generated['ar'], isNot(contains('معالجة خارجية مضبوطة')));

    for (final source in generated.values) {
      expect(source, isNot(contains('Gemini')));
    }
  });
}
