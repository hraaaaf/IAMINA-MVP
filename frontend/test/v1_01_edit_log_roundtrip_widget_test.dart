import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/edit_log_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

void main() {
  testWidgets(
    'unchanged mmol/L edit preserves 69.9 mg/dL in real Drift storage',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      final recordedAt = DateTime(2026, 9, 20, 10, 30);
      await db.into(db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const Value(1),
          updatedAt: recordedAt,
          unitPreference: const Value('mmol/L'),
        ),
      );
      final logId = await db.into(db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: recordedAt,
          bloodSugar: 69.9,
          clientUuid: 'v1-01-edit-no-op-699',
          loggedAt: Value(recordedAt),
        ),
      );
      final profile = await db.select(db.patientProfiles).getSingle();
      final router = GoRouter(
        initialLocation: '/journal/$logId/edit',
        routes: [
          GoRoute(
            path: '/journal/:id/edit',
            builder: (_, state) => EditLogScreen(
              logId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(
            path: '/journal',
            builder: (_, __) => const Scaffold(body: Text('Journal returned')),
          ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            Provider<PatientProfileData?>.value(value: profile),
            ChangeNotifierProvider<TweaksNotifier>(
              create: (_) => TweaksNotifier(),
            ),
          ],
          child: MaterialApp.router(
            locale: const Locale('fr'),
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
            routerConfig: router,
          ),
        ),
      );
      await tester.pumpAndSettle();

      final glucoseInput = find.byKey(const Key('edit-glucose-input'));
      expect(glucoseInput, findsOneWidget);
      expect(tester.widget<TextField>(glucoseInput).controller!.text, '3.9');

      final save = find.byKey(const Key('save-edit-log-button'));
      await tester.ensureVisible(save);
      await tester.pumpAndSettle();
      await tester.tap(save);
      await tester.pumpAndSettle();

      // 69.9 mg/dL must remain in the low-glucose safety branch; re-encoding
      // a rounded 3.9 mmol/L would otherwise silently cross 70 mg/dL.
      final dialog = find.byType(AlertDialog);
      expect(dialog, findsOneWidget);
      final confirm = find.descendant(
        of: dialog,
        matching: find.byType(FilledButton),
      );
      expect(confirm, findsOneWidget);
      await tester.tap(confirm);
      await tester.pumpAndSettle();

      final stored = await db.getLogById(logId);
      expect(stored, isNotNull);
      expect(stored!.bloodSugar, closeTo(69.9, 1e-9));
      expect(stored.bloodSugar < 70, isTrue);

      // Stop subscribed widgets before database teardown.
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    },
  );
  for (final viewport in <Size>[const Size(390, 844), const Size(768, 1024)]) {
    for (final modifyGlucose in <bool>[false, true]) {
      testWidgets(
        'unit preference switch during edit cannot reinterpret glucose '
        '${viewport.width.toInt()}px, modified=$modifyGlucose',
        (tester) async {
          tester.view.physicalSize = viewport;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);

          final db = AppDatabase(NativeDatabase.memory());
          addTearDown(db.close);
          final recordedAt = DateTime(2026, 9, 20, 10, 30);
          await db.into(db.patientProfiles).insert(
            PatientProfilesCompanion.insert(
              userId: const Value(1),
              updatedAt: recordedAt,
              unitPreference: const Value('mmol/L'),
            ),
          );
          final id = await db.into(db.logEntries).insert(
            LogEntriesCompanion.insert(
              createdAt: recordedAt,
              bloodSugar: 69.9,
              clientUuid: 'v1-01-switch-${viewport.width}-$modifyGlucose',
              loggedAt: Value(recordedAt),
            ),
          );
          final initialProfile =
              await db.select(db.patientProfiles).getSingle();
          final profileNotifier =
              ValueNotifier<PatientProfileData?>(initialProfile);
          addTearDown(profileNotifier.dispose);
          final router = GoRouter(
            initialLocation: '/journal/$id/edit',
            routes: [
              GoRoute(
                path: '/journal/:id/edit',
                builder: (_, state) => EditLogScreen(
                  logId: int.parse(state.pathParameters['id']!),
                ),
              ),
              GoRoute(
                path: '/journal',
                builder: (_, __) =>
                    const Scaffold(body: Text('Journal returned')),
              ),
            ],
          );
          addTearDown(router.dispose);
          await tester.pumpWidget(
            ValueListenableBuilder<PatientProfileData?>(
              valueListenable: profileNotifier,
              builder: (_, profile, __) => MultiProvider(
                providers: [
                  Provider<AppDatabase>.value(value: db),
                  Provider<PatientProfileData?>.value(value: profile),
                  ChangeNotifierProvider<TweaksNotifier>(
                    create: (_) => TweaksNotifier(),
                  ),
                ],
                child: MaterialApp.router(
                  locale: const Locale('fr'),
                  localizationsDelegates:
                      AppLocalizations.localizationsDelegates,
                  supportedLocales: AppLocalizations.supportedLocales,
                  routerConfig: router,
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();

          final glucoseInput = find.byKey(const Key('edit-glucose-input'));
          expect(glucoseInput, findsOneWidget);
          expect(tester.widget<TextField>(glucoseInput).controller!.text, '3.9');
          expect(tester.widget<TextField>(glucoseInput).decoration?.suffixText,
              'mmol/L');

          profileNotifier.value =
              initialProfile.copyWith(unitPreference: 'mg/dL');
          await tester.pumpAndSettle();
          // The profile changed, but the editor keeps its original unit
          // together with the displayed value; it never reinterprets 3.9.
          expect(tester.widget<TextField>(glucoseInput).controller!.text, '3.9');
          expect(tester.widget<TextField>(glucoseInput).decoration?.suffixText,
              'mmol/L');

          if (modifyGlucose) {
            await tester.enterText(glucoseInput, '4.0');
          }
          final save = find.byKey(const Key('save-edit-log-button'));
          // After editing a TextField, focused keyboard/scroll position can
          // leave the footer below the 390px test viewport. Exercise a real
          // scroll gesture until the save control is actually hit-testable.
          tester.testTextInput.hide();
          await tester.pumpAndSettle();
          await tester.dragUntilVisible(
            save,
            find.byType(SingleChildScrollView).first,
            const Offset(0, -250),
          );
          await tester.pumpAndSettle();
          await tester.tap(save);
          await tester.pumpAndSettle();

          if (!modifyGlucose) {
            final dialog = find.byType(AlertDialog);
            expect(dialog, findsOneWidget);
            final confirm = find.descendant(
              of: dialog,
              matching: find.byType(FilledButton),
            );
            expect(confirm, findsOneWidget);
            await tester.tap(confirm);
            await tester.pumpAndSettle();
          } else {
            // 4.0 mmol/L = 72.064 mg/dL: not a low-glucose alert.
            expect(find.byType(AlertDialog), findsNothing);
          }

          final stored = await db.getLogById(id);
          expect(stored, isNotNull);
          expect(
            stored!.bloodSugar,
            closeTo(modifyGlucose ? 72.064 : 69.9, 1e-7),
          );
          await tester.pumpWidget(const SizedBox.shrink());
          await tester.pumpAndSettle();
        },
      );
    }
  }

}
