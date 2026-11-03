import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/dashboard_my_reminders_card.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

class _OwnerDatabase extends AppDatabase {
  _OwnerDatabase(this.items) : super(NativeDatabase.memory());

  final List<ReminderData> items;

  @override
  Stream<List<ReminderData>> watchReminders() => Stream.value(items);
}

MaterialApp _localizedApp(Widget child, Locale locale) => MaterialApp(
  locale: locale,
  supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
  localizationsDelegates: const [
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  home: Scaffold(body: child),
);

void main() {
  test('D3 replaces Your next step without moving clinical trends', () {
    final source = File('lib/features/dashboard/widgets/dashboard_responsive_sections.dart')
        .readAsStringSync();
    expect(source, contains('DashboardTrendSection('));
    expect(source, contains('DashboardInsightSection('));
    expect(source, contains('DashboardMyRemindersCard()'));
    expect(source, isNot(contains('DashboardNextActionSection(')));
    expect(
      source.indexOf('DashboardMyRemindersCard()'),
      greaterThan(source.indexOf('DashboardTrendSection(')),
    );
    final premium =
        File('lib/features/dashboard/dashboard_premium_screen.dart')
            .readAsStringSync();
    expect(
      premium.substring(premium.indexOf('class _EmptyPremiumDashboard')),
      contains('DashboardMyRemindersCard()'),
      reason: 'Reminders must exist on Home even before a first glucose reading.',
    );
  });

  for (final locale in const [Locale('fr'), Locale('en'), Locale('ar')]) {
    testWidgets('D3 real 3 upcoming, empty CTA, ordering and locale ' +
        locale.languageCode, (tester) async {
      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      final router = GoRouter(
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) =>
                const Scaffold(body: DashboardMyRemindersCard()),
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
          value: db,
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

      final empty = switch (locale.languageCode) {
        'ar' => 'لم يتم إعداد أي تذكير.',
        'en' => 'No reminders configured.',
        _ => 'Aucun rappel configuré.',
      };
      expect(find.text(empty), findsOneWidget);
      expect(find.byKey(const ValueKey('d3-reminders-create')), findsOneWidget);
      final now = DateTime.now();
      final late = await db.addReminder(
        title: 'REMINDER_LATE', dueAt: now.add(const Duration(days: 5)));
      final first = await db.addReminder(
        title: 'REMINDER_FIRST', dueAt: now.add(const Duration(days: 1)));
      final third = await db.addReminder(
        title: 'REMINDER_THIRD', dueAt: now.add(const Duration(days: 3)));
      final second = await db.addReminder(
        title: 'REMINDER_SECOND', dueAt: now.add(const Duration(days: 2)));
      final old = await db.addReminder(
        title: 'REMINDER_PAST', dueAt: now.subtract(const Duration(days: 1)));
      final disabled = await db.addReminder(
        title: 'REMINDER_DISABLED', dueAt: now.add(const Duration(hours: 1)));
      await db.setReminderEnabled(disabled, false);
      await tester.pumpAndSettle();

      expect(find.byKey(ValueKey('d3-reminder-' + first.toString())),
          findsOneWidget);
      expect(find.byKey(ValueKey('d3-reminder-' + second.toString())),
          findsOneWidget);
      expect(find.byKey(ValueKey('d3-reminder-' + third.toString())),
          findsOneWidget);
      expect(find.byKey(ValueKey('d3-reminder-' + late.toString())),
          findsNothing);
      expect(find.byKey(ValueKey('d3-reminder-' + old.toString())),
          findsNothing);
      expect(find.byKey(ValueKey('d3-reminder-' + disabled.toString())),
          findsNothing);

      // Dates are chronological, not creation order, and never demo reminders.
      final visible = tester.widgetList<Text>(find.byType(Text))
          .map((t) => t.data).toList();
      expect(visible.indexOf('REMINDER_FIRST'),
          lessThan(visible.indexOf('REMINDER_SECOND')));
      expect(visible.indexOf('REMINDER_SECOND'),
          lessThan(visible.indexOf('REMINDER_THIRD')));
      expect(find.text(empty), findsNothing);
      expect(find.byKey(const ValueKey('d3-reminders-see-all')), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('d3-reminders-see-all')));
      await tester.pumpAndSettle();
      expect(find.text('REMINDERS_DESTINATION'), findsOneWidget);
    });
  }

  testWidgets('D3 vault A to B to A never exposes previous owner reminders',
      (tester) async {
    final now = DateTime.now();
    ReminderData sample(int id, String name) => ReminderData(
      id: id,
      title: name,
      dueAt: now.add(const Duration(days: 1)),
      enabled: true,
      createdAt: now,
    );
    final a = _OwnerDatabase([sample(1, 'OWNER_A_PRIVATE')]);
    final b = _OwnerDatabase([sample(2, 'OWNER_B_PRIVATE')]);
    addTearDown(a.close);
    addTearDown(b.close);
    final current = ValueNotifier<AppDatabase>(a);
    addTearDown(current.dispose);
    await tester.pumpWidget(ValueListenableBuilder<AppDatabase>(
      valueListenable: current,
      builder: (context, db, _) => Provider<AppDatabase>.value(
        value: db,
        child: _localizedApp(const DashboardMyRemindersCard(),
            const Locale('fr')),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('OWNER_A_PRIVATE'), findsOneWidget);
    expect(find.text('OWNER_B_PRIVATE'), findsNothing);

    current.value = b;
    await tester.pump();
    expect(find.text('OWNER_A_PRIVATE'), findsNothing);
    await tester.pumpAndSettle();
    expect(find.text('OWNER_B_PRIVATE'), findsOneWidget);

    current.value = a;
    await tester.pump();
    expect(find.text('OWNER_B_PRIVATE'), findsNothing);
    await tester.pumpAndSettle();
    expect(find.text('OWNER_A_PRIVATE'), findsOneWidget);
  });

  testWidgets('D3 empty state opens actual reminder creation screen',
      (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    final router = GoRouter(routes: [
      GoRoute(
        path: '/',
        builder: (context, state) =>
            const Scaffold(body: DashboardMyRemindersCard()),
      ),
      GoRoute(
        path: '/reminders',
        builder: (context, state) =>
            const Scaffold(body: Text('CREATE_REMINDER_DESTINATION')),
      ),
    ]);
    addTearDown(router.dispose);
    await tester.pumpWidget(Provider<AppDatabase>.value(
      value: db,
      child: MaterialApp.router(routerConfig: router),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('d3-reminders-create')));
    await tester.pumpAndSettle();
    expect(find.text('CREATE_REMINDER_DESTINATION'), findsOneWidget);
  });
}
