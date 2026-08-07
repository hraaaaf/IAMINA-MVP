import 'package:amina/features/navigation/main_shell.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/modules_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<GoRouter> pumpNavigation(
    WidgetTester tester, {
    required Locale locale,
  }) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;

    final api = ApiClient(baseUrl: 'http://127.0.0.1:1');
    final modules = ModulesProvider(api);
    final router = GoRouter(
      initialLocation: '/dashboard',
      routes: [
        ShellRoute(
          builder: (_, __, child) => MainShell(child: child),
          routes: [
            for (final route in const [
              '/dashboard',
              '/summary',
              '/journal',
              '/importer',
              '/profile',
            ])
              GoRoute(
                path: route,
                builder: (_, __) => Scaffold(
                  body: Center(child: Text('route:$route')),
                ),
              ),
          ],
        ),
      ],
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<ModulesProvider>.value(
        value: modules,
        child: MaterialApp.router(
          routerConfig: router,
          locale: locale,
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
        ),
      ),
    );
    await tester.pumpAndSettle();
    return router;
  }

  void expectTouchTargets(WidgetTester tester) {
    for (final route in const [
      '/dashboard',
      '/summary',
      '/journal',
      '/importer',
      '/profile',
    ]) {
      final destination = find.byKey(ValueKey('mobile-nav-$route'));
      expect(destination, findsOneWidget);
      final size = tester.getSize(destination);
      expect(size.width, greaterThanOrEqualTo(48));
      expect(size.height, greaterThanOrEqualTo(48));
    }
  }

  Finder semanticsContaining(String label) =>
      find.bySemanticsLabel(RegExp(RegExp.escape(label)));

  testWidgets('390px French navigation keeps every label visible and explicit', (
    tester,
  ) async {
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final semantics = tester.ensureSemantics();

    final router = await pumpNavigation(tester, locale: const Locale('fr'));
    addTearDown(router.dispose);

    final nav = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(nav.labelBehavior, NavigationDestinationLabelBehavior.alwaysShow);
    expect(nav.destinations, hasLength(5));
    expect(nav.selectedIndex, 0);

    for (final label in const [
      'Accueil',
      'IAmina',
      'Journal',
      'Importer',
      'Paramètres',
    ]) {
      expect(find.text(label), findsOneWidget);
      expect(semanticsContaining(label), findsWidgets);
    }

    expectTouchTargets(tester);

    await tester.tap(find.byKey(const ValueKey('mobile-nav-/importer')));
    await tester.pumpAndSettle();

    expect(router.routeInformationProvider.value.uri.path, '/importer');
    expect(tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex, 3);
    expect(find.text('route:/importer'), findsOneWidget);
    expect(tester.takeException(), isNull);
    semantics.dispose();
  });

  testWidgets('390px Arabic navigation is RTL, readable and route-aware', (
    tester,
  ) async {
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final semantics = tester.ensureSemantics();

    final router = await pumpNavigation(tester, locale: const Locale('ar'));
    addTearDown(router.dispose);

    final navFinder = find.byType(NavigationBar);
    expect(Directionality.of(tester.element(navFinder)), TextDirection.rtl);

    for (final label in const [
      'الرئيسية',
      'IAmina',
      'اليومية',
      'استيراد',
      'الإعدادات',
    ]) {
      expect(find.text(label), findsOneWidget);
      expect(semanticsContaining(label), findsWidgets);
    }

    expectTouchTargets(tester);

    await tester.tap(find.byKey(const ValueKey('mobile-nav-/journal')));
    await tester.pumpAndSettle();

    expect(router.routeInformationProvider.value.uri.path, '/journal');
    expect(tester.widget<NavigationBar>(navFinder).selectedIndex, 2);
    expect(find.text('route:/journal'), findsOneWidget);
    expect(tester.takeException(), isNull);
    semantics.dispose();
  });
}
