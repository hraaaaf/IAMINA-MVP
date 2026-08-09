import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

Widget _sheet(AppDatabase db, {Locale locale = const Locale('fr')}) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      body: MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          Provider<PatientProfileData?>.value(value: null),
        ],
        child: const AddLogSheet(),
      ),
    ),
  );
}

void _narrow(WidgetTester tester) {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
}

void _wide(WidgetTester tester) {
  tester.view.physicalSize = const Size(1440, 1000);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
}

void main() {
  late AppDatabase db;

  setUp(() => db = _openDb());
  tearDown(() async => db.close());

  group('P0-JOURNAL-2 express metabolic event', () {
    test('keeps hypoglycemia safety boundaries deterministic', () {
      expect(classifyGlucoseEntrySafety(53), GlucoseEntrySafety.level2Low);
      expect(classifyGlucoseEntrySafety(54), GlucoseEntrySafety.level1Low);
      expect(classifyGlucoseEntrySafety(69), GlucoseEntrySafety.level1Low);
      expect(classifyGlucoseEntrySafety(70), GlucoseEntrySafety.nonLow);
    });

    testWidgets('starts blank and does not assume a measurement context',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      final glucose = tester.widget<TextField>(
        find.byKey(const Key('glucose-input')),
      );
      expect(glucose.controller?.text, isEmpty);
      expect(find.text('Aucune valeur n’est supposée avant ta saisie.'),
          findsOneWidget);
      expect(find.byKey(const Key('glycemic-context-fasting')), findsOneWidget);
      expect(
        tester.widget<ChoiceChip>(
          find.byKey(const Key('glycemic-context-fasting')),
        ).selected,
        isFalse,
      );
    });

    testWidgets('separates measurement context from optional meal taxonomy',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.text('CONTEXTE DE LA MESURE'), findsOneWidget);
      expect(find.byKey(const Key('add-meal-button')), findsOneWidget);
      expect(find.text('Sport'), findsNothing);
      expect(find.byKey(const Key('meal-section')), findsNothing);

      await tester.tap(find.byKey(const Key('add-meal-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('meal-section')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-breakfast')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-lunch')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-dinner')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-snack')), findsOneWidget);
      expect(find.text('Sport'), findsNothing);
    });

    testWidgets('mobile keeps secondary details out of the primary path',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-details-button')), findsOneWidget);
      expect(find.byKey(const Key('journal-details-card')), findsNothing);
      expect(find.byKey(const Key('insulin-taken-input')), findsNothing);

      await tester.tap(find.byKey(const Key('journal-details-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-details-card')), findsOneWidget);
      expect(find.byKey(const Key('insulin-taken-input')), findsOneWidget);
    });

    testWidgets('desktop composes primary event and optional details side by side',
        (tester) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-details-button')), findsNothing);
      expect(find.byKey(const Key('journal-details-card')), findsOneWidget);
      expect(find.byKey(const Key('glucose-input')), findsOneWidget);
      expect(find.byKey(const Key('add-meal-button')), findsOneWidget);
    });

    testWidgets('persists context and meal independently with no insulin default',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.tap(find.byKey(const Key('glycemic-context-pre_meal')));
      await tester.tap(find.byKey(const Key('add-meal-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('meal-type-lunch')));
      await tester.enterText(
        find.byKey(const Key('meal-note-input')),
        'Salade et pain',
      );
      await tester.tap(find.text('Enregistrer la mesure'));
      await tester.pumpAndSettle();

      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.bloodSugar, 126);
      expect(logs.single.glycemicContext, 'pre_meal');
      expect(logs.single.mealType, 'lunch');
      expect(logs.single.mealDescription, 'Salade et pain');
      expect(logs.single.insulinUnits, isNull);
    });

    testWidgets('Arabic is real localized RTL content, not mirrored French',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db, locale: const Locale('ar')));
      await tester.pumpAndSettle();

      expect(find.text('قياس جديد'), findsOneWidget);
      expect(find.text('سياق القياس'), findsOneWidget);
      expect(find.text('إضافة وجبة · اختياري'), findsOneWidget);
      expect(find.text('Nouvelle mesure'), findsNothing);
      expect(
        Directionality.of(tester.element(find.text('قياس جديد'))),
        TextDirection.rtl,
      );
    });

    testWidgets('does not expose fabricated nutrition or dose judgement',
        (tester) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.textContaining('IG 35'), findsNothing);
      expect(find.textContaining('g glucides'), findsNothing);
      expect(find.textContaining('Impact'), findsNothing);
      expect(find.textContaining('Dose standard'), findsNothing);
      expect(find.textContaining('Dose critique'), findsNothing);
      expect(find.textContaining('Analyse IAmina'), findsNothing);
    });
  });
}
