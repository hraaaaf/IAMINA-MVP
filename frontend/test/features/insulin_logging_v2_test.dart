import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/edit_log_screen.dart';
import 'package:amina/features/journal/widgets/insulin_logging.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

AppDatabase _db() => AppDatabase(NativeDatabase.memory());

Widget _providers(
  AppDatabase db,
  Widget child, {
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
          Provider<PatientProfileData?>.value(value: null),
        ],
        child: child,
      ),
    ),
  );
}

void main() {
  test('dose formatter preserves patient-entered decimal precision', () {
    expect(formatTakenInsulinUnits(4), '4');
    expect(formatTakenInsulinUnits(4.5), '4.5');
    expect(formatTakenInsulinUnits(4.75), '4.75');
    expect(isValidTakenInsulinInput(''), isTrue);
    expect(isValidTakenInsulinInput('4,5'), isTrue);
    expect(isValidTakenInsulinInput('0'), isFalse);
    expect(isValidTakenInsulinInput('-1'), isFalse);
  });

  testWidgets(
    'edit clears historical insulin without rewriting meal context or Ramadan legacy state',
    (tester) async {
      final db = _db();
      addTearDown(db.close);
      final id = await db
          .into(db.logEntries)
          .insert(
            LogEntriesCompanion.insert(
              createdAt: DateTime(2026, 8, 9, 12),
              bloodSugar: 130,
              insulinUnits: const drift.Value(4.5),
              glycemicContext: const drift.Value('post_meal'),
              mealType: const drift.Value('lunch'),
              clientUuid: '11111111-1111-1111-1111-111111111111',
              loggedAt: drift.Value(DateTime(2026, 8, 9, 12)),
              ramadanMode: const drift.Value(true),
              syncStatus: const drift.Value('synced'),
              syncAttempts: const drift.Value(2),
              errorSync: const drift.Value(true),
            ),
          );

      await tester.pumpWidget(_providers(db, EditLogScreen(logId: id)));
      await tester.pumpAndSettle();
      final insulinField = tester.widget<TextField>(
        find.byKey(const Key('edit-insulin-taken-input')),
      );
      expect(insulinField.controller?.text, '4.5');
      expect(find.text('Mode Ramadan'), findsNothing);
      expect(find.text('Iftar'), findsNothing);

      await tester.enterText(
        find.byKey(const Key('edit-insulin-taken-input')),
        '',
      );
      await tester.tap(find.byKey(const Key('save-edit-log-button')));
      await tester.pumpAndSettle();

      final log = await db.getLogById(id);
      expect(log!.insulinUnits, isNull);
      expect(log.glycemicContext, 'post_meal');
      expect(log.mealType, 'lunch');
      expect(log.ramadanMode, isTrue);
      expect(log.syncStatus, 'pending');
      expect(log.syncAttempts, 0);
      expect(log.errorSync, isFalse);
    },
  );

  testWidgets(
    'edit accepts decimal administered dose without stepper rounding',
    (tester) async {
      final db = _db();
      addTearDown(db.close);
      final id = await db
          .into(db.logEntries)
          .insert(
            LogEntriesCompanion.insert(
              createdAt: DateTime(2026, 8, 9, 12),
              bloodSugar: 130,
              clientUuid: '22222222-2222-2222-2222-222222222222',
            ),
          );
      await tester.pumpWidget(_providers(db, EditLogScreen(logId: id)));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('edit-insulin-taken-input')),
        '4.75',
      );
      await tester.tap(find.byKey(const Key('save-edit-log-button')));
      await tester.pumpAndSettle();
      expect((await db.getLogById(id))!.insulinUnits, 4.75);
    },
  );

  testWidgets('edit flow is localized in Arabic RTL', (tester) async {
    final db = _db();
    addTearDown(db.close);
    final id = await db
        .into(db.logEntries)
        .insert(
          LogEntriesCompanion.insert(
            createdAt: DateTime(2026, 8, 9, 12),
            bloodSugar: 130,
            clientUuid: '33333333-3333-3333-3333-333333333333',
          ),
        );
    await tester.pumpWidget(
      _providers(db, EditLogScreen(logId: id), locale: const Locale('ar')),
    );
    await tester.pumpAndSettle();
    expect(find.text('تعديل القياس'), findsOneWidget);
    expect(find.text('Modifier la mesure'), findsNothing);
    expect(
      Directionality.of(tester.element(find.text('تعديل القياس'))),
      TextDirection.rtl,
    );
  });
}
