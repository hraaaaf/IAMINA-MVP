import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

Widget _sheet(AppDatabase db) {
  return MaterialApp(
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
  tester.view.physicalSize = const Size(900, 1100);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
}

void main() {
  late AppDatabase db;

  setUp(() => db = _openDb());
  tearDown(() async => db.close());

  group('P0-JOURNAL-1 deterministic low-glucose boundaries', () {
    test('53 mg/dL is level 2 low', () {
      expect(
        classifyGlucoseEntrySafety(53),
        GlucoseEntrySafety.level2Low,
      );
    });

    test('54 and 69 mg/dL are level 1 low', () {
      expect(
        classifyGlucoseEntrySafety(54),
        GlucoseEntrySafety.level1Low,
      );
      expect(
        classifyGlucoseEntrySafety(69),
        GlucoseEntrySafety.level1Low,
      );
    });

    test('70 mg/dL is not classified as low', () {
      expect(
        classifyGlucoseEntrySafety(70),
        GlucoseEntrySafety.nonLow,
      );
    });

    test('mmol/L-equivalent boundaries classify after mg/dL normalization', () {
      expect(
        classifyGlucoseEntrySafety(2.9 * 18),
        GlucoseEntrySafety.level2Low,
      );
      expect(
        classifyGlucoseEntrySafety(3.0 * 18),
        GlucoseEntrySafety.level1Low,
      );
      expect(
        classifyGlucoseEntrySafety(3.8 * 18),
        GlucoseEntrySafety.level1Low,
      );
      expect(
        classifyGlucoseEntrySafety(3.9 * 18),
        GlucoseEntrySafety.nonLow,
      );
    });

    testWidgets('53 and 54 render distinct patient safety states',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));

      await tester.enterText(find.byKey(const Key('glucose-input')), '53');
      await tester.pump();
      expect(find.byKey(const Key('level2-low-message')), findsOneWidget);
      expect(find.byKey(const Key('level1-low-message')), findsNothing);

      await tester.enterText(find.byKey(const Key('glucose-input')), '54');
      await tester.pump();
      expect(find.byKey(const Key('level2-low-message')), findsNothing);
      expect(find.byKey(const Key('level1-low-message')), findsOneWidget);
    });
  });

  group('P0-JOURNAL-1 clinical truthfulness', () {
    testWidgets('starts without a fabricated glucose value or target verdict',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pump();

      final glucose = tester.widget<TextField>(
        find.byKey(const Key('glucose-input')),
      );
      expect(glucose.controller?.text, isEmpty);
      expect(find.text('Dans la cible'), findsNothing);
      expect(find.text('Hyperglycémie modérée'), findsNothing);
      expect(
        find.text('Aucune valeur n’est supposée avant ta saisie.'),
        findsOneWidget,
      );
    });

    testWidgets('does not classify a non-low value against a generic target',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.enterText(
        find.byKey(const Key('glucose-input')),
        '180',
      );
      await tester.pump();

      expect(find.text('Dans la cible'), findsNothing);
      expect(
        find.text('La cible personnelle n’est pas déduite de cette valeur seule.'),
        findsOneWidget,
      );
    });

    testWidgets('mobile keeps secondary data behind details', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pump();

      expect(find.textContaining('+ Détails'), findsOneWidget);
      expect(find.text('INSULINE PRISE'), findsNothing);

      await tester.tap(find.textContaining('+ Détails'));
      await tester.pump();

      expect(find.text('INSULINE PRISE'), findsOneWidget);
      expect(find.byKey(const Key('insulin-taken-input')), findsOneWidget);
    });

    testWidgets('insulin is recorded as taken without dose presets or judgement',
        (tester) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pump();

      expect(find.text('INSULINE PRISE'), findsOneWidget);
      expect(find.text('Dose réellement prise'), findsOneWidget);
      expect(find.text('Zone normale'), findsNothing);
      expect(find.text('Dose standard'), findsNothing);
      expect(find.text('Dose élevée'), findsNothing);
      expect(find.text('Dose critique'), findsNothing);
      expect(find.text('2 U'), findsNothing);
      expect(find.text('20 U'), findsNothing);
    });

    testWidgets('food logging exposes no fabricated carbs GI or impact score',
        (tester) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pump();

      await tester.tap(find.text('Déjeuner'));
      await tester.pump();

      expect(find.text('CE QUE TU AS MANGÉ'), findsOneWidget);
      expect(find.textContaining('IG 35'), findsNothing);
      expect(find.textContaining('IG 60'), findsNothing);
      expect(find.textContaining('IG 75'), findsNothing);
      expect(find.textContaining('g glucides'), findsNothing);
      expect(find.text('Impact faible'), findsNothing);
      expect(find.text('Impact modéré'), findsNothing);
      expect(find.text('Impact élevé'), findsNothing);
    });

    testWidgets('no immediate generative-analysis promise is shown',
        (tester) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pump();

      expect(find.textContaining('Que penses-tu de cette mesure'), findsNothing);
      expect(find.textContaining('conseil personnalisé'), findsNothing);
      expect(find.textContaining('Analyse IAmina'), findsNothing);
    });
  });
}
