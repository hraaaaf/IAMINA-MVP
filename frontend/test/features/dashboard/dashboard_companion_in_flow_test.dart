import 'package:amina/features/dashboard/widgets/dashboard_companion_callout.dart';
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
      for (final compact in const <bool>[false, true]) {
        testWidgets('W03 in-flow companion CTA routes without overlay '
            '${locale.languageCode} $size compact=$compact', (tester) async {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);

          final router = GoRouter(initialLocation: '/dashboard', routes: [
            GoRoute(
              path: '/dashboard',
              builder: (_, __) => Scaffold(
                body: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: DashboardCompanionCallout(compact: compact),
                  ),
                ),
              ),
            ),
            GoRoute(
              path: '/companion/chat',
              builder: (_, __) =>
                  const Scaffold(body: Text('IAMINA_CHAT_ROUTE')),
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

          final key = compact
              ? 'dashboard-empty-companion-secondary'
              : 'dashboard-secondary-companion';
          final button = find.byKey(ValueKey(key));
          expect(button, findsOneWidget);
          expect(find.byType(FloatingActionButton), findsNothing);
          expect(tester.getSize(button).height, greaterThanOrEqualTo(48));
          expect(
            find.text(locale.languageCode == 'ar'
                ? 'اطرح سؤالاً'
                : 'Poser une question'),
            findsOneWidget,
          );
          expect(tester.takeException(), isNull);

          await tester.tap(button);
          await tester.pumpAndSettle();
          expect(find.text('IAMINA_CHAT_ROUTE'), findsOneWidget);
          expect(tester.takeException(), isNull);
        });
      }
    }
  }
}
