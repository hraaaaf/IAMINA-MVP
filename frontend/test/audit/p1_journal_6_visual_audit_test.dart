import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/features/journal/edit_log_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

Widget _app(AppDatabase db, Locale locale, Widget child) => MaterialApp(
  locale: locale,
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(
    body: MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<PatientProfileData?>.value(value: null),
      ],
      child: RepaintBoundary(
        key: const Key('visual-audit-boundary'),
        child: child,
      ),
    ),
  ),
);

Future<void> _size(WidgetTester tester, Size size, AppDatabase db) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(() async {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
    await db.close();
  });
}

void main() {
  final cases = <(String, Locale, Size)>[
    ('fr-desktop-1440x1000', const Locale('fr'), const Size(1440, 1000)),
    ('fr-tablet-768x1024', const Locale('fr'), const Size(768, 1024)),
    ('fr-mobile-390x844', const Locale('fr'), const Size(390, 844)),
    ('fr-small-360x560', const Locale('fr'), const Size(360, 560)),
    ('ar-desktop-1440x1000', const Locale('ar'), const Size(1440, 1000)),
    ('ar-tablet-768x1024', const Locale('ar'), const Size(768, 1024)),
    ('ar-mobile-390x844', const Locale('ar'), const Size(390, 844)),
    ('ar-small-360x560', const Locale('ar'), const Size(360, 560)),
  ];

  for (final item in cases) {
    testWidgets('add context ${item.$1}', (tester) async {
      final db = AppDatabase(NativeDatabase.memory());
      await _size(tester, item.$3, db);
      await tester.pumpWidget(_app(db, item.$2, const AddLogSheet(isPage: true)));
      await tester.pumpAndSettle();

      final details = find.byKey(const Key('journal-details-button'));
      if (details.evaluate().isNotEmpty) {
        await tester.ensureVisible(details);
        await tester.tap(details);
        await tester.pumpAndSettle();
      }

      expect(find.byKey(const Key('journal-context-selector')), findsNothing);
      final contextButton = find.byKey(const Key('journal-context-button'));
      await tester.ensureVisible(contextButton);
      await tester.tap(contextButton);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-context-selector')), findsOneWidget);
      await tester.ensureVisible(find.byKey(const Key('context-stress')));
      await tester.tap(find.byKey(const Key('context-stress')));
      await tester.tap(find.byKey(const Key('context-poor-sleep')));
      await tester.pumpAndSettle();

      await expectLater(
        find.byKey(const Key('visual-audit-boundary')),
        matchesGoldenFile('goldens/p1j6-add-${item.$1}.png'),
      );
    });

    testWidgets('edit context ${item.$1}', (tester) async {
      final db = AppDatabase(NativeDatabase.memory());
      await _size(tester, item.$3, db);
      final id = await db.into(db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: DateTime(2026, 8, 9, 12),
          bloodSugar: 132,
          insulinUnits: const drift.Value(4.5),
          glycemicContext: const drift.Value('post_meal'),
          mealType: const drift.Value('lunch'),
          clientUuid: '66666666-6666-6666-6666-666666666666',
          loggedAt: drift.Value(DateTime(2026, 8, 9, 12)),
          isSick: const drift.Value(true),
          isStressed: const drift.Value(false),
          isActive: const drift.Value(true),
          sleepQuality: const drift.Value('bad'),
        ),
      );
      await tester.pumpWidget(_app(db, item.$2, EditLogScreen(logId: id)));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('edit-context-card')), findsOneWidget);
      expect(find.byKey(const Key('edit-context-illness')), findsOneWidget);
      expect(find.byKey(const Key('edit-context-poor-sleep')), findsOneWidget);

      await expectLater(
        find.byKey(const Key('visual-audit-boundary')),
        matchesGoldenFile('goldens/p1j6-edit-${item.$1}.png'),
      );
    });
  }
}
