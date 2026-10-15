import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/dashboard_reminders_summary_card.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

void main() {
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
