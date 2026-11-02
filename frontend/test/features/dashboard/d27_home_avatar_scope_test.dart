import 'dart:io';

import 'package:amina/features/dashboard/dashboard_companion_entry_screen.dart';
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
      testWidgets('D27 draggable avatar routes Home to chat ${locale.languageCode} $size',
          (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final router = GoRouter(initialLocation: '/dashboard', routes: [
          GoRoute(
            path: '/dashboard',
            builder: (_, __) => const Scaffold(
              body: Stack(children: [
                Positioned.fill(child: DashboardCompanionAvatarAction()),
              ]),
            ),
          ),
          GoRoute(
            path: '/companion/chat',
            builder: (_, __) => const Scaffold(body: Text('IAMINA_CHAT_ROUTE')),
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
        final avatar = find.byKey(const ValueKey('dashboard-companion-chat-action'));
        expect(avatar, findsOneWidget);
        final fab = tester.widget<FloatingActionButton>(avatar);
        expect(fab.tooltip, locale.languageCode == 'ar'
            ? 'تحدث مع IAmina' : 'Parler avec IAmina');
        final image = tester.widget<Image>(find.byType(Image));
        expect((image.image as AssetImage).assetName,
            'assets/images/logo_amina.png');

        final before = tester.getTopLeft(avatar);
        final delta = locale.languageCode == 'ar'
            ? const Offset(140, -140)
            : const Offset(-140, -140);
        await tester.drag(avatar, delta);
        await tester.pumpAndSettle();
        final after = tester.getTopLeft(avatar);
        expect((after.dx - before.dx).abs(), greaterThan(50));
        expect(after.dy, lessThan(before.dy - 50));
        expect(after.dx, greaterThanOrEqualTo(12));
        expect(after.dy, greaterThanOrEqualTo(12));
        expect(tester.getBottomRight(avatar).dy,
            lessThanOrEqualTo(size.height - 104 + 0.1));
        expect(find.text('IAMINA_CHAT_ROUTE'), findsNothing,
            reason: 'Dragging must not accidentally send a chat navigation');
        expect(tester.takeException(), isNull);

        // WCAG 2.2 2.5.7: move by taps, not only by dragging.
        await tester.longPress(avatar);
        await tester.pumpAndSettle();
        final grid =
            find.byKey(const Key('dashboard-companion-position-grid'));
        expect(grid, findsOneWidget);
        await tester.tapAt(tester.getTopLeft(grid) + const Offset(28, 30));
        await tester.pumpAndSettle();
        expect(grid, findsNothing);
        expect(find.text('IAMINA_CHAT_ROUTE'), findsNothing);
        final selected = tester.getTopLeft(avatar);
        expect((selected.dx - after.dx).abs(), greaterThan(10));
        expect(selected.dx, greaterThanOrEqualTo(12));
        expect(selected.dy, greaterThanOrEqualTo(12));
        expect(tester.takeException(), isNull);

        await tester.tap(avatar);
        await tester.pumpAndSettle();
        expect(find.text('IAMINA_CHAT_ROUTE'), findsOneWidget);
        expect(avatar, findsNothing);
        expect(tester.takeException(), isNull);
      });
    }
  }

  test('D27 launcher is on Home only; local browser persistence is UI-only', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final home = File('lib/features/dashboard/dashboard_companion_entry_screen.dart')
        .readAsStringSync();
    final chat = File('lib/features/companion/companion_conversation_screen.dart')
        .readAsStringSync();
    final storage = File(
      'lib/features/dashboard/companion_fab_position_web.dart',
    ).readAsStringSync();
    expect(module, contains('builder: () => const DashboardCompanionEntryScreen()'));
    expect(module, contains("path: '/companion/chat'"));
    expect(home.split('DashboardCompanionAvatarAction(').length - 1, 2);
    expect(home, contains('onPanUpdate:'));
    expect(home, contains('onPanEnd:'));
    expect(home, contains('CallbackShortcuts('));
    expect(home, contains('LogicalKeyboardKey.arrowLeft'));
    expect(home, contains('onLongPress: _showPositionPicker'));
    expect(home, contains('customSemanticsActions:'));
    expect(home, contains('104'));
    expect(storage, contains('window.localStorage'));
    expect(storage, contains('iamina.d27.fab.position.v1'));
    expect(chat, isNot(contains('DashboardCompanionAvatarAction')));
    expect(chat, contains("tag: 'dashboard-companion-chat-action'"));
    expect(chat, isNot(contains('FloatingActionButton.small(')));
  });
}
