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
        // D27 finger ergonomics: full 56px target, not a 40px mini FAB.
        expect(tester.getSize(avatar), const Size(56, 56));
        final fab = tester.widget<FloatingActionButton>(avatar);
        // FAB.tooltip installs a competing long-press recognizer and would
        // block the accessible position picker; use explicit Semantics instead.
        expect(fab.tooltip, isNull);
        // The approved brain icon must stand alone: no circular FAB or shadow.
        expect(fab.backgroundColor, Colors.transparent);
        expect(fab.elevation, 0);
        expect(fab.focusElevation, 0);
        expect(fab.hoverElevation, 0);
        expect(fab.highlightElevation, 0);
        expect(fab.child, isA<SizedBox>());
        expect(
          find.byWidgetPredicate(
            (widget) => widget is Semantics &&
                widget.properties.label ==
                    (locale.languageCode == 'ar'
                        ? 'تحدث مع IAmina'
                        : 'Parler avec IAmina'),
          ),
          findsOneWidget,
        );
        final image = tester.widget<Image>(find.byType(Image));
        expect((image.image as AssetImage).assetName,
            'assets/images/iamina_chatbrain_diabetes.png');
        expect(image.color, isNull,
            reason: 'Tinting the solid RGBA bubble would hide the brain lines');

        // Before any upward movement there must be room to move DOWN too.
        final initial = tester.getTopLeft(avatar);
        await tester.drag(avatar, const Offset(0, 48));
        await tester.pumpAndSettle();
        final lowered = tester.getTopLeft(avatar);
        expect(lowered.dy - initial.dy, closeTo(48, 2));
        expect(find.text('IAMINA_CHAT_ROUTE'), findsNothing);

        final before = tester.getTopLeft(avatar);
        final delta = locale.languageCode == 'ar'
            ? const Offset(140, -140)
            : const Offset(-140, -140);
        await tester.drag(avatar, delta);
        await tester.pumpAndSettle();
        final after = tester.getTopLeft(avatar);
        // A 140px finger movement must produce 140px of button travel.
        expect(after.dx - before.dx, closeTo(delta.dx, 2));
        expect(after.dy - before.dy, closeTo(delta.dy, 2));
        expect(after.dx, greaterThanOrEqualTo(12));
        expect(after.dy, greaterThanOrEqualTo(12));
        expect(tester.getBottomRight(avatar).dy,
            lessThanOrEqualTo(size.height - 12 + 0.1));
        expect(find.text('IAMINA_CHAT_ROUTE'), findsNothing,
            reason: 'Dragging must not accidentally send a chat navigation');
        expect(tester.takeException(), isNull);

        // One continuous finger gesture must follow all four circular segments
        // without losing movement when the floating widget rebuilds.
        final finger = await tester.startGesture(tester.getCenter(avatar));
        var expected = after;
        for (final step in const <Offset>[
          Offset(42, -34),
          Offset(38, 34),
          Offset(-38, 34),
          Offset(-42, -34),
        ]) {
          await finger.moveBy(step);
          await tester.pump();
          expected += step;
          final actual = tester.getTopLeft(avatar);
          expect(actual.dx, closeTo(expected.dx, 3));
          expect(actual.dy, closeTo(expected.dy, 3));
        }
        await finger.up();
        await tester.pumpAndSettle();
        expect(tester.getTopLeft(avatar).dx, closeTo(after.dx, 3));
        expect(tester.getTopLeft(avatar).dy, closeTo(after.dy, 3));
        expect(find.text('IAMINA_CHAT_ROUTE'), findsNothing);

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

  testWidgets(
    'D27 mobile shell: avatar reaches 12px above the real bottom nav',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      // MainShell owns the bottomNavigationBar; the avatar is inside body.
      // A second 104px clearance would leave an artificial dead zone.
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(
          body: DashboardCompanionAvatarAction(),
          bottomNavigationBar: SizedBox(
            height: 104,
            child: ColoredBox(
              key: Key('d27-shell-bottom-nav'),
              color: Colors.white,
            ),
          ),
        ),
      ));
      await tester.pumpAndSettle();

      final avatar =
          find.byKey(const ValueKey('dashboard-companion-chat-action'));
      final dock = find.byKey(const Key('d27-shell-bottom-nav'));
      final dockTop = tester.getTopLeft(dock).dy;
      expect(tester.getBottomRight(avatar).dy, lessThan(dockTop - 12));

      await tester.drag(avatar, const Offset(0, 500));
      await tester.pumpAndSettle();

      // No invisible 104px dead zone, and no overlap with the navigation.
      expect(tester.getBottomRight(avatar).dy, closeTo(dockTop - 12, 1));
      expect(tester.getTopLeft(avatar).dy, greaterThan(12));
      expect(tester.takeException(), isNull);
    },
  );

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
    expect(home, contains('followFinger(details.globalPosition)'));
    expect(home, contains('_diameter = 56'));
    expect(home, contains('onPanEnd:'));
    expect(home, contains('CallbackShortcuts('));
    expect(home, contains('LogicalKeyboardKey.arrowLeft'));
    expect(home, contains('onLongPress: _showPositionPicker'));
    expect(home, contains('customSemanticsActions:'));
    expect(home, contains('_bottomEdge = 12'));
    expect(home, isNot(contains('_dockClearance = 104')));
    expect(storage, contains('window.localStorage'));
    expect(storage, contains('iamina.d27.fab.position.v1'));
    expect(chat, isNot(contains('DashboardCompanionAvatarAction')));
    expect(chat, contains("tag: 'dashboard-companion-chat-action'"));
    expect(chat, isNot(contains('FloatingActionButton.small(')));
  });
}
