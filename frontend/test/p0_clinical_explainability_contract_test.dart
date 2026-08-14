import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();
Map<String, dynamic> _arb(String locale) =>
    jsonDecode(_read('lib/l10n/app_$locale.arb')) as Map<String, dynamic>;

void main() {
  test(
    'summary exposes coverage and never fabricates confidence or trends',
    () {
      final source = _read('lib/features/journal/ai_summary_screen.dart');
      final localizedCopy =
          _read('lib/core/localization/ai_summary_localized_copy.dart');

      for (final required in <String>[
        'kpis.logCount',
        'kpis.daysWithData',
        'l10n.coverageDisclosure',
        'l10n.automaticObservation',
        'l10n.gmiBasis',
        'constraints.maxWidth < 720',
      ]) {
        expect(
          source,
          contains(required),
          reason: 'Missing explainability contract: $required',
        );
      }

      for (final required in <String>[
        'Repères généraux non personnalisés',
        'Observation automatique',
        'estimation, pas HbA1c laboratoire',
        'Les données manquantes peuvent modifier l’interprétation',
      ]) {
        expect(
          localizedCopy,
          contains(required),
          reason: 'Missing localized explainability wording: $required',
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
    },
  );

  test('all target-range surfaces use the localized truthful contract', () {
    final frenchArb = _read('lib/l10n/app_fr.arb');
    final adapter = _read('lib/l10n/audited_page_copy.dart');
    final sources = <String, String>{
      'KPI card': _read('lib/features/dashboard/widgets/kpi_tir_card.dart'),
      'contextual hero': _read('lib/features/dashboard/widgets/hero_tir.dart'),
    };

    for (final required in <String>[
      'Mesures dans la cible',
      'proportion des mesures enregistrées, pas temps dans la cible d’un capteur de glucose en continu (CGM)',
      'votre cible personnelle peut être différente',
      '{count} mesures sur {days} jours',
    ]) {
      expect(
        frenchArb,
        contains(required),
        reason: 'Canonical localized truthfulness contract is missing: $required',
      );
    }
    expect(adapter, contains('l10n.targetCoverage(count, days)'));
    expect(adapter, contains('l10n.readingsInRange'));

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

  test('GMI fails closed without verified CGM coverage and keeps disclosure', () {
    final source = _read('lib/features/dashboard/widgets/kpi_gmi_card.dart');
    final compactSource = _read('lib/features/dashboard/widgets/kpi_cards.dart');
    final fr = _arb('fr');
    final en = _arb('en');
    final ar = _arb('ar');

    for (final key in <String>[
      'dashboardGmiCoverage',
      'dashboardInsufficientData',
      'dashboardGmiDisclaimer',
    ]) {
      expect(
        source,
        contains('l10n.$key'),
        reason: 'Fail-closed GMI must consume localized key $key',
      );
    }

    expect(source, contains("'--'"));
    expect(source, isNot(contains('ClinicalEngine.calcGMI')));
    expect(source, isNot(contains('l10n.dashboardGmiLimitedCoverage')));
    expect(source, isNot(contains('l10n.dashboardGmiCalculated')));

    expect(compactSource, contains("value: '--'"));
    expect(compactSource, contains('l10n.dashboardInsufficientData'));
    expect(compactSource, isNot(contains('ClinicalEngine.calcGMI')));
    expect(compactSource, isNot(contains('l10n.dashboardGmiLimitedCoverage')));

    expect(fr['dashboardGmiCoverage'], contains('Moyenne'));
    expect(fr['dashboardGmiDisclaimer'], contains('ne remplace pas une HbA1c de laboratoire'));
    expect(en['dashboardGmiCoverage'], contains('Average'));
    expect(en['dashboardGmiDisclaimer'], contains('does not replace a laboratory HbA1c'));
    expect(ar['dashboardGmiCoverage'], contains('المتوسط'));
    expect(ar['dashboardGmiDisclaimer'], contains('لا يغني هذا التقدير عن فحص HbA1c المخبري'));

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

  test('CV remains descriptive without verified sensor coverage', () {
    final source = _read('lib/features/dashboard/widgets/kpi_cv_card.dart');

    expect(source, contains('ClinicalEngine.calcCV'));
    expect(source, contains('l10n.dashboardCvTitle'));
    expect(source, contains('l10n.dashboardMeasurementCoverage'));

    for (final forbidden in <String>[
      'l10n.dashboardCvReferenceShort',
      'l10n.dashboardCvBelowReference',
      'l10n.dashboardCvAboveReference',
      'l10n.dashboardCvReferenceExplanation',
      'Variabilité maîtrisée',
      'Objectif <36% atteint',
      "'Stable'",
      'Cible recommandée',
    ]) {
      expect(
        source,
        isNot(contains(forbidden)),
        reason: 'CV must stay descriptive without verified CGM coverage: $forbidden',
      );
    }
  });
}
