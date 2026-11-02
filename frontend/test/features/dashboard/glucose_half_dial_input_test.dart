import 'package:amina/features/dashboard/widgets/glucose_half_dial_input.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('illustrative range colors are red on BOTH outside edges', () {
    const red = Color(0xFFD84752);
    const amber = Color(0xFFF1A34B);
    const green = Color(0xFF27A87D);
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

  for (final width in <double>[390, 768, 1280]) {
    testWidgets('new measurement half dial and unit toggle on $width', (tester) async {
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
                mgdl = raw == null ? null : (unit == 'mmol/L' ? raw * 18.0 : raw);
              }),
              onValueSelected: (value) => set(() {
                mgdl = value;
                controller.text = unit == 'mmol/L'
                    ? (value / 18.0).toStringAsFixed(1)
                    : value.toStringAsFixed(0);
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
      expect(find.byKey(const Key('glucose-half-dial-slider')), findsOneWidget);
      expect(find.byKey(const Key('glucose-half-dial-guide-note')), findsOneWidget);

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

      await tester.drag(
        find.byKey(const Key('glucose-half-dial-slider')),
        const Offset(-65, 0),
      );
      await tester.pump();
      expect(mgdl, isNot(140));
      expect(double.parse(controller.text), mgdl);
      expect(tester.takeException(), isNull);
    });
  }
}
