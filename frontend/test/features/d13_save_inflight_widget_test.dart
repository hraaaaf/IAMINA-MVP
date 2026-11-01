import 'dart:async';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' show QueryExecutor, QueryInterceptor;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

/// Delay the actual Drift INSERT statement, not the onSave callback or a fake
/// widget state. The same in-memory SQLite row is written when released.
class _HeldGlucoseInsert extends QueryInterceptor {
  final entered = Completer<void>();
  final release = Completer<void>();

  @override
  Future<int> runInsert(
    QueryExecutor executor,
    String statement,
    List<Object?> args,
  ) async {
    if (statement.toLowerCase().contains('log_entries')) {
      if (!entered.isCompleted) entered.complete();
      await release.future;
    }
    return executor.runInsert(statement, args);
  }
}

Widget _routeHarness(AppDatabase db, Locale locale) => MaterialApp(
  locale: locale,
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(
    body: Builder(
      builder: (context) => Center(
        child: FilledButton(
          key: const Key('open-add-log'),
          onPressed: () {
            Navigator.of(context).push<void>(
              MaterialPageRoute<void>(
                builder: (_) => Scaffold(
                  body: MultiProvider(
                    providers: [
                      Provider<AppDatabase>.value(value: db),
                      Provider<PatientProfileData?>.value(value: null),
                    ],
                    child: const AddLogSheet(),
                  ),
                ),
              ),
            );
          },
          child: const Text('OPEN'),
        ),
      ),
    ),
  ),
);

void main() {
  for (final testCase in <({Locale locale, Size viewport})>[
    (locale: const Locale('fr'), viewport: const Size(390, 844)),
    (locale: const Locale('ar'), viewport: const Size(1280, 900)),
  ]) {
    testWidgets(
      'D13 ${testCase.locale.languageCode} blocks back while real Drift insert '
      'is pending and writes exactly once after release',
      (tester) async {
        tester.view.physicalSize = testCase.viewport;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final held = _HeldGlucoseInsert();
        final db = AppDatabase(NativeDatabase.memory().interceptWith(held));
        addTearDown(() async {
          if (!held.release.isCompleted) held.release.complete();
          await db.close();
        });

        await tester.pumpWidget(_routeHarness(db, testCase.locale));
        await tester.pumpAndSettle();
        await tester.tap(find.byKey(const Key('open-add-log')));
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('glucose-input')), findsOneWidget);
        await tester.enterText(find.byKey(const Key('glucose-input')), '126');
        await tester.pump();
        await tester.tap(find.byKey(const Key('save-log-button')));
        await tester.pump();
        await tester.pump();

        expect(held.entered.isCompleted, isTrue,
            reason: 'Must intercept the real SQLite log INSERT.');
        expect(
          tester.widget<FilledButton>(
            find.byKey(const Key('save-log-button')),
          ).onPressed,
          isNull,
          reason: 'Duplicate save disabled while the INSERT awaits.',
        );

        // App back and system/browser back both use _confirmLeave.
        await tester.tap(find.byIcon(Icons.arrow_back_ios_new_rounded));
        await tester.pump();
        expect(find.byKey(const Key('glucose-input')), findsOneWidget);
        expect(find.byType(AlertDialog), findsNothing);

        await tester.binding.handlePopRoute();
        await tester.pump();
        expect(find.byKey(const Key('glucose-input')), findsOneWidget);
        expect(find.byType(AlertDialog), findsNothing);
        expect(find.byKey(const Key('post-save-receipt')), findsNothing);

        held.release.complete();
        await tester.pumpAndSettle();

        final rows = await db.select(db.logEntries).get();
        expect(rows, hasLength(1));
        expect(rows.single.bloodSugar, 126);
        expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
  }
}
