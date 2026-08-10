from pathlib import Path

shell_path = Path('frontend/lib/features/navigation/main_shell.dart')
shell = shell_path.read_text()
old_padding = "minimum: const EdgeInsets.fromLTRB(12, 0, 12, 10),"
new_padding = "minimum: EdgeInsets.symmetric(horizontal: 12).copyWith(bottom: 10),"
if old_padding not in shell:
    raise SystemExit('UX5 expected SafeArea minimum not found')
shell = shell.replace(old_padding, new_padding, 1)
shell_path.write_text(shell)

Path('frontend/test/p0_ux_8_mobile_navigation_test.dart').write_text(r'''import 'package:amina/features/navigation/main_shell.dart';
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

  testWidgets('390px French navigation keeps every label visible and explicit', (
    tester,
  ) async {
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
  });

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
''')

real_actions_path = Path('frontend/test/p0_real_actions_contract_test.dart')
real_actions = real_actions_path.read_text()
old_real = """    expect(RegExp(r'for \\(final \\w+ in entries\\)').hasMatch(shell), isTrue);\n    expect(shell, contains('NavigationDestination('));\n    expect(shell, contains('onDestinationSelected:'));\n    expect(shell, contains('GoRouter.of(context).go(entries[index].route)'));"""
new_real = """    expect(shell, contains('for (var index = 0; index < entries.length; index++)'));\n    expect(shell, contains('_GlassNavDestination('));\n    expect(shell, contains('entry: entries[index]'));\n    expect(shell, contains(\"ValueKey('mobile-nav-\\${entry.route}')\"));\n    expect(shell, contains('GoRouter.of(context).go(entries[index].route)'));"""
if old_real not in real_actions:
    raise SystemExit('legacy real-actions navigation contract not found')
real_actions_path.write_text(real_actions.replace(old_real, new_real, 1))

rtl_access_path = Path('frontend/test/p0_ux_6_4_rtl_accessibility_contract_test.dart')
rtl_access = rtl_access_path.read_text()
old_labels = """  test('mobile navigation labels remain permanently visible', () {\n    expect(\n      source,\n      contains('NavigationDestinationLabelBehavior.alwaysShow'),\n    );\n    expect(\n      source,\n      isNot(contains('NavigationDestinationLabelBehavior.onlyShowSelected')),\n    );\n  });"""
new_labels = """  test('mobile navigation labels remain permanently visible', () {\n    expect(source, contains('class _GlassNavDestination'));\n    expect(source, contains('final label = entry.label(AppLocalizations.of(context)!);'));\n    expect(source, contains('child: Text('));\n    expect(source, contains('maxLines: 1'));\n    expect(source, isNot(contains('NavigationDestinationLabelBehavior.onlyShowSelected')));\n  });"""
if old_labels not in rtl_access:
    raise SystemExit('legacy always-show navigation contract not found')
rtl_access_path.write_text(rtl_access.replace(old_labels, new_labels, 1))
