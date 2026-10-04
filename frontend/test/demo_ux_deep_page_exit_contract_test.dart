import 'dart:io';

import 'package:amina/core/widgets/mobile_page_header.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<GoRouter> pumpExitHarness(
    WidgetTester tester, {
    required String initialLocation,
  }) async {
    final router = GoRouter(
      initialLocation: initialLocation,
      routes: [
        GoRoute(
          path: '/dashboard',
          builder: (_, __) => const Scaffold(body: Text('dashboard')),
        ),
        GoRoute(
          path: '/deep',
          builder: (_, __) => const Scaffold(
            body: Center(child: AminaPageExitButton()),
          ),
        ),
      ],
    );
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.pumpAndSettle();
    return router;
  }

  testWidgets('canonical page exit falls back to dashboard on direct entry', (
    tester,
  ) async {
    final router = await pumpExitHarness(tester, initialLocation: '/deep');
    addTearDown(router.dispose);

    await tester.tap(find.byKey(const ValueKey('amina-page-exit')));
    await tester.pumpAndSettle();

    expect(router.routeInformationProvider.value.uri.path, '/dashboard');
  });

  testWidgets('canonical page exit pops when navigation history exists', (
    tester,
  ) async {
    final router = await pumpExitHarness(tester, initialLocation: '/dashboard');
    addTearDown(router.dispose);

    router.push('/deep');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('amina-page-exit')));
    await tester.pumpAndSettle();

    expect(router.routeInformationProvider.value.uri.path, '/dashboard');
  });

  test('all deep utility pages expose the canonical exit control', () {
    for (final path in <String>[
      'lib/features/import/import_screen.dart',
      'lib/features/reminders/reminders_screen.dart',
      'lib/features/medications/medication_screen.dart',
      'lib/features/import/cgm_screen.dart',
      'lib/features/documents/document_import_screen.dart',
      'lib/features/documents/document_import_premium_screen.dart',
      'lib/features/journal/add_log_screen.dart',
      'lib/features/journal/edit_log_screen.dart',
    ]) {
      expect(
        File(path).readAsStringSync(),
        contains('AminaPageExitButton'),
        reason: path,
      );
    }
  });

  test('companion close buttons have a dashboard fallback', () {
    for (final path in <String>[
      'lib/features/companion/companion_premium_screen_presentation.dart',
      'lib/features/companion/companion_conversation_screen.dart',
    ]) {
      final source = File(path).readAsStringSync();
      expect(source, contains('router.canPop()'), reason: path);
      expect(source, contains("router.go('/dashboard')"), reason: path);
    }
  });
}
