import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/journal_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

void main() {
  for (final locale in const [Locale('fr'), Locale('en'), Locale('ar')]) {
    testWidgets('journal import and CGM shortcuts navigate in ${locale.languageCode}',
        (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      final router = GoRouter(
        initialLocation: '/journal',
        routes: [
          GoRoute(path: '/journal', builder: (_, __) => const JournalScreen()),
          GoRoute(
            path: '/importer',
            builder: (_, __) =>
                const Scaffold(body: Center(child: Text('Import destination'))),
          ),
          GoRoute(
            path: '/cgm',
            builder: (_, __) =>
                const Scaffold(body: Center(child: Text('CGM destination'))),
          ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            StreamProvider<PatientProfileData?>(
              create: (_) => db.watchProfile(),
              initialData: null,
            ),
          ],
          child: MaterialApp.router(
            locale: locale,
            supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
            localizationsDelegates: const [
              AppLocalizations.delegate,
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            routerConfig: router,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('journal-import-shortcut')), findsOneWidget);
      expect(find.byKey(const Key('journal-cgm-shortcut')), findsOneWidget);
      expect(tester.getRect(find.byKey(const Key('journal-import-shortcut'))).height,
          greaterThanOrEqualTo(44));
      expect(tester.takeException(), isNull);

      await tester.tap(find.byKey(const Key('journal-import-shortcut')));
      await tester.pumpAndSettle();
      expect(find.text('Import destination'), findsOneWidget);

      router.go('/journal');
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('journal-cgm-shortcut')));
      await tester.pumpAndSettle();
      expect(find.text('CGM destination'), findsOneWidget);
    });
  }
}
