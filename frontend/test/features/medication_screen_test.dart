import 'package:amina/data/drift/database.dart';
import 'package:amina/features/medications/medication_screen.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

Widget _screen(AppDatabase db, {Locale locale = const Locale('fr')}) {
  return MaterialApp(
    locale: locale,
    home: Provider<AppDatabase>.value(
      value: db,
      child: const MedicationScreen(),
    ),
  );
}

void _narrow(WidgetTester tester) {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
}

void main() {
  late AppDatabase db;

  setUp(() => db = _openDb());
  tearDown(() async => db.close());

  testWidgets('starts with save disabled until a treatment name is entered', (
    tester,
  ) async {
    _narrow(tester);
    await tester.pumpWidget(_screen(db));
    await tester.pumpAndSettle();

    expect(
      tester
          .widget<FilledButton>(find.byKey(const Key('save-medication-event')))
          .onPressed,
      isNull,
    );

    await tester.enterText(
      find.byKey(const Key('medication-name-input')),
      'Insuline rapide',
    );
    await tester.pump();

    expect(
      tester
          .widget<FilledButton>(find.byKey(const Key('save-medication-event')))
          .onPressed,
      isNotNull,
    );
  });

  testWidgets('rejects an invalid or non-positive entered dose', (tester) async {
    _narrow(tester);
    await tester.pumpWidget(_screen(db));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('medication-name-input')),
      'Insuline rapide',
    );
    await tester.enterText(
      find.byKey(const Key('medication-dose-input')),
      '-2',
    );
    await tester.tap(find.byKey(const Key('save-medication-event')));
    await tester.pump();

    expect(find.text('Saisissez une dose positive valide.'), findsOneWidget);
    expect(await db.watchMedicationEvents().first, isEmpty);
  });

  testWidgets('rejects an orphan unit when no dose was entered', (tester) async {
    _narrow(tester);
    await tester.pumpWidget(_screen(db));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('medication-name-input')),
      'Metformine',
    );
    await tester.enterText(find.byKey(const Key('medication-unit-input')), 'mg');
    await tester.tap(find.byKey(const Key('save-medication-event')));
    await tester.pump();

    expect(find.text('Ajoutez la dose ou effacez l’unité.'), findsOneWidget);
    expect(await db.watchMedicationEvents().first, isEmpty);
  });

  testWidgets('persists a factual decimal dose without recommending one', (
    tester,
  ) async {
    _narrow(tester);
    await tester.pumpWidget(_screen(db));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('medication-name-input')),
      'Insuline rapide',
    );
    await tester.enterText(find.byKey(const Key('medication-dose-input')), '4,5');
    await tester.enterText(find.byKey(const Key('medication-unit-input')), 'U');
    await tester.tap(find.byKey(const Key('save-medication-event')));
    await tester.pumpAndSettle();

    final items = await db.watchMedicationEvents().first;
    expect(items, hasLength(1));
    expect(items.single.label, 'Insuline rapide');
    expect(items.single.dose, 4.5);
    expect(items.single.unit, 'U');
    expect(find.text('IAmina ne recommande ni médicament ni dose.'), findsOneWidget);
  });

  testWidgets('requires confirmation before deleting a recorded intake', (
    tester,
  ) async {
    _narrow(tester);
    final id = await db.addMedicationEvent(
      label: 'Metformine',
      dose: 500,
      unit: 'mg',
      takenAt: DateTime(2026, 8, 15, 8),
    );

    await tester.pumpWidget(_screen(db));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(Key('delete-medication-event-$id')));
    await tester.pumpAndSettle();

    expect(find.text('Supprimer cette prise ?'), findsOneWidget);
    expect(await db.watchMedicationEvents().first, hasLength(1));

    await tester.tap(find.text('Annuler'));
    await tester.pumpAndSettle();
    expect(await db.watchMedicationEvents().first, hasLength(1));

    await tester.tap(find.byKey(Key('delete-medication-event-$id')));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Supprimer'));
    await tester.pumpAndSettle();

    expect(await db.watchMedicationEvents().first, isEmpty);
  });
}
