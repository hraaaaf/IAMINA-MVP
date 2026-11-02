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

  test('direct touch map is monotonic, bounded and reversible at references', () {
    final points = [40.0, 60, 70, 80, 90, 120, 160, 170, 180, 200, 320];
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
      'D22 premium direct semicircle editing, stepper and unit at $width',
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

        await tester.tap(find.byKey(const Key('glucose-half-dial-plus')));
        await tester.pump();
        expect(mgdl, 141);
        expect(controller.text, '141');

        await tester.tap(find.byKey(const Key('glucose-half-dial-minus')));
        await tester.pump();
        expect(mgdl, 140);

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
            const Duration(milliseconds: 500));
        await tester.pump();
        expect(mgdl, isNot(135));
        expect(mgdl, inInclusiveRange(40, 320));
        expect(double.parse(controller.text), mgdl);
        expect(tester.takeException(), isNull);
      },
    );
  }
}
