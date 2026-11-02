import 'dart:io';

import 'package:amina/features/dashboard/dashboard_companion_entry_screen.dart';
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
      testWidgets('D27 branded avatar routes Home to chat ${locale.languageCode} $size',
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
                PositionedDirectional(
                  end: 20,
                  bottom: 104,
                  child: DashboardCompanionAvatarAction(),
                ),
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
        expect(tester.takeException(), isNull);
        await tester.tap(avatar);
        await tester.pumpAndSettle();
        expect(find.text('IAMINA_CHAT_ROUTE'), findsOneWidget);
        expect(avatar, findsNothing);
        expect(tester.takeException(), isNull);
      });
    }
  }

  test('D27 only wires the floating avatar into the actual Home shell route', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final home = File('lib/features/dashboard/dashboard_companion_entry_screen.dart')
        .readAsStringSync();
    final chat = File('lib/features/companion/companion_conversation_screen.dart')
        .readAsStringSync();
    expect(module, contains('builder: () => const DashboardCompanionEntryScreen()'));
    expect(module, contains("path: '/companion/chat'"));
    expect(home.split('DashboardCompanionAvatarAction(').length - 1, 2);
    expect(chat, isNot(contains('DashboardCompanionAvatarAction')));
    expect(chat, isNot(contains('dashboard-companion-chat-action')));
  });
}
