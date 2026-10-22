import 'package:amina/features/profile/profile_focus_safe_expansion_tile.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('D21: collapsed retained children cannot capture keyboard focus',
      (tester) async {
    final fieldFocus = FocusNode();
    addTearDown(fieldFocus.dispose);
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ProfileFocusSafeExpansionTile(
          title: const Text('Medical details'),
          subtitle: const Text('Synthetic only'),
          leading: const Icon(Icons.tune),
          initiallyExpanded: true,
          children: [
            TextField(focusNode: fieldFocus),
          ],
        ),
      ),
    ));
    await tester.pumpAndSettle();

    fieldFocus.requestFocus();
    await tester.pump();
    expect(fieldFocus.hasFocus, isTrue);
    expect(fieldFocus.canRequestFocus, isTrue);

    await tester.tap(find.text('Medical details'));
    await tester.pumpAndSettle();
    expect(fieldFocus.hasFocus, isFalse);
    expect(fieldFocus.canRequestFocus, isFalse);

    // A keyboard request must not activate an invisible retained input.
    fieldFocus.requestFocus();
    await tester.pump();
    expect(fieldFocus.hasFocus, isFalse);

    await tester.tap(find.text('Medical details'));
    await tester.pumpAndSettle();
    expect(fieldFocus.canRequestFocus, isTrue);
    fieldFocus.requestFocus();
    await tester.pump();
    expect(fieldFocus.hasFocus, isTrue);
  });

  testWidgets('D21: collapsed panel retains unsaved inputs', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ProfileFocusSafeExpansionTile(
          title: const Text('Iamina details'),
          subtitle: const Text('Synthetic form'),
          leading: const Icon(Icons.info_outline),
          initiallyExpanded: true,
          children: [TextFormField(initialValue: 'original')],
        ),
      ),
    ));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextFormField), 'unsaved synthetic');
    await tester.tap(find.text('Iamina details'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Iamina details'));
    await tester.pumpAndSettle();
    expect(find.text('unsaved synthetic'), findsOneWidget);
  });

  testWidgets('D21: initially collapsed retained controls are excluded',
      (tester) async {
    final focus = FocusNode();
    addTearDown(focus.dispose);
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ProfileFocusSafeExpansionTile(
          title: const Text('Privacy'),
          subtitle: const Text('Consent'),
          leading: const Icon(Icons.lock),
          initiallyExpanded: false,
          children: [TextField(focusNode: focus)],
        ),
      ),
    ));
    await tester.pumpAndSettle();
    expect(focus.canRequestFocus, isFalse);
    await tester.tap(find.text('Privacy'));
    await tester.pumpAndSettle();
    expect(focus.canRequestFocus, isTrue);
  });
}
