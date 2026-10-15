import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/dashboard_reminders_summary_card.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';


class _OwnerReminderDatabase extends AppDatabase {
  _OwnerReminderDatabase(this.count, this.title) : super(NativeDatabase.memory());

  final int count;
  final String title;

  @override
  Stream<List<ReminderData>> watchReminders() => Stream.value(
    List<ReminderData>.generate(
      count,
      (i) => ReminderData(
        id: i + 1,
        title: title,
        dueAt: DateTime(2026, 11, 12),
        enabled: true,
        createdAt: DateTime(2026, 10, 15),
      ),
    ),
  );
}

void main() {
  testWidgets('decision #3 A→B→A database switch never shows previous owner', (tester) async {
    // Controlled, independent vault streams isolate the widget's owner
    // switching behavior from Drift's native asynchronous test scheduler.
    // The other FR/EN/AR tests exercise actual Drift reads and writes.
    final a = _OwnerReminderDatabase(1, 'A synthetic medical title');
    final b = _OwnerReminderDatabase(2, 'B synthetic medical title');
    addTearDown(a.close);
    addTearDown(b.close);
    final selected = ValueNotifier<AppDatabase>(a);
    addTearDown(selected.dispose);

    await tester.pumpWidget(ValueListenableBuilder<AppDatabase>(
      valueListenable: selected,
      builder: (context, db, _) => Provider<AppDatabase>.value(
        value: db,
        child: const MaterialApp(
          locale: Locale('fr'),
          home: Scaffold(body: DashboardRemindersSummaryCard()),
        ),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('1 rappel actif'), findsOneWidget);
    expect(find.textContaining('synthetic medical title'), findsNothing);

    selected.value = b;
    await tester.pump();
    expect(find.text('1 rappel actif'), findsNothing,
        reason: 'Never show patient A count during switch to B.');
    await tester.pumpAndSettle();
    expect(find.text('2 rappels actifs'), findsOneWidget);
    expect(find.textContaining('synthetic medical title'), findsNothing);

    selected.value = a;
    await tester.pump();
    expect(find.text('2 rappels actifs'), findsNothing,
        reason: 'Never show patient B count during switch to A.');
    await tester.pumpAndSettle();
    expect(find.text('1 rappel actif'), findsOneWidget);
  });

  test('decision #3 keeps the clinical trend section ahead of reminders', () {
    final source = File('lib/features/dashboard/dashboard_premium_screen.dart')
        .readAsStringSync();
    final start = source.indexOf('SliverChildListDelegate([');
    final end = source.indexOf('const _DataTools()', start);
    expect(start, greaterThanOrEqualTo(0));
    expect(end, greaterThan(start));
    final sliver = source.substring(start, end);
    final today = sliver.indexOf('DashboardTodaySection(');
    final trends = sliver.indexOf('DashboardResponsiveSections(');
    final reminders = sliver.indexOf('const DashboardRemindersSummaryCard()');
    expect(today, greaterThanOrEqualTo(0));
    expect(trends, greaterThan(today));
    expect(reminders, greaterThan(trends));
  });

  for (final locale in const [Locale('fr'), Locale('en'), Locale('ar')]) {
    testWidgets('decision #3 local-first count and privacy ${locale.languageCode}',
        (tester) async {
      final database = AppDatabase(NativeDatabase.memory());
      addTearDown(database.close);
      final router = GoRouter(
        initialLocation: '/',
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) =>
                const Scaffold(body: DashboardRemindersSummaryCard()),
          ),
          GoRoute(
            path: '/reminders',
            builder: (context, state) =>
                const Scaffold(body: Text('REMINDERS_DESTINATION')),
          ),
        ],
      );
      addTearDown(router.dispose);
      await tester.pumpWidget(
        Provider<AppDatabase>.value(
          value: database,
          child: MaterialApp.router(
            locale: locale,
            supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            routerConfig: router,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('dashboard-reminders-card')),
          findsOneWidget);
      final empty = switch (locale.languageCode) {
        'ar' => 'لا توجد تذكيرات نشطة',
        'en' => 'No active reminders',
        _ => 'Aucun rappel actif',
      };
      expect(find.text(empty), findsOneWidget);

      final id = await database.addReminder(
        title: 'Synthetic sensitive medication title',
        dueAt: DateTime(2026, 11, 12),
      );
      await tester.pumpAndSettle();
      final one = switch (locale.languageCode) {
        'ar' => 'تذكير نشط واحد',
        'en' => '1 active reminder',
        _ => '1 rappel actif',
      };
      expect(find.text(one), findsOneWidget);
      expect(find.textContaining('Synthetic sensitive'), findsNothing);

      await database.setReminderEnabled(id, false);
      await tester.pumpAndSettle();
      expect(find.text(empty), findsOneWidget);
      await database.setReminderEnabled(id, true);
      await tester.pumpAndSettle();
      expect(find.text(one), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('dashboard-reminders-card')));
      await tester.pumpAndSettle();
      expect(find.text('REMINDERS_DESTINATION'), findsOneWidget);
    });
  }
}
