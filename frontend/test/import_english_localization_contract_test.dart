import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Import production status copy follows the active locale', () {
    final source = File('lib/features/import/import_screen.dart').readAsStringSync();

    const forbidden = <String>[
      "à l'instant",
      'Données expirées',
      'Dernière mesure',
      'Stockage local',
      'Données stockées sur cet appareil',
      'Données démo — 21 jours',
      'Charger un jeu de données cliniques réalistes',
      'Chargé',
      'Charger',
    ];
    for (final literal in forbidden) {
      expect(source, isNot(contains(literal)), reason: 'Hardcoded locale copy: $literal');
    }

    expect(source, contains('AppLocalizations.of(context)!'));
    expect(source, contains('l10n.readingsRecorded(totalLogs)'));
    expect(source, contains('l10n.latestReadingStoredLocally(label)'));
    expect(source, contains('l10n.storedOnDevice'));
  });

  test('Import supplemental copy keeps explicit EN FR AR parity', () {
    final copy = File('lib/core/localization/import_localized_copy.dart').readAsStringSync();
    expect(copy, contains("'ar' => ar"));
    expect(copy, contains("'fr' => fr"));
    expect(copy, contains('_ => en'));
  });
}
