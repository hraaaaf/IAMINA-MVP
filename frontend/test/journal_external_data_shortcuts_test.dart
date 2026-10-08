import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/journal_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

bool _focusInside(WidgetTester tester, Finder target) {
  final targetElement = tester.element(target);
  Element? current = FocusManager.instance.primaryFocus?.context as Element?;
  while (current != null) {
    if (identical(current, targetElement)) return true;
    Element? parent;
    current.visitAncestorElements((ancestor) {
      parent = ancestor;
      return false;
    });
    current = parent;
  }
  return false;
}

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

      // Verify a real Tab traversal + Enter activation, not a second tap.
      router.pop();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 450));
      final importShortcut =
          find.byKey(const Key('journal-import-shortcut'));
      for (var tries = 0;
          tries < 40 && !_focusInside(tester, importShortcut);
          tries++) {
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pump();
      }
      expect(_focusInside(tester, importShortcut), isTrue);
      await tester.sendKeyEvent(LogicalKeyboardKey.enter);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('Import destination'), findsOneWidget);

      // Drain Drift QueryStream cancellation timers after route teardown, so
      // each locale test leaves a clean fake-async scheduler.
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump(const Duration(milliseconds: 20));
    });
  }

  // Increased font size must keep both actions legible, visible and tappable
  // without depending on a two-column compact layout.
  for (final locale in const [Locale('fr'), Locale('en'), Locale('ar')]) {
    for (final size in const [Size(390, 844), Size(360, 560)]) {
      for (final scale in const [1.3, 1.6]) {
    testWidgets('journal shortcuts at ${size.width.toInt()}x${size.height.toInt()} scale $scale in ${locale.languageCode}',
        (tester) async {
      tester.view.physicalSize = size;
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
            builder: (_, __) => const Scaffold(
              body: Center(child: Text('Import destination')),
            ),
          ),
          GoRoute(
            path: '/cgm',
            builder: (_, __) => const Scaffold(
              body: Center(child: Text('CGM destination')),
            ),
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
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context).copyWith(
                textScaler: TextScaler.linear(scale),
              ),
              child: child!,
            ),
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
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      final importButton = find.byKey(const Key('journal-import-shortcut'));
      final cgmButton = find.byKey(const Key('journal-cgm-shortcut'));
      expect(importButton, findsOneWidget);
      expect(cgmButton, findsOneWidget);
      final a = tester.getRect(importButton);
      final b = tester.getRect(cgmButton);
      for (final rect in [a, b]) {
        expect(rect.height, greaterThanOrEqualTo(48));
        expect(rect.left, greaterThanOrEqualTo(0));
        expect(rect.right, lessThanOrEqualTo(size.width));
        expect(rect.bottom, lessThanOrEqualTo(size.height));
      }
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump(const Duration(milliseconds: 20));
        });
      }
    }
  }
}
