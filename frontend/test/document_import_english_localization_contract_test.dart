import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Document Import does not embed French production copy', () {
    final source = File(
      'lib/features/documents/document_import_screen.dart',
    ).readAsStringSync();

    const forbidden = <String>[
      'Impossible de lire le fichier',
      'Le serveur n’a pas pu analyser',
      'La confirmation a échoué',
      'Document analysé',
      'Glycémies',
      'Bilan biologique',
      'Médicaments',
      'Observations cliniques',
      'Confirmer l’import',
      'Document importé',
      'Glycémies importées',
      'Doublons ignorés',
      'Retour au tableau de bord',
      'Importer un autre document',
      'Analyse du document en cours',
      'Confiance:',
      'Vérifiez les données ci-dessous',
      'autres mesures',
      'Glucose à jeun',
      'Cholestérol total',
      'Triglycérides',
      'Créatinine',
      'Date du bilan',
      'Aucune donnée médicale détectée',
    ];

    for (final literal in forbidden) {
      expect(source, isNot(contains(literal)), reason: 'Hardcoded locale copy: $literal');
    }
  });

  test('Document Import supplemental copy has explicit EN FR AR parity', () {
    final copy = File(
      'lib/core/localization/document_import_localized_copy.dart',
    ).readAsStringSync();
    expect(copy, contains("'ar' => ar"));
    expect(copy, contains("'fr' => fr"));
    expect(copy, contains('_ => en'));
  });
}
