import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/edit_log_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

/// D22/F04: isolated synthetic in-memory SQLite records, never patient data.
/// This does not approve any mg/dL↔mmol/L conversion factor or target policy.
AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

Future<int> _seedGlucose(AppDatabase db, double raw, String uuid) =>
    db.into(db.logEntries).insert(
      LogEntriesCompanion.insert(
        createdAt: DateTime.utc(2026, 10, 29, 12),
        bloodSugar: raw,
        clientUuid: uuid,
      ),
    );

Future<PatientProfileData> _unitProfile(
  AppDatabase db,
  String unit,
) async {
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: const drift.Value(1),
      updatedAt: DateTime.utc(2026, 10, 29, 12),
      unitPreference: drift.Value(unit),
    ),
  );
  return (await db.getProfileForLocalUserId(1))!;
}

Widget _app(AppDatabase db, int id, PatientProfileData? profile) {
  final router = GoRouter(
    initialLocation: '/edit',
    routes: [
      GoRoute(
        path: '/edit',
        builder: (context, state) => MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            Provider<PatientProfileData?>.value(value: profile),
          ],
          child: EditLogScreen(logId: id),
        ),
      ),
      GoRoute(
        path: '/journal',
        builder: (context, state) =>
            const Scaffold(body: SizedBox(key: Key('journal-destination'))),
      ),
    ],
  );
  return MaterialApp.router(
    locale: const Locale('fr'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    routerConfig: router,
  );
}

Future<void> _save(WidgetTester tester) async {
  final save = tester.widget<FilledButton>(
    find.byKey(const Key('save-edit-log-button')),
  );
  expect(save.onPressed, isNotNull);
  save.onPressed!();
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'F04 mmol/L: changing meal only preserves original raw 103 mg/dL',
    (tester) async {
      final db = _openDb();
      addTearDown(db.close);
      final profile = await _unitProfile(db, 'mmol/L');
      final id = await _seedGlucose(
        db, 103.0, 'd22-f04-synthetic-01',
      );
      await tester.pumpWidget(_app(db, id, profile));
      await tester.pumpAndSettle();
      final field = tester.widget<TextField>(
        find.byKey(const Key('edit-glucose-input')),
      );
      expect(field.controller!.text, '5.7');
      // A non-glucose edit must not normalize 103 to 102.6.
      await tester.ensureVisible(find.byKey(const Key('add-meal-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('add-meal-button')));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('meal-note-input')),
        'Note modifiée uniquement',
      );
      await _save(tester);
      final after = (await db.getLogById(id))!;
      expect(after.bloodSugar, 103.0);
      expect(after.mealDescription, 'Note modifiée uniquement');
    },
  );

  testWidgets(
    'F04 mmol/L: equivalent decimal format 5,70 is not a glucose edit',
    (tester) async {
      final db = _openDb();
      addTearDown(db.close);
      final profile = await _unitProfile(db, 'mmol/L');
      final id = await _seedGlucose(
        db, 103.25, 'd22-f04-synthetic-02',
      );
      await tester.pumpWidget(_app(db, id, profile));
      await tester.pumpAndSettle();
      expect(
        tester.widget<TextField>(find.byKey(const Key('edit-glucose-input')))
            .controller!.text,
        '5.7',
      );
      await tester.enterText(
        find.byKey(const Key('edit-glucose-input')), '5,70',
      );
      await _save(tester);
      expect((await db.getLogById(id))!.bloodSugar, 103.25);
    },
  );

  testWidgets(
    'F04 mg/dL: rounded display and retyped equivalent retain raw 103.25',
    (tester) async {
      final db = _openDb();
      addTearDown(db.close);
      final profile = await _unitProfile(db, 'mg/dL');
      final id = await _seedGlucose(
        db, 103.25, 'd22-f04-synthetic-03',
      );
      await tester.pumpWidget(_app(db, id, profile));
      await tester.pumpAndSettle();
      expect(
        tester.widget<TextField>(find.byKey(const Key('edit-glucose-input')))
            .controller!.text,
        '103',
      );
      await tester.enterText(
        find.byKey(const Key('edit-glucose-input')), '103,0',
      );
      await _save(tester);
      expect((await db.getLogById(id))!.bloodSugar, 103.25);
    },
  );

  testWidgets(
    'F04 concurrent newer raw value is not overwritten by meal-only save',
    (tester) async {
      final db = _openDb();
      addTearDown(db.close);
      final profile = await _unitProfile(db, 'mmol/L');
      final id = await _seedGlucose(
        db, 103.0, 'd22-f04-synthetic-04',
      );
      await tester.pumpWidget(_app(db, id, profile));
      await tester.pumpAndSettle();
      await db.updateLog(
        id, const LogEntriesCompanion(bloodSugar: drift.Value(111.25)),
      );
      await _save(tester);
      expect((await db.getLogById(id))!.bloodSugar, 111.25);
    },
  );

  testWidgets(
    'F04 explicit mg/dL field change still writes the edited number',
    (tester) async {
      final db = _openDb();
      addTearDown(db.close);
      final profile = await _unitProfile(db, 'mg/dL');
      final id = await _seedGlucose(
        db, 103.0, 'd22-f04-synthetic-05',
      );
      await tester.pumpWidget(_app(db, id, profile));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('edit-glucose-input')), '111',
      );
      await _save(tester);
      expect((await db.getLogById(id))!.bloodSugar, 111.0);
    },
  );
}
