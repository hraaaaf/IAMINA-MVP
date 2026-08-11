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

  test('GMI always discloses method, coverage and laboratory limitation', () {
    final source = _read('lib/features/dashboard/widgets/kpi_gmi_card.dart');
    final fr = _arb('fr');
    final en = _arb('en');
    final ar = _arb('ar');

    for (final key in <String>[
      'dashboardGmiCoverage',
      'dashboardGmiLimitedCoverage',
      'dashboardGmiCalculated',
      'dashboardGmiDisclaimer',
    ]) {
      expect(
        source,
        contains('l10n.$key'),
        reason: 'GMI must consume localized explainability key $key',
      );
    }

    expect(fr['dashboardGmiCoverage'], contains('Moyenne'));
    expect(fr['dashboardGmiLimitedCoverage'], contains('moins de 14 jours ou 50 mesures'));
    expect(fr['dashboardGmiDisclaimer'], contains('ne remplace pas une HbA1c de laboratoire'));

    expect(en['dashboardGmiCoverage'], contains('Average'));
    expect(en['dashboardGmiLimitedCoverage'], contains('fewer than 14 days or 50 readings'));
    expect(en['dashboardGmiDisclaimer'], contains('does not replace a laboratory HbA1c'));

    expect(ar['dashboardGmiCoverage'], contains('المتوسط'));
    expect(ar['dashboardGmiLimitedCoverage'], contains('أقل من 14 يومًا أو 50 قياسًا'));
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

  test('CV is a general reference, never a personalized success claim', () {
    final source = _read('lib/features/dashboard/widgets/kpi_cv_card.dart');
    final fr = _arb('fr');
    final en = _arb('en');
    final ar = _arb('ar');

    for (final key in <String>[
      'dashboardCvReferenceShort',
      'dashboardCvBelowReference',
      'dashboardCvAboveReference',
      'dashboardCvReferenceExplanation',
    ]) {
      expect(
        source,
        contains('l10n.$key'),
        reason: 'CV must consume localized reference key $key',
      );
    }

    expect(fr['dashboardCvReferenceShort'], contains('Repère général <36 %'));
    expect(fr['dashboardCvBelowReference'], contains('Sous le repère général'));
    expect(fr['dashboardCvAboveReference'], contains('Au-dessus du repère général'));
    expect(fr['dashboardCvReferenceExplanation'], contains('Votre objectif personnel peut être différent'));

    expect(en['dashboardCvReferenceShort'], contains('General reference <36%'));
    expect(en['dashboardCvBelowReference'], contains('Below the general reference'));
    expect(en['dashboardCvAboveReference'], contains('Above the general reference'));
    expect(en['dashboardCvReferenceExplanation'], contains('Your personal target may differ'));

    expect(ar['dashboardCvReferenceShort'], contains('مرجع عام <36٪'));
    expect(ar['dashboardCvBelowReference'], contains('أقل من المرجع العام'));
    expect(ar['dashboardCvAboveReference'], contains('أعلى من المرجع العام'));
    expect(ar['dashboardCvReferenceExplanation'], contains('قد يختلف هدفك الشخصي'));

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
