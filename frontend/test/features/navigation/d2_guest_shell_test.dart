import 'package:amina/features/navigation/d2_guest_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

/// D2 isolated-component tests, NOT a live application or database FUE.
/// No database, backend, patient session or AI provider is constructed.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const viewports = <(double, double)>[
    (390, 844),
    (430, 932),
    (768, 1024),
    (1280, 900),
  ];

  for (final locale in const ['fr', 'ar']) {
    for (final viewport in viewports) {
      testWidgets('D2 guest shell navigation $locale $viewport', (tester) async {
        tester.view.physicalSize = Size(viewport.$1, viewport.$2);
        tester.view.devicePixelRatio = 1;
        addTearDown(() {
          tester.view.resetPhysicalSize();
          tester.view.resetDevicePixelRatio();
        });

        final requestedRoutes = <String>[];
        await tester.pumpWidget(MaterialApp(
          locale: Locale(locale),
          supportedLocales: const [Locale('fr'), Locale('ar')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: D2GuestShell(onProtectedAction: requestedRoutes.add),
        ));
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('d2-guest-empty-state')), findsOneWidget);
        expect(tester.takeException(), isNull);

        for (final section in ['journal', 'summary', 'profile', 'dashboard']) {
          final target = find.byKey(Key('d2-guest-nav-$section'));
          expect(target, findsOneWidget);
          await tester.tap(target);
          await tester.pumpAndSettle();
          expect(find.byKey(const Key('d2-guest-empty-state')), findsOneWidget);
          expect(tester.takeException(), isNull);
        }

        // Browsing sections must never request login or make a provider call.
        expect(requestedRoutes, isEmpty);
        expect(find.byKey(const Key('d2-guest-action-companion')), findsOneWidget);
      });
    }
  }

  for (final locale in const ['fr', 'ar']) {
    testWidgets('D2 protected first use requests login $locale', (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final requestedRoutes = <String>[];
      await tester.pumpWidget(MaterialApp(
        locale: Locale(locale),
        supportedLocales: const [Locale('fr'), Locale('ar')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: D2GuestShell(onProtectedAction: requestedRoutes.add),
      ));
      await tester.pumpAndSettle();

      for (final entry in const [
        ('add', '/ajouter'),
        ('import', '/importer'),
        ('companion', '/companion/chat'),
      ]) {
        final button = find.byKey(Key('d2-guest-action-${entry.$1}'));
        await tester.ensureVisible(button);
        await tester.tap(button);
        await tester.pump();
        expect(requestedRoutes.last, entry.$2);
      }

      await tester.tap(find.byKey(const Key('d2-guest-nav-summary')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('d2-guest-action-export')));
      expect(requestedRoutes.last, '/summary?intent=export');

      await tester.tap(find.byKey(const Key('d2-guest-nav-profile')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('d2-guest-action-edit')));
      expect(requestedRoutes.last, '/profile?intent=edit');

      expect(requestedRoutes, [
        '/ajouter',
        '/importer',
        '/companion/chat',
        '/summary?intent=export',
        '/profile?intent=edit',
      ]);
      expect(tester.takeException(), isNull);
    });
  }
}
