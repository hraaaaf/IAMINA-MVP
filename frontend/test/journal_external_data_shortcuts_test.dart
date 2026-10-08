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
      // Journal may show a repeating loading shimmer while Drift emits its
      // initial stream value. Do not wait for animations to settle forever.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.byKey(const Key('journal-import-shortcut')), findsOneWidget);
      expect(find.byKey(const Key('journal-cgm-shortcut')), findsOneWidget);
      final importRect = tester.getRect(
        find.byKey(const Key('journal-import-shortcut')),
      );
      final cgmRect = tester.getRect(
        find.byKey(const Key('journal-cgm-shortcut')),
      );
      expect(importRect.height, greaterThanOrEqualTo(48));
      expect(cgmRect.height, greaterThanOrEqualTo(48));
      // Standard 390px mobile fits both shortcuts on a single row.
      expect((importRect.top - cgmRect.top).abs(), lessThan(4));
      expect(tester.takeException(), isNull);

      await tester.tap(find.byKey(const Key('journal-import-shortcut')));
      // Journal may show a repeating loading shimmer while Drift emits its
      // initial stream value. Do not wait for animations to settle forever.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('Import destination'), findsOneWidget);

      // Return through the same imperative stack used by context.push.
      // router.go() can leave the old page's outgoing overlay hit-testing
      // above Journal while the transition is still in flight.
      router.pop();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 450));
      expect(find.text('Import destination'), findsNothing);
      await tester.tap(find.byKey(const Key('journal-cgm-shortcut')));
      // Journal may show a repeating loading shimmer while Drift emits its
      // initial stream value. Do not wait for animations to settle forever.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('CGM destination'), findsOneWidget);

      // Drain Drift QueryStream cancellation timers after route teardown, so
      // each locale test leaves a clean fake-async scheduler.
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump(const Duration(milliseconds: 20));
    });
  }
}
