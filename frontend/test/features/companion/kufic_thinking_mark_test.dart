import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Arabic Kufic mark separates then rejoins without changing the asset', (
    tester,
  ) async {
    final motion = AnimationController(
      vsync: tester,
      duration: const Duration(milliseconds: 1600),
    );
    addTearDown(motion.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: KuficThinkingMark(animation: motion, staticMark: false),
        ),
      ),
    );
    final first = find.byKey(const Key('companion-kufic-segment-0'));
    final last = find.byKey(const Key('companion-kufic-segment-3'));
    double x(Finder finder) =>
        tester.widget<Transform>(finder).transform.getTranslation().x;

    expect(find.byKey(const Key('companion-kufic-thinking')), findsOneWidget);
    expect(first, findsOneWidget);
    expect(last, findsOneWidget);
    expect(x(first), closeTo(0, 0.001));

    motion.value = 0.5;
    await tester.pump();
    expect(x(first), closeTo(-2, 0.001));
    expect(x(last), closeTo(2, 0.001));

    motion.value = 1;
    await tester.pump();
    expect(x(first), closeTo(0, 0.001));
    expect(x(last), closeTo(0, 0.001));
    expect(tester.takeException(), isNull);
  });

  testWidgets('reduced-motion or voice-processing mode uses one static mark', (
    tester,
  ) async {
    final motion = AnimationController(vsync: tester);
    addTearDown(motion.dispose);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: KuficThinkingMark(animation: motion, staticMark: true),
        ),
      ),
    );
    expect(find.byKey(const Key('companion-kufic-static')), findsOneWidget);
    expect(find.byKey(const Key('companion-kufic-thinking')), findsNothing);
    expect(find.byKey(const Key('companion-kufic-segment-0')), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
