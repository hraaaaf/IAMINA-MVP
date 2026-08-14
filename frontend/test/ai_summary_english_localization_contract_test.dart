import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('AI summary static shell follows the active locale', () {
    final source = _read('lib/features/journal/ai_summary_screen.dart');
    final copy = _read('lib/core/localization/ai_summary_localized_copy.dart');

    expect(source, contains('ai_summary_localized_copy.dart'));
    for (final getter in <String>[
      '.keyEvents',
      '.mostlyInTarget',
      '.readingsInRange',
      '.ambulatoryGlucoseProfile',
      '.discussionPoints',
      '.automaticObservation',
      '.chatCtaBody',
    ]) {
      expect(source, contains(getter), reason: 'Missing localized shell copy: $getter');
    }

    for (final frenchLiteral in <String>[
      'ÉVÉNEMENTS CLÉS',
      'Aucune découverte pour le moment.',
      'Voir mes découvertes',
      'MESURES DANS LA CIBLE',
      'PROFIL GLYCÉMIQUE AMBULATOIRE',
      'POINTS À DISCUTER',
      'Observation automatique',
      'Demander pourquoi',
      'Posez vos questions ou demandez une explication des données disponibles.',
    ]) {
      expect(source, isNot(contains("'$frenchLiteral'")),
          reason: 'Static French must not remain embedded in the screen: $frenchLiteral');
    }

    for (final localeMarker in <String>["en: '", "fr: '", "ar: '"]) {
      expect(copy, contains(localeMarker));
    }
  });

  test('server-provided clinical insight content stays verbatim', () {
    final source = _read('lib/features/journal/ai_summary_screen.dart');

    expect(source, contains('card.title'));
    expect(source, contains('card.body'));
    expect(source, contains('card.action'));
    expect(source, isNot(contains('translate(card.title')));
    expect(source, isNot(contains('translate(card.body')));
    expect(source, isNot(contains('translate(card.action')));
  });
}
