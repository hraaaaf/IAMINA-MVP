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

  group('Add Log focused glucose journal', () {
    test('keeps hypoglycemia safety boundaries deterministic', () {
      expect(classifyGlucoseEntrySafety(53), GlucoseEntrySafety.level2Low);
      expect(classifyGlucoseEntrySafety(54), GlucoseEntrySafety.level1Low);
      expect(classifyGlucoseEntrySafety(69), GlucoseEntrySafety.level1Low);
      expect(classifyGlucoseEntrySafety(70), GlucoseEntrySafety.nonLow);
    });

    testWidgets('starts blank with save disabled and no inferred context', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      final glucose = tester.widget<TextField>(
        find.byKey(const Key('glucose-input')),
      );
      expect(glucose.controller?.text, isEmpty);
      expect(
        find.text('Aucune valeur n’est supposée avant ta saisie.'),
        findsOneWidget,
      );
      expect(
        tester
            .widget<ChoiceChip>(
              find.byKey(const Key('glycemic-context-fasting')),
            )
            .selected,
        isFalse,
      );
      expect(
        tester.widget<FilledButton>(find.byKey(const Key('save-log-button'))).onPressed,
        isNull,
      );
    });

    testWidgets('enables save only after a valid glucose value', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.pump();

      expect(
        tester.widget<FilledButton>(find.byKey(const Key('save-log-button'))).onPressed,
        isNotNull,
      );
    });

    testWidgets('keeps meal and measurement context separate and optional', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.text('CONTEXTE DE LA MESURE'), findsOneWidget);
      expect(find.byKey(const Key('add-meal-button')), findsOneWidget);
      expect(find.byKey(const Key('meal-section')), findsNothing);

      await tester.tap(find.byKey(const Key('add-meal-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('meal-section')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-breakfast')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-lunch')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-dinner')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-snack')), findsOneWidget);
    });

    testWidgets('mobile hides rare details and never exposes insulin intake', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-details-button')), findsOneWidget);
      expect(find.byKey(const Key('journal-details-card')), findsNothing);
      expect(find.byKey(const Key('insulin-taken-input')), findsNothing);
      expect(find.textContaining('insuline prise', findRichText: true), findsNothing);

      await tester.tap(find.byKey(const Key('journal-details-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-details-card')), findsOneWidget);
      expect(find.byKey(const Key('insulin-taken-input')), findsNothing);
      expect(find.byKey(const Key('journal-context-button')), findsOneWidget);
    });

    testWidgets('desktop keeps primary event and optional context side by side', (
      tester,
    ) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-details-button')), findsNothing);
      expect(find.byKey(const Key('journal-details-card')), findsOneWidget);
      expect(find.byKey(const Key('glucose-input')), findsOneWidget);
      expect(find.byKey(const Key('add-meal-button')), findsOneWidget);
      expect(find.byKey(const Key('insulin-taken-input')), findsNothing);
    });

    testWidgets('persists glucose context and meal with insulin always null', (
      tester,
    ) async {
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
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.bloodSugar, 126);
      expect(logs.single.glycemicContext, 'pre_meal');
      expect(logs.single.mealType, 'lunch');
      expect(logs.single.mealDescription, 'Salade et pain');
      expect(logs.single.insulinUnits, isNull);
    });

    testWidgets('additional context remains factual and optional', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.pump();
      await tester.tap(find.byKey(const Key('journal-details-button')));
      await tester.pumpAndSettle();
      final contextButton = find.byKey(const Key('journal-context-button'));
      await tester.ensureVisible(contextButton);
      await tester.pumpAndSettle();
      await tester.tap(contextButton);
      await tester.pumpAndSettle();
      final stressChip = find.byKey(const Key('context-stress'));
      await tester.ensureVisible(stressChip);
      await tester.pumpAndSettle();
      await tester.tap(stressChip);
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final logs = await db.select(db.logEntries).get();
      expect(logs.single.isStressed, isTrue);
      expect(logs.single.insulinUnits, isNull);
    });

    testWidgets('Arabic remains real localized RTL content', (tester) async {
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

    testWidgets('does not expose fabricated nutrition or treatment judgement', (
      tester,
    ) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.textContaining('IG 35'), findsNothing);
      expect(find.textContaining('Dose standard'), findsNothing);
      expect(find.textContaining('Dose critique'), findsNothing);
      expect(find.textContaining('Analyse IAmina'), findsNothing);
      expect(find.byKey(const Key('insulin-taken-input')), findsNothing);
    });
  });

  group('Add Log post-save receipt', () {
    testWidgets('successful save shows factual receipt and resets next draft', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.tap(find.byKey(const Key('glycemic-context-post_meal')));
      await tester.tap(find.byKey(const Key('add-meal-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('meal-type-lunch')));
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.insulinUnits, isNull);

      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
      expect(find.text('Enregistrée sur cet appareil.'), findsOneWidget);
      expect(find.textContaining('126 mg/dL'), findsOneWidget);
      expect(find.textContaining('Après repas'), findsOneWidget);
      expect(find.textContaining('Déjeuner'), findsOneWidget);
      expect(find.textContaining(' U'), findsNothing);
      expect(
        find.textContaining('n’interprète pas la mesure'),
        findsOneWidget,
      );

      final addAnother = find.byKey(const Key('post-save-add-another'));
      await tester.ensureVisible(addAnother);
      await tester.pumpAndSettle();
      await tester.tap(addAnother);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-receipt')), findsNothing);
      final glucose = tester.widget<TextField>(
        find.byKey(const Key('glucose-input')),
      );
      expect(glucose.controller?.text, isEmpty);
      expect(find.byKey(const Key('meal-section')), findsNothing);
      expect(find.byKey(const Key('journal-details-card')), findsNothing);
    });

    testWidgets('Arabic receipt is localized RTL and factual', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db, locale: const Locale('ar')));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.pump();
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
      expect(find.text('تم الحفظ على هذا الجهاز.'), findsOneWidget);
      expect(find.text('عرض في السجل'), findsOneWidget);
      expect(find.text('إضافة قياس آخر'), findsOneWidget);
      expect(
        Directionality.of(
          tester.element(find.text('تم الحفظ على هذا الجهاز.')),
        ),
        TextDirection.rtl,
      );
      expect(tester.takeException(), isNull);
    });
  });
}
