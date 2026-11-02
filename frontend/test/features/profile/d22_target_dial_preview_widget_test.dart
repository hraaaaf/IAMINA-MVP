import 'package:amina/features/profile/d22_target_dial_preview.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// D22-B preview UX only: neither a prescribed target nor persistent data.
void main() {
  testWidgets('semicircle preview has controls and a nonclinical warning',
      (tester) async {
    String unit = 'mg/dL';
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(body: StatefulBuilder(
        builder: (context, set) => SingleChildScrollView(
          child: D22TargetDialPreview(
            unit: unit,
            onUnitChanged: (v) => set(() => unit = v),
          ),
        ),
      )),
    ));
    expect(find.byKey(const Key('d22-dial-preview')), findsOneWidget);
    expect(find.byKey(const Key('d22-dial-arc')), findsOneWidget);
    expect(find.byKey(const Key('d22-dial-accessible-slider')), findsOneWidget);
    expect(find.byKey(const Key('d22-dial-select-min')), findsOneWidget);
    expect(find.byKey(const Key('d22-dial-select-max')), findsOneWidget);
    expect(find.textContaining('not saved'), findsOneWidget);

    await tester.tap(find.byKey(const Key('d22-dial-unit-toggle')));
    await tester.pumpAndSettle();
    expect(unit, 'mmol/L');
    expect(find.textContaining('mmol/L'), findsWidgets);

    await tester.tap(find.byKey(const Key('d22-dial-select-max')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Maximum'), findsWidgets);
    final before = tester.widget<Text>(
      find.byKey(const Key('d22-dial-active-value')),
    ).data;
    await tester.drag(find.byKey(const Key('d22-dial-accessible-slider')),
        const Offset(-80, 0));
    await tester.pumpAndSettle();
    final after = tester.widget<Text>(
      find.byKey(const Key('d22-dial-active-value')),
    ).data;
    expect(after, isNot(before));
  });
}
