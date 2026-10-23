import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/dashboard_reminders_summary_card.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';


class _OwnerReminderDatabase extends AppDatabase {
  _OwnerReminderDatabase(this.count, this.title, {DateTime? firstDueAt})
      : firstDueAt = firstDueAt ?? DateTime.now().add(const Duration(days: 10)),
        super(NativeDatabase.memory());

  final int count;
  final String title;
  final DateTime firstDueAt;

  @override
  Stream<List<ReminderData>> watchReminders() => Stream.value(
    List<ReminderData>.generate(
      count,
      (i) => ReminderData(
        id: i + 1,
        title: title,
        dueAt: firstDueAt.add(Duration(days: i)),
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
    final a = _OwnerReminderDatabase(
      1, 'A synthetic medical title',
      firstDueAt: DateTime.now().add(const Duration(days: 10)),
    );
    final b = _OwnerReminderDatabase(
      2, 'B synthetic medical title',
      firstDueAt: DateTime.now().add(const Duration(days: 40)),
    );
    final aDate = DateFormat('dd/MM/yyyy HH:mm').format(a.firstDueAt);
    final bDate = DateFormat('dd/MM/yyyy HH:mm').format(b.firstDueAt);
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
          supportedLocales: [Locale('fr'), Locale('en'), Locale('ar')],
          localizationsDelegates: [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: Scaffold(body: DashboardRemindersSummaryCard()),
        ),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('1 rappel actif'), findsOneWidget);
    expect(find.textContaining('synthetic medical title'), findsNothing);
    expect(find.text(aDate), findsOneWidget);
    expect(find.text(bDate), findsNothing);

    selected.value = b;
    await tester.pump();
    expect(find.text('1 rappel actif'), findsNothing,
        reason: 'Never show patient A count during switch to B.');
    await tester.pumpAndSettle();
    expect(find.text('2 rappels actifs'), findsOneWidget);
    expect(find.textContaining('synthetic medical title'), findsNothing);
    expect(find.text(aDate), findsNothing,
        reason: 'Never retain patient A upcoming dates after vault change.');
    expect(find.text(bDate), findsOneWidget);

    selected.value = a;
    await tester.pump();
    expect(find.text('2 rappels actifs'), findsNothing,
        reason: 'Never show patient B count during switch to A.');
    await tester.pumpAndSettle();
    expect(find.text('1 rappel actif'), findsOneWidget);
    expect(find.text(aDate), findsOneWidget);
    expect(find.text(bDate), findsNothing);
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

  test('D3: next three means enabled + future + sorted, never titles', () {
    final now = DateTime(2026, 10, 23, 12);
    ReminderData item(int id, DateTime due, {bool enabled = true}) =>
        ReminderData(
          id: id,
          title: 'Private medical title $id',
          dueAt: due,
          enabled: enabled,
          createdAt: now.subtract(const Duration(days: 2)),
        );
    final next = now.add(const Duration(hours: 3));
    final later = now.add(const Duration(days: 2));
    final third = now.add(const Duration(days: 4));
    final fourth = now.add(const Duration(days: 6));
    expect(nextThreeUpcomingReminderTimes([
      item(1, fourth),
      item(2, now.subtract(const Duration(minutes: 1))),
      item(3, third),
      item(4, later),
      item(5, next),
      item(6, now.add(const Duration(minutes: 10)), enabled: false),
    ], now), [next, later, third]);
  });

  for (final viewport in const [
    Size(390, 844), Size(768, 1024), Size(1280, 900),
  ]) {
    testWidgets('D3 dates privacy and layout at ${viewport.width}x${viewport.height}',
        (tester) async {
      tester.view.physicalSize = viewport;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final first = DateTime.now().add(const Duration(days: 2));
      final dates = List<DateTime>.generate(
        4, (i) => first.add(Duration(days: i)),
      );
      final database = _OwnerReminderDatabase(
        4, 'SECRET MEDICATION NEVER ON HOME', firstDueAt: first,
      );
      addTearDown(database.close);
      final locale = viewport.width == 390
          ? const Locale('ar')
          : viewport.width == 768
              ? const Locale('fr')
              : const Locale('en');
      await tester.pumpWidget(Provider<AppDatabase>.value(
        value: database,
        child: MaterialApp(
          locale: locale,
          supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const Scaffold(body: DashboardRemindersSummaryCard()),
        ),
      ));
      await tester.pumpAndSettle();
      final expectedHeader = switch (locale.languageCode) {
        'ar' => 'المواعيد القادمة',
        'en' => 'Upcoming reminders',
        _ => 'Prochaines échéances',
      };
      expect(find.text(expectedHeader), findsOneWidget);
      for (var i = 0; i < 3; i++) {
        expect(
          find.text(DateFormat('dd/MM/yyyy HH:mm').format(dates[i])),
          findsOneWidget,
        );
      }
      expect(find.text(DateFormat('dd/MM/yyyy HH:mm').format(dates[3])),
          findsNothing);
      expect(find.textContaining('SECRET MEDICATION'), findsNothing);
      expect(find.byKey(const ValueKey('dashboard-reminder-due-3')),
          findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
}
