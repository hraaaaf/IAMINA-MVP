import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String read(String path) => File(path).readAsStringSync();

void main() {
  test('audited pages expose explicit FR EN AR product copy', () {
    final adapter = read('lib/l10n/audited_page_copy.dart');
    final arabic = read('lib/l10n/app_ar.arb');
    final english = read('lib/l10n/app_en.arb');
    final french = read('lib/l10n/app_fr.arb');

    expect(adapter, contains('AppLocalizations.of(context)'));
    expect(adapter, isNot(contains('String pick(')));

    for (final required in <String>[
      'نظرة عامة',
      'البيانات محدّثة',
      'آخر قياس',
      'القياسات ضمن النطاق',
      'اربط مصادر بياناتك',
      'اتصالات مباشرة',
      'غير متاح',
      'استيراد مستند',
      'الملف مكتمل',
      'اكتمل الملف بنسبة',
      'أكمل ملفك للحصول على تحليلات أدق.',
    ]) {
      expect(
        arabic,
        contains(required),
        reason: 'Missing audited Arabic copy: $required',
      );
    }

    for (final catalog in <String>[english, french]) {
      expect(catalog, contains('"overview"'));
      expect(catalog, contains('"unavailable"'));
      expect(catalog, contains('"profileCompletionPrompt"'));
    }
  });

  test('dashboard audited surfaces consume localized copy', () {
    final sources = <String>[
      read('lib/features/dashboard/widgets/top_bar.dart'),
      read('lib/features/dashboard/widgets/hero_section.dart'),
      read('lib/features/dashboard/widgets/hero_live.dart'),
      read('lib/features/dashboard/widgets/hero_tir.dart'),
      read('lib/features/dashboard/widgets/kpi_tir_card.dart'),
    ].join('\n');

    expect(sources, contains('AuditedPageCopy.of(context)'));
    for (final forbidden in <String>[
      "detailed ? 'Accueil · Vue d\\'ensemble'",
      "? 'Bonjour'",
      "const _HeroBadge(label: 'DERNIÈRE MESURE')",
      "CardHead(title: 'Mesures dans la cible'",
    ]) {
      expect(
        sources,
        isNot(contains(forbidden)),
        reason: 'Hardcoded audited dashboard copy remains: $forbidden',
      );
    }
  });

  test('import and profile audited surfaces consume localized copy', () {
    final importer = read('lib/features/import/import_screen.dart');
    final document = read('lib/features/documents/document_import_screen.dart');
    final profile = read('lib/features/profile/profile_screen.dart');
    final combined = '$importer\n$document\n$profile';

    for (final source in <String>[importer, document, profile]) {
      expect(source, contains('audited_page_copy.dart'));
      expect(source, contains('AuditedPageCopy.of(context)'));
    }

    for (final forbidden in <String>[
      "'Non disponible'",
      "label: const Text('Choisir un document')",
      "_buildTextField('Min'",
      "_buildTextField('Max'",
      "'Profil complet ✓'",
      "'Profil complété à",
      'Complétez votre profil pour des analyses plus précises.',
    ]) {
      expect(
        combined,
        isNot(contains(forbidden)),
        reason: 'Hardcoded audited page copy remains: $forbidden',
      );
    }
  });
}
