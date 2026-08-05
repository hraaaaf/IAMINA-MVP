#!/usr/bin/env python3
"""Write parser-safe permanent contracts after the scoped localization migration."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]

localization_test = r'''import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String read(String path) => File(path).readAsStringSync();

void main() {
  test('audited pages expose explicit FR EN AR product copy', () {
    final copy = read('lib/l10n/audited_page_copy.dart');
    for (final required in <String>[
      "'ar' => ar",
      'نظرة عامة',
      'البيانات محدّثة',
      'آخر قياس',
      'القياسات ضمن النطاق',
      'اربط مصادر بياناتك',
      'اتصالات مباشرة',
      'غير متاح',
      'استيراد مستند',
      'الملف مكتمل',
    ]) {
      expect(
        copy,
        contains(required),
        reason: 'Missing audited Arabic copy: $required',
      );
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
      "'Profil complet'",
    ]) {
      expect(
        combined,
        isNot(contains(forbidden)),
        reason: 'Hardcoded audited page copy remains: $forbidden',
      );
    }
  });
}
'''

clinical_test = r'''import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('summary exposes coverage and never fabricates confidence or trends', () {
    final source = _read('lib/features/journal/ai_summary_screen.dart');

    for (final required in <String>[
      'Repères généraux non personnalisés',
      'kpis.logCount',
      'kpis.daysWithData',
      'Observation automatique',
      'estimation, pas HbA1c laboratoire',
      'constraints.maxWidth < 720',
      'Les données manquantes peuvent modifier l’interprétation',
    ]) {
      expect(
        source,
        contains(required),
        reason: 'Missing explainability contract: $required',
      );
    }

    for (final forbidden in <String>[
      '_confidenceForSeverity',
      'conf. ',
      'class _SignalBars',
      'Icons.arrow_upward',
      'Icons.arrow_downward',
      'confidenceBadge',
      'required this.trend',
      'conseils personnalisés',
      'Cible 70–180',
      '/100',
    ]) {
      expect(
        source,
        isNot(contains(forbidden)),
        reason: 'Fabricated precision remains: $forbidden',
      );
    }
  });

  test('all target-range surfaces use the localized truthful contract', () {
    final copy = _read('lib/l10n/audited_page_copy.dart');
    final sources = <String, String>{
      'KPI card': _read('lib/features/dashboard/widgets/kpi_tir_card.dart'),
      'contextual hero': _read('lib/features/dashboard/widgets/hero_tir.dart'),
    };

    for (final required in <String>[
      'Mesures dans la cible',
      'proportion de mesures, pas durée CGM',
      'votre cible personnelle peut être différente',
      r'$count mesures sur $days jour',
    ]) {
      expect(
        copy,
        contains(required),
        reason: 'Localized truthfulness contract is missing: $required',
      );
    }

    for (final entry in sources.entries) {
      final source = entry.value;
      expect(
        source,
        contains('AuditedPageCopy.of(context)'),
        reason: '${entry.key} must use the localized truthfulness source',
      );
      expect(
        source,
        contains('copy.targetCoverage'),
        reason: '${entry.key} must expose measurement coverage',
      );

      for (final forbidden in <String>[
        'Temps en cible',
        'TEMPS EN CIBLE',
        'Objectif ADA',
        'Objectif ≥',
        'Atteint',
      ]) {
        expect(
          source,
          isNot(contains(forbidden)),
          reason: '${entry.key} retains misleading wording: $forbidden',
        );
      }
    }
  });

  test('GMI always discloses method, coverage and laboratory limitation', () {
    final source = _read('lib/features/dashboard/widgets/kpi_gmi_card.dart');

    expect(source, contains('Moyenne'));
    expect(source, contains(r'${logs.length} mesures'));
    expect(source, contains('Couverture limitée'));
    expect(source, contains('moins de 14 jours ou 50 mesures'));
    expect(source, contains('ne remplace pas une HbA1c de laboratoire'));

    for (final forbidden in <String>[
      '_confidence',
      'GmiConfidence',
      'Confiance élevée',
      'Confiance moyenne',
      'Confiance faible',
    ]) {
      expect(
        source,
        isNot(contains(forbidden)),
        reason: 'Unsupported GMI confidence: $forbidden',
      );
    }
  });

  test('CV is a general reference, never a personalized success claim', () {
    final source = _read('lib/features/dashboard/widgets/kpi_cv_card.dart');

    expect(source, contains('Repère général <36 %'));
    expect(source, contains('Sous le repère général'));
    expect(source, contains('Au-dessus du repère général'));
    expect(source, contains('Votre objectif personnel peut être différent'));

    for (final forbidden in <String>[
      'Variabilité maîtrisée',
      'Objectif <36% atteint',
      "'Stable'",
      'Cible recommandée',
    ]) {
      expect(
        source,
        isNot(contains(forbidden)),
        reason: 'Personalized CV claim remains: $forbidden',
      );
    }
  });
}
'''

(root / 'frontend/test/p0_audited_page_localization_contract_test.dart').write_text(
    localization_test,
    encoding='utf-8',
)
(root / 'frontend/test/p0_clinical_explainability_contract_test.dart').write_text(
    clinical_test,
    encoding='utf-8',
)
print('Parser-safe audited localization and clinical contracts written.')
