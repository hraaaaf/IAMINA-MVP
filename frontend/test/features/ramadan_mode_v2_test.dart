import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

AppDatabase openDb() => AppDatabase(NativeDatabase.memory());

Widget sheet(
  AppDatabase db,
  PatientProfileData profile, {
  Locale locale = const Locale('fr'),
}) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      body: MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          Provider<PatientProfileData?>.value(value: profile),
        ],
        child: const AddLogSheet(),
      ),
    ),
  );
}

Future<PatientProfileData> activeProfile(AppDatabase db) async {
  final now = DateTime.now();
  await db
      .into(db.patientProfiles)
      .insert(
        PatientProfilesCompanion.insert(
          userId: const drift.Value(1),
          updatedAt: now,
          ramadanStartDate: drift.Value(now.subtract(const Duration(days: 1))),
          ramadanEndDate: drift.Value(now.add(const Duration(days: 1))),
        ),
      );
  return db.select(db.patientProfiles).getSingle();
}

void main() {
  late AppDatabase db;
  setUp(() => db = openDb());
  tearDown(() async => db.close());

  testWidgets(
    'configured period adapts meal vocabulary without selecting a meal',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      final profile = await activeProfile(db);
      await tester.pumpWidget(sheet(db, profile));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('add-meal-button')));
      await tester.pumpAndSettle();

      expect(
        find.byKey(const Key('ramadan-meal-vocabulary-hint')),
        findsOneWidget,
      );
      expect(find.byKey(const Key('meal-type-suhoor')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-iftar')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-snack')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-other')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-breakfast')), findsNothing);
      for (final key in <String>['suhoor', 'iftar', 'snack', 'other']) {
        expect(
          tester.widget<ChoiceChip>(find.byKey(Key('meal-type-$key'))).selected,
          isFalse,
        );
      }
      expect(find.textContaining('Aucun jeûne n’est supposé'), findsOneWidget);
    },
  );

  testWidgets('Arabic Ramadan vocabulary is localized RTL and still neutral', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    final profile = await activeProfile(db);
    await tester.pumpWidget(sheet(db, profile, locale: const Locale('ar')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('add-meal-button')));
    await tester.pumpAndSettle();

    expect(find.text('السحور'), findsOneWidget);
    expect(find.text('الإفطار'), findsOneWidget);
    final hint = find.byKey(const Key('ramadan-meal-vocabulary-hint'));
    expect(hint, findsOneWidget);
    expect(Directionality.of(tester.element(hint)), TextDirection.rtl);
    expect(find.textContaining('لا يُفترض أنك صائم'), findsOneWidget);
  });
}
