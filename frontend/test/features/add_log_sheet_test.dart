import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/services/api_client.dart';
import '../mocks.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

// ── Helpers ───────────────────────────────────────────────────────────────────

// AddLogSheet uses MediaQuery.size.width >= 720 to pick wide vs narrow layout.
// Default test viewport (800 × 600) always triggers WIDE layout.
// Set this at the start of each narrow-mode test.
void _setNarrow(WidgetTester tester) {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
}

void _setWide(WidgetTester tester) {
  tester.view.physicalSize = const Size(820, 1200);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
}

// AddLogSheet is designed for phone dimensions.  At narrow viewport, certain
// Row widgets have more content than space, producing cosmetic overflow errors.
// Intercept AFTER testWidgets sets its own handler to drop overflow warnings.
void _ignoreOverflow() {
  final handler = FlutterError.onError;
  FlutterError.onError = (FlutterErrorDetails details) {
    if (details.exception.toString().contains('overflowed')) return;
    handler?.call(details);
  };
  addTearDown(() => FlutterError.onError = handler);
}

// ── Widget factory ────────────────────────────────────────────────────────────

Widget makeSheet({required AppDatabase db, MockApiClient? api}) {
  final mockApi = api ?? MockApiClient();
  return MaterialApp(
    home: Scaffold(
      body: MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          Provider<ApiClient>.value(value: mockApi),
          Provider<PatientProfileData?>.value(value: null),
        ],
        child: const AddLogSheet(),
      ),
    ),
  );
}

void main() {
  late AppDatabase db;
  late MockApiClient mockApi;

  setUp(() {
    db = _openDb();
    mockApi = MockApiClient();
  });

  tearDown(() async {
    await db.close();
  });

  // ── Express mode (narrow — default mobile) ────────────────────────────────
  // Layout branch: _buildNarrowLayout() — triggered by MediaQuery width < 720.

  group('Express mode (narrow layout)', () {
    testWidgets('shows glucose card and meal type selector', (tester) async {
      _setNarrow(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.text('Dans la cible'), findsOneWidget);  // glucose range label
      expect(find.text('MOMENT DU REPAS'), findsOneWidget);// meal section label
      expect(find.text('À jeun'),         findsOneWidget); // default pill
    });

    testWidgets('shows "+ Détails" expand button in express mode', (tester) async {
      _setNarrow(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.textContaining('+ Détails'), findsOneWidget);
    });

    testWidgets('insulin and health sections hidden in express mode', (tester) async {
      _setNarrow(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.text("DOSE D'INSULINE"), findsNothing);
      expect(find.text('ÉTAT DU JOUR'),    findsNothing);
    });

    testWidgets('expanding details reveals insulin section', (tester) async {
      _setNarrow(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      await tester.tap(find.textContaining('+ Détails'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 500));

      expect(find.text("DOSE D'INSULINE"), findsOneWidget);
      expect(find.text('ÉTAT DU JOUR'),    findsOneWidget);
    });

    testWidgets('meal type pills are visible', (tester) async {
      _setNarrow(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.text('À jeun'),         findsOneWidget);
      expect(find.text('Petit-déjeuner'), findsOneWidget);
      expect(find.text('Déjeuner'),       findsOneWidget);
      expect(find.text('Dîner'),          findsOneWidget);
    });

    testWidgets('food section hidden when À jeun in express mode', (tester) async {
      _setNarrow(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.text('ALIMENTS'), findsNothing);
    });

    testWidgets('selecting Déjeuner in expanded mode shows food section', (tester) async {
      _setNarrow(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // Expand details first
      await tester.tap(find.textContaining('+ Détails'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 500));

      // Select a meal type that has food
      await tester.tap(find.text('Déjeuner'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('ALIMENTS'), findsOneWidget);
    });
  });

  // ── Wide layout (tablet / desktop — always detailed) ─────────────────────
  // Layout branch: _buildWideLayout() — triggered by MediaQuery width ≥ 720.

  group('Wide layout (≥720px — all sections always visible)', () {
    testWidgets('shows insulin and health sections without expanding', (tester) async {
      _setWide(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.text("DOSE D'INSULINE"),      findsOneWidget);
      expect(find.text('ÉTAT DU JOUR'),         findsOneWidget);
      expect(find.text('Enregistrer la mesure'), findsOneWidget);
    });

    testWidgets('insulin dose stepper is present', (tester) async {
      _setWide(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // Section label + UNITÉS label inside the stepper card
      expect(find.text("DOSE D'INSULINE"), findsOneWidget);
      expect(find.text('UNITÉS'),          findsOneWidget);
    });

    testWidgets('health state toggles render', (tester) async {
      _setWide(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.text('Malade'),  findsOneWidget);
      expect(find.text('Stressé'), findsOneWidget);
      expect(find.text('Actif'),   findsOneWidget);
    });

    testWidgets('switching to Déjeuner shows food section', (tester) async {
      _setWide(tester);
      _ignoreOverflow();
      await tester.pumpWidget(makeSheet(db: db, api: mockApi));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      await tester.tap(find.text('Déjeuner'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('ALIMENTS'), findsOneWidget);
    });
  });
}
