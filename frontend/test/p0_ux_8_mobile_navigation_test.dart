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
                builder: (_, __) =>
                    Scaffold(body: Center(child: Text('route:$route'))),
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

  Finder destination(String route) => find.byKey(ValueKey('mobile-nav-$route'));

  void expectFiveDestinations() {
    for (final route in const [
      '/dashboard',
      '/summary',
      '/journal',
      '/importer',
      '/profile',
    ]) {
      expect(destination(route), findsOneWidget);
    }
  }

  void expectTouchTargets(WidgetTester tester) {
    for (final route in const [
      '/dashboard',
      '/summary',
      '/journal',
      '/importer',
      '/profile',
    ]) {
      final target = destination(route);
      final size = tester.getSize(target);
      expect(size.width, greaterThanOrEqualTo(48));
      expect(size.height, greaterThanOrEqualTo(48));
    }
  }

  Finder semanticsContaining(String label) =>
      find.bySemanticsLabel(RegExp(RegExp.escape(label)));

  testWidgets(
    '390px French navigation keeps every label visible and explicit',
    (tester) async {
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final semantics = tester.ensureSemantics();

      final router = await pumpNavigation(tester, locale: const Locale('fr'));
      addTearDown(router.dispose);

      expectFiveDestinations();
      expect(
        Directionality.of(tester.element(destination('/dashboard'))),
        TextDirection.ltr,
      );

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

      await tester.tap(destination('/importer'));
      await tester.pumpAndSettle();

      expect(router.routeInformationProvider.value.uri.path, '/importer');
      expect(find.text('route:/importer'), findsOneWidget);
      expectFiveDestinations();
      expect(tester.takeException(), isNull);
      semantics.dispose();
    },
  );

  testWidgets('390px Arabic navigation is RTL, readable and route-aware', (
    tester,
  ) async {
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final semantics = tester.ensureSemantics();

    final router = await pumpNavigation(tester, locale: const Locale('ar'));
    addTearDown(router.dispose);

    expectFiveDestinations();
    expect(
      Directionality.of(tester.element(destination('/dashboard'))),
      TextDirection.rtl,
    );

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

    await tester.tap(destination('/journal'));
    await tester.pumpAndSettle();

    expect(router.routeInformationProvider.value.uri.path, '/journal');
    expect(find.text('route:/journal'), findsOneWidget);
    expectFiveDestinations();
    expect(tester.takeException(), isNull);
    semantics.dispose();
  });
}
