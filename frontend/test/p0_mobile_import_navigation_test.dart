import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/dashboard_convergent_screen.dart';
import 'package:amina/features/documents/document_import_screen.dart';
import 'package:amina/features/import/import_screen.dart';
import 'package:amina/features/navigation/main_shell.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/modules_provider.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    '390px user can navigate to Importer and open the document review flow',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      final api = ApiClient(baseUrl: 'http://127.0.0.1:1');
      final modules = ModulesProvider(api);
      addTearDown(db.close);

      final router = GoRouter(
        initialLocation: '/dashboard',
        routes: [
          GoRoute(
            path: '/pulper',
            builder: (_, __) => const DocumentImportScreen(),
          ),
          ShellRoute(
            builder: (_, __, child) => MainShell(child: child),
            routes: [
              GoRoute(
                path: '/dashboard',
                builder: (_, __) => const DashboardConvergentScreen(),
              ),
              GoRoute(
                path: '/importer',
                builder: (_, __) => const ImportScreen(),
              ),
            ],
          ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            Provider<ApiClient>.value(value: api),
            ChangeNotifierProvider<ModulesProvider>.value(value: modules),
          ],
          child: MaterialApp.router(
            routerConfig: router,
            locale: const Locale('fr'),
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
          ),
        ),
      );
      await tester.pumpAndSettle();

      final importerAction = find.byKey(
        const ValueKey('dashboard-import-action'),
      );
      expect(importerAction, findsOneWidget);
      expect(find.byKey(const ValueKey('mobile-nav-/importer')), findsNothing);
      expect(tester.takeException(), isNull);

      await tester.tap(importerAction);
      await tester.pumpAndSettle();

      expect(find.byType(ImportScreen), findsOneWidget);
      expect(find.text('Importer'), findsWidgets);
      final firstUse = find.byKey(const ValueKey('import-first-use'));
      final populatedCta = find.byKey(const ValueKey('import-document-cta'));
      expect(firstUse.evaluate().length + populatedCta.evaluate().length, 1);
      expect(tester.takeException(), isNull);

      if (firstUse.evaluate().isNotEmpty) {
        final firstUseAction = find.descendant(
          of: firstUse,
          matching: find.byType(FilledButton),
        );
        expect(firstUseAction, findsOneWidget);
        await tester.tap(firstUseAction);
      } else {
        await tester.tap(populatedCta);
      }
      await tester.pumpAndSettle();

      expect(find.byType(DocumentImportScreen), findsOneWidget);
      expect(find.text('Importer un document'), findsOneWidget);
      expect(
        find.byKey(const ValueKey('choose-document-button')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('document picker remains usable on a short mobile viewport', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 560);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      Provider<ApiClient>.value(
        value: ApiClient(baseUrl: 'http://127.0.0.1:1'),
        child: MaterialApp(
          locale: const Locale('fr'),
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: const DocumentImportScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('document-import-pick-scroll')),
      findsOneWidget,
    );
    await tester.scrollUntilVisible(
      find.byKey(const ValueKey('choose-document-button')),
      120,
      scrollable: find.byType(Scrollable).first,
    );
    expect(
      find.byKey(const ValueKey('choose-document-button')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}
