import 'package:amina/features/dashboard/dashboard_companion_entry_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  for (final locale in const <Locale>[Locale('fr'), Locale('ar')]) {
    for (final size in const <Size>[
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets('W03 approved FAB has dedicated non-overlapping lane and opens chat '
          '${locale.languageCode} $size', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final router = GoRouter(initialLocation: '/dashboard', routes: [
          GoRoute(
            path: '/dashboard',
            builder: (_, __) => DashboardCompanionFloatingShell(
              child: Scaffold(
                key: const ValueKey('dashboard-content-viewport'),
                body: ListView(
                  children: const [
                    SizedBox(height: 400, child: Text('READING_CARD')),
                    SizedBox(height: 400, child: Text('REMINDERS_CARD')),
                    SizedBox(height: 300),
                  ],
                ),
              ),
            ),
          ),
          GoRoute(
            path: '/companion/chat',
            builder: (_, __) => const Scaffold(body: Text('CHAT_ROUTE')),
          ),
        ]);
        addTearDown(router.dispose);

        await tester.pumpWidget(MaterialApp.router(
          locale: locale,
          supportedLocales: AppLocalizations.supportedLocales,
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          routerConfig: router,
        ));
        await tester.pumpAndSettle();

        final fab = find.byKey(const ValueKey('dashboard-companion-chat-action'));
        final lane = find.byKey(const ValueKey('dashboard-companion-safe-lane'));
        final viewport = find.byKey(const ValueKey('dashboard-content-viewport'));
        expect(fab, findsOneWidget);
        expect(lane, findsOneWidget);
        final fabRect = tester.getRect(fab);
        final viewportRect = tester.getRect(viewport);
        expect(fabRect.width, closeTo(58, .1));
        expect(fabRect.height, closeTo(58, .1));
        expect(fabRect.top, greaterThanOrEqualTo(viewportRect.bottom));
        expect(fabRect.bottom, lessThanOrEqualTo(tester.getRect(lane).bottom));
        if (locale.languageCode == 'ar') {
          expect(fabRect.left, lessThan(40));
        } else {
          expect(fabRect.right, greaterThan(size.width - 40));
        }
        expect(find.text('Poser une question'), findsNothing);
        expect(find.text('اطرح سؤالاً'), findsNothing);
        expect(tester.takeException(), isNull);
        await tester.tap(fab);
        await tester.pumpAndSettle();
        expect(find.text('CHAT_ROUTE'), findsOneWidget);
        expect(tester.takeException(), isNull);
      });
    }
  }
}
