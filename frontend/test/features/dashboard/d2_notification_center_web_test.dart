import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/dashboard_premium_screen.dart';
import 'package:amina/features/notifications/d2_notifications_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

void main() {
  test('D2 bell route exists, and D3 reminders retain a separate route', () {
    final modules = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final home =
        File('lib/features/dashboard/dashboard_premium_screen.dart')
            .readAsStringSync();
    final d3 =
        File('lib/features/dashboard/widgets/dashboard_my_reminders_card.dart')
            .readAsStringSync();

    expect(modules, contains("path: '/notifications'"));
    expect(modules, contains('const D2NotificationsScreen()'));
    expect(modules, contains("path: '/reminders'"));
    expect(modules, contains('const RemindersScreen()'));
    expect(home, contains("ValueKey('dashboard-notifications-action')"));
    expect(home, contains("context.go('/notifications')"));
    expect(home, isNot(contains("ValueKey('dashboard-reminders-action')")));
    expect(home, contains('DashboardMyRemindersCard()'));
    expect(d3, contains("context.go('/reminders')"));
  });

  test('D2 empty inbox cannot claim real events or storage that do not exist', () {
    final source =
        File('lib/features/notifications/d2_notifications_screen.dart')
            .readAsStringSync();
    expect(source, contains('La réception des notifications n’est pas encore activée'));
    expect(source, contains('aucun message fictif'));
    expect(source, isNot(contains('Tout marquer comme lu')));
    expect(source, isNot(contains('notification-inbox')));
    expect(source, isNot(contains('ApiClient(')));
    expect(source, isNot(contains('Firebase')));
    expect(source, isNot(contains('reminder-title-input')));
  });

  for (final locale in const ['fr', 'ar', 'en']) {
    for (final viewport in const <(double, double)>[
      (390, 844),
      (430, 932),
      (768, 1024),
      (1280, 900),
    ]) {
      testWidgets('D2 true home bell -> D2 screen -> home, $locale $viewport',
          (tester) async {
        tester.view.physicalSize = Size(viewport.$1, viewport.$2);
        tester.view.devicePixelRatio = 1;
        final db = AppDatabase(NativeDatabase.memory());
        final router = GoRouter(
          initialLocation: '/dashboard',
          routes: [
            GoRoute(
              path: '/dashboard',
              builder: (context, state) => const DashboardPremiumScreen(),
            ),
            GoRoute(
              path: '/notifications',
              builder: (context, state) => const D2NotificationsScreen(),
            ),
            GoRoute(
              path: '/reminders',
              builder: (context, state) =>
                  const Scaffold(body: Text('D3_REMINDERS_DESTINATION')),
            ),
          ],
        );
        addTearDown(() async {
          tester.view.resetPhysicalSize();
          tester.view.resetDevicePixelRatio();
          router.dispose();
          await db.close();
        });

        await tester.pumpWidget(
          Provider<AppDatabase>.value(
            value: db,
            child: MaterialApp.router(
              routerConfig: router,
              locale: Locale(locale),
              supportedLocales: AppLocalizations.supportedLocales,
              localizationsDelegates: const [
                AppLocalizations.delegate,
                GlobalMaterialLocalizations.delegate,
                GlobalWidgetsLocalizations.delegate,
                GlobalCupertinoLocalizations.delegate,
              ],
            ),
          ),
        );
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);

        final bell =
            find.byKey(const ValueKey('dashboard-notifications-action'));
        expect(bell, findsOneWidget);
        // D3 is below the fold on mobile and SliverList builds lazily:
        // preserve its source contract above; D3 Chrome independently verifies it.
        expect(tester.widget<IconButton>(bell).tooltip, isNotEmpty);
        await tester.tap(bell);
        await tester.pumpAndSettle();

        expect(find.byKey(const ValueKey('d2-notifications-screen')),
            findsOneWidget);
        expect(find.byKey(const ValueKey('d2-notifications-unavailable')),
            findsOneWidget);
        expect(find.byKey(const ValueKey('d2-notifications-boundary')),
            findsOneWidget);
        expect(find.text('D3_REMINDERS_DESTINATION'), findsNothing);
        expect(find.byType(ListTile), findsNothing);
        expect(find.byType(Switch), findsNothing);
        final expected = switch (locale) {
          'ar' => 'الإشعارات ستتوفر قريباً',
          'en' => 'Notifications are coming soon',
          _ => 'Les notifications arrivent bientôt',
        };
        expect(find.text(expected), findsOneWidget);
        expect(tester.takeException(), isNull);

        await tester.tap(find.byKey(const ValueKey('amina-page-exit')));
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('d2-notifications-screen')),
            findsNothing);
        expect(find.byKey(const ValueKey('dashboard-notifications-action')),
            findsOneWidget);
        expect(tester.takeException(), isNull);
      });
    }
  }
}
