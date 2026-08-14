import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('AI Summary static shell does not embed French production copy', () {
    final source = File(
      'lib/features/journal/ai_summary_screen.dart',
    ).readAsStringSync();

    const forbidden = <String>[
      'ÉVÉNEMENTS CLÉS',
      'Aucune découverte pour le moment.',
      'Une majorité des mesures disponibles',
      'Certaines mesures disponibles',
      'Voir mes découvertes',
      'Discuter avec IAmina',
      'MESURES DANS LA CIBLE',
      'GMI ESTIMÉE',
      'VARIABILITÉ (CV)',
      'PROFIL GLYCÉMIQUE AMBULATOIRE',
      'Données insuffisantes.',
      'POINTS À DISCUTER',
      'À discuter avec le médecin',
      'Observation automatique',
      'Piste à discuter',
      'Demander pourquoi',
      'Posez vos questions',
      'Démarrer',
    ];

    for (final literal in forbidden) {
      expect(source, isNot(contains(literal)), reason: 'Hardcoded locale copy: $literal');
    }
  });

  test('AI Summary supplemental shell copy keeps explicit EN FR AR parity', () {
    final copy = File(
      'lib/core/localization/ai_summary_localized_copy.dart',
    ).readAsStringSync();

    expect(copy, contains("'ar' => ar"));
    expect(copy, contains("'fr' => fr"));
    expect(copy, contains('_ => en'));
    expect(copy, contains('String get keyEvents'));
    expect(copy, contains('String get readingsInRange'));
    expect(copy, contains('String get discussionPoints'));
    expect(copy, contains('String get automaticObservation'));
  });

  test('server clinical insight content remains verbatim', () {
    final source = File(
      'lib/features/journal/ai_summary_screen.dart',
    ).readAsStringSync();

    expect(source, contains('card.title'));
    expect(source, contains('card.body'));
    expect(source, contains('title: card.action'));
    expect(source, contains('l10n.discussionSuggestion(card.action)'));
  });
}
