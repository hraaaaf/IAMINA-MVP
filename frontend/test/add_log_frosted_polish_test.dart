import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/features/journal/add_log_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

Widget _providers(AppDatabase db, Widget child) {
  return MultiProvider(
    providers: [
      Provider<AppDatabase>.value(value: db),
      Provider<PatientProfileData?>.value(value: null),
    ],
    child: child,
  );
}

Widget _sheet(AppDatabase db, {bool isPage = false}) {
  return MaterialApp(
    locale: const Locale('fr'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      body: _providers(db, AddLogSheet(isPage: isPage)),
    ),
  );
}

Widget _screen(AppDatabase db) {
  return MaterialApp(
    locale: const Locale('fr'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: _providers(db, const AddLogScreen()),
  );
}

void _viewport(WidgetTester tester, Size size) {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

void main() {
  late AppDatabase db;

  setUp(() => db = _openDb());
  tearDown(() async => db.close());

  testWidgets('glucose entry uses restrained frosted surfaces and integrated unit', (
    tester,
  ) async {
    _viewport(tester, const Size(390, 844));
    await tester.pumpWidget(_sheet(db));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('glucose-glass-card')), findsOneWidget);
    expect(find.byKey(const Key('save-log-glass-bar')), findsOneWidget);
    expect(find.byType(BackdropFilter), findsNWidgets(2));

    final ambientBackdrop = tester.widget<DecoratedBox>(
      find.byKey(const Key('add-log-ambient-backdrop')),
    );
    final ambientDecoration = ambientBackdrop.decoration as BoxDecoration;
    expect(ambientDecoration.gradient, isA<LinearGradient>());

    final glucose = tester.widget<TextField>(
      find.byKey(const Key('glucose-input')),
    );
    expect(glucose.decoration?.suffixIcon, isNotNull);
    expect(find.byKey(const Key('glucose-unit')), findsOneWidget);
    expect(find.text('mg/dL'), findsOneWidget);
    expect(glucose.style?.fontSize, 44);

    final meal = tester.widget<OutlinedButton>(
      find.byKey(const Key('add-meal-button')),
    );
    expect(meal.style?.minimumSize?.resolve(<WidgetState>{})?.height, 48);

    final details = tester.widget<OutlinedButton>(
      find.byKey(const Key('journal-details-button')),
    );
    expect(details.style?.minimumSize?.resolve(<WidgetState>{})?.height, 48);
    expect(tester.takeException(), isNull);
  });

  testWidgets('page mode suppresses the legacy internal header', (tester) async {
    _viewport(tester, const Size(390, 844));
    await tester.pumpWidget(_sheet(db, isPage: true));
    await tester.pumpAndSettle();

    expect(find.text('Nouvelle mesure'), findsNothing);
    expect(find.byKey(const Key('glucose-glass-card')), findsOneWidget);
    expect(find.byKey(const Key('glucose-unit')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('page content stays close beneath the canonical header', (
    tester,
  ) async {
    _viewport(tester, const Size(390, 844));
    await tester.pumpWidget(_screen(db));
    await tester.pumpAndSettle();

    expect(find.text('Nouvelle mesure'), findsOneWidget);
    final subtitle = find.text('Notez simplement ce qui vient de se passer.');
    expect(subtitle, findsOneWidget);

    final subtitleBottom = tester.getBottomLeft(subtitle).dy;
    final glucoseTop = tester
        .getTopLeft(find.byKey(const Key('glucose-glass-card')))
        .dy;
    expect(glucoseTop - subtitleBottom, lessThan(90));
    expect(glucoseTop, lessThan(210));
    expect(tester.takeException(), isNull);
  });

  testWidgets('compact frosted entry stays overflow-free on harsh small screen', (
    tester,
  ) async {
    _viewport(tester, const Size(360, 560));
    await tester.pumpWidget(_sheet(db));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('glucose-input')), findsOneWidget);
    expect(find.byKey(const Key('glucose-unit')), findsOneWidget);
    expect(find.byKey(const Key('save-log-button')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
