import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

String _source() =>
    File('lib/features/medications/medication_screen.dart').readAsStringSync();

void main() {
  group('Medications factual intake contract', () {
    test('guards medication input without making treatment recommendations', () {
      final source = _source();

      expect(source, contains("parsed == null || !parsed.isFinite || parsed <= 0"));
      expect(source, contains("rawDose.isNotEmpty && parsedDose == null"));
      expect(source, contains("rawUnit.isNotEmpty && rawDose.isEmpty"));
      expect(source, contains("_saving || _name.text.trim().isEmpty"));
      expect(source, contains('IAmina ne recommande ni médicament ni dose.'));
      expect(source, isNot(contains('dose recommandée')));
      expect(source, isNot(contains('recommended dose')));
    });

    test('requires explicit confirmation before deleting a recorded intake', () {
      final source = _source();

      expect(source, contains('showDialog<bool>'));
      expect(source, contains('Supprimer cette prise ?'));
      expect(source, contains('if (confirmed == true) await db.deleteMedicationEvent(id);'));
    });

    test('database preserves a factual decimal dose and unit', () async {
      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);

      await db.addMedicationEvent(
        label: 'Insuline rapide',
        dose: 4.5,
        unit: 'U',
        takenAt: DateTime(2026, 8, 15, 8),
      );

      final items = await db.select(db.medicationEvents).get();
      expect(items, hasLength(1));
      expect(items.single.label, 'Insuline rapide');
      expect(items.single.dose, 4.5);
      expect(items.single.unit, 'U');
    });
  });
}
