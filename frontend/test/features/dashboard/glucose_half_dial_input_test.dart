import 'dart:math' as math;

import 'package:amina/features/dashboard/widgets/glucose_half_dial_input.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('nonpersonalized color bands stay RED / AMBER / GREEN / AMBER / RED', () {
    const red = Color(0xFFCF475A);
    const amber = Color(0xFFF0A447);
    const green = Color(0xFF18A781);
    expect(d22IllustrativeGlucoseArcColor(55), red);
    expect(d22IllustrativeGlucoseArcColor(69), red);
    expect(d22IllustrativeGlucoseArcColor(70), amber);
    expect(d22IllustrativeGlucoseArcColor(89), amber);
    expect(d22IllustrativeGlucoseArcColor(100), green);
    expect(d22IllustrativeGlucoseArcColor(160), green);
    expect(d22IllustrativeGlucoseArcColor(165), amber);
    expect(d22IllustrativeGlucoseArcColor(180), amber);
    expect(d22IllustrativeGlucoseArcColor(181), red);
    expect(d22IllustrativeGlucoseArcColor(250), red);
  });

  test('ambient accent is continuous and mirrors BOTH red ends', () {
    const red = Color(0xFFE36462);
    const orange = Color(0xFFE9A348);
    const green = Color(0xFF23A881);
    expect(d22GlucoseDialAmbientColor(null), const Color(0xFF198C78));
    expect(d22GlucoseDialAmbientColor(40), red);
    expect(d22GlucoseDialAmbientColor(60), red);
    expect(d22GlucoseDialAmbientColor(82), orange);
    expect(d22GlucoseDialAmbientColor(105), green);
    expect(d22GlucoseDialAmbientColor(125), green);
    expect(d22GlucoseDialAmbientColor(168), orange);
    expect(d22GlucoseDialAmbientColor(187), red);
    expect(d22GlucoseDialAmbientColor(250), red);
    expect(d22GlucoseDialAmbientColor(75), isNot(red));
    expect(d22GlucoseDialAmbientColor(75), isNot(orange));
    expect(d22GlucoseDialAmbientColor(175), isNot(orange));
    expect(d22GlucoseDialAmbientColor(175), isNot(red));
    expect(d22GlucoseDialAmbientColor(69),
        isNot(d22GlucoseDialAmbientColor(72)));
    expect(d22GlucoseDialAmbientColor(179),
        isNot(d22GlucoseDialAmbientColor(184)));
  });

  test('visual zone labels cover both ends without defining targets', () {
    expect(d22GlucoseDialVisualZone(null), isNull);
    expect(d22GlucoseDialVisualZone(55), D22GlucoseDialVisualZone.lowRed);
    expect(d22GlucoseDialVisualZone(80), D22GlucoseDialVisualZone.lowAmber);
    expect(d22GlucoseDialVisualZone(140),
        D22GlucoseDialVisualZone.centerGreen);
    expect(d22GlucoseDialVisualZone(170),
        D22GlucoseDialVisualZone.highAmber);
    expect(d22GlucoseDialVisualZone(200),
        D22GlucoseDialVisualZone.highRed);
    expect(d22GlucoseDialVisualZone(double.nan), isNull);
  });

  test('direct touch map is monotonic, bounded and reversible at references', () {
    final points = <double>[40, 60, 70, 80, 90, 120, 160, 170, 180, 200, 320];
    var last = -1.0;
    for (final value in points) {
      final position = d22DialFractionForMgdl(value);
      expect(position, greaterThan(last));
      expect(position, inInclusiveRange(0, 1));
      expect(d22DialMgdlForFraction(position), closeTo(value, .00001));
      last = position;
    }
    // Expanded central band must remain symmetric and the red band short.
    expect(d22DialFractionForMgdl(90), closeTo(.29, .00001));
    expect(d22DialFractionForMgdl(160), closeTo(.71, .00001));
    expect(d22DialMgdlForFraction(-1), 40);
    expect(d22DialMgdlForFraction(2), 320);
  });

  for (final width in <double>[390, 768, 1280]) {
    testWidgets(
      'D22 clean direct semicircle editing, touch and unit at $width',
      (tester) async {
        tester.view.physicalSize = Size(width, 844);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final controller = TextEditingController(text: '140');
        addTearDown(controller.dispose);
        String unit = 'mg/dL';
        double? mgdl = 140;

        await tester.pumpWidget(MaterialApp(
          home: Scaffold(body: StatefulBuilder(
            builder: (context, set) => SingleChildScrollView(
              child: GlucoseHalfDialInput(
                controller: controller,
                unit: unit,
                valueMgdl: mgdl,
                onTextChanged: (value) => set(() {
                  final raw = double.tryParse(value.replaceAll(',', '.'));
                  mgdl = raw == null ? null :
                      (unit == 'mmol/L' ? raw * 18.0 : raw);
                }),
                onValueSelected: (value) => set(() {
                  mgdl = value;
                  controller.value = TextEditingValue(
                    text: unit == 'mmol/L'
                        ? (value / 18.0).toStringAsFixed(1)
                        : value.round().toString(),
                    selection: const TextSelection.collapsed(offset: 0),
                  );
                }),
                onToggleUnit: () => set(() {
                  unit = unit == 'mg/dL' ? 'mmol/L' : 'mg/dL';
                  controller.text = unit == 'mg/dL'
                      ? mgdl!.round().toString()
                      : (mgdl! / 18.0).toStringAsFixed(1);
                }),
              ),
            ),
          )),
        ));

        expect(find.byKey(const Key('glucose-half-dial-input')), findsOneWidget);
        expect(find.byKey(const Key('glucose-half-dial-arc')), findsOneWidget);
        expect(find.byKey(const Key('glucose-input')), findsOneWidget);
        expect(find.byKey(const Key('glucose-half-dial-edit-center')), findsOneWidget);
        expect(find.byKey(const Key('glucose-half-dial-slider')), findsNothing);
        expect(find.byKey(const Key('glucose-half-dial-guide-note')), findsOneWidget);
        expect(tester.takeException(), isNull);

        // UX3: no plus or minus controls remain. The center input and arc
        // are the only primary entry surfaces.
        expect(find.byKey(const Key('glucose-half-dial-plus')), findsNothing);
        expect(find.byKey(const Key('glucose-half-dial-minus')), findsNothing);
        expect(find.byKey(const Key('glucose-half-dial-slider')), findsNothing);

        await tester.tap(find.byKey(const Key('glucose-half-dial-unit-toggle')));
        await tester.pump();
        expect(unit, 'mmol/L');
        expect(controller.text, '7.8');
        expect(mgdl, 140);

        await tester.tap(find.byKey(const Key('glucose-half-dial-unit-toggle')));
        await tester.pump();
        expect(unit, 'mg/dL');
        expect(controller.text, '140');
        expect(mgdl, 140);

        // Precision keyboard remains directly inside the colored semicircle.
        await tester.enterText(find.byKey(const Key('glucose-input')), '135');
        await tester.pump();
        expect(controller.text, '135');
        expect(mgdl, 135);

        // Drag the colored arc itself: no separate horizontal slider.
        final dial = find.byKey(const Key('glucose-half-dial-touch-surface'));
        final bounds = tester.getRect(dial);
        final center = Offset(bounds.center.dx, bounds.bottom - 18);
        final radius = (bounds.width / 2 - 30) < (bounds.height - 35)
            ? bounds.width / 2 - 30 : bounds.height - 35;
        final first = Offset(center.dx - radius, center.dy);
        final second = Offset(center.dx, center.dy - radius);
        await tester.timedDragFrom(first, second - first,
            const Duration(milliseconds: 250));
        await tester.pump();
        expect(mgdl, isNot(135));
        expect(mgdl, inInclusiveRange(40, 320));
        expect(double.parse(controller.text), mgdl);

        // UX3 regression: a finger starting ~50px INSIDE the visual ring
        // must still grab the selection. The previous 34px annulus missed it.
        final generousStart = Offset(center.dx - radius + 53, center.dy - 16);
        final generousEnd = Offset(center.dx, center.dy - radius + 35);
        await tester.timedDragFrom(generousStart,
            generousEnd - generousStart, const Duration(milliseconds: 170));
        await tester.pump();
        expect(mgdl, inInclusiveRange(40, 320));
        expect(double.parse(controller.text), mgdl);
        // Numeric input remains active and independent from arc gestures.
        await tester.enterText(find.byKey(const Key('glucose-input')), '123');
        await tester.pump();
        expect(controller.text, '123');
        expect(mgdl, 123);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('iPhone vertical swipe on arc edits value WITHOUT scrolling page',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = TextEditingController(text: '140');
    addTearDown(controller.dispose);
    double reading = 140;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          key: const Key('d22-scroll-parent'),
          child: Column(children: [
            const SizedBox(key: Key('d22-outside-dial'), height: 170),
            StatefulBuilder(builder: (context, set) => GlucoseHalfDialInput(
              controller: controller,
              unit: 'mg/dL',
              valueMgdl: reading,
              onTextChanged: (_) {},
              onValueSelected: (v) => set(() {
                reading = v;
                controller.text = v.round().toString();
              }),
              onToggleUnit: () {},
            )),
            const SizedBox(height: 1200),
          ]),
        ),
      ),
    ));

    final page = tester.state<ScrollableState>(
      find.descendant(
        of: find.byKey(const Key('d22-scroll-parent')),
        matching: find.byType(Scrollable),
      ).first,
    );
    expect(page.position.pixels, 0);
    final dial = tester.getRect(
        find.byKey(const Key('glucose-half-dial-touch-surface')));
    final center = Offset(dial.center.dx, dial.bottom - 18);
    final radius = math.min(dial.width / 2 - 30, dial.height - 35);
    // A predominantly VERTICAL swipe that used to make iOS Safari scroll
    // the enclosing page instead of tracking the finger along the arc.
    final start = Offset(center.dx - radius * .88,
        center.dy - radius * .13);
    await tester.timedDragFrom(start, const Offset(0, -110),
        const Duration(milliseconds: 260));
    await tester.pumpAndSettle();
    expect(page.position.pixels, closeTo(0, .1),
        reason: 'The arc must win the parent ScrollView gesture arena');
    expect(reading, isNot(140));
    expect(double.parse(controller.text), reading);

    // Scrolling from OUTSIDE the dial must still work normally.
    await tester.drag(
        find.byKey(const Key('d22-outside-dial')),
        const Offset(0, -140));
    await tester.pumpAndSettle();
    expect(page.position.pixels, greaterThan(30));
    expect(tester.takeException(), isNull);
  });
}
