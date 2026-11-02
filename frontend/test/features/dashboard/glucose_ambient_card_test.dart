import 'package:amina/features/dashboard/widgets/add_log_view.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Visual-state regression: validates the REAL glucose entry card, not just
/// its pure palette helper. The colors are illustrative, not prescriptions.
void main() {
  testWidgets('entry card tints smoothly on BOTH extremes and central band',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final controller = TextEditingController(text: '40');
    addTearDown(controller.dispose);
    var glucose = 40.0;
    late StateSetter change;

    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(
        body: SingleChildScrollView(
          child: StatefulBuilder(builder: (context, set) {
            change = set;
            return AddLogGlucoseCard(
              controller: controller,
              unit: 'mg/dL',
              mgdl: glucose,
              onChanged: (_) {},
              onValueSelected: (_) {},
              onToggleUnit: () {},
            );
          }),
        ),
      ),
    ));

    Color cardColor() {
      final widget = tester.widget<AnimatedContainer>(
        find.byKey(const Key('glucose-glass-card')),
      );
      return (widget.decoration! as BoxDecoration).color!;
    }

    Color cardBorder() {
      final widget = tester.widget<AnimatedContainer>(
        find.byKey(const Key('glucose-glass-card')),
      );
      return ((widget.decoration! as BoxDecoration).border! as Border)
          .top.color;
    }

    final lowColor = cardColor();
    final lowBorder = cardBorder();
    expect(find.byKey(const Key('glucose-ambient-zone-message')), findsOneWidget);
    expect(find.textContaining('sous la limite basse'), findsOneWidget);
    // Existing low-glucose safety warning stays visible and independent.
    expect(find.textContaining('Valeur basse détectée'), findsOneWidget);

    change(() => glucose = 140);
    await tester.pump();
    final middleColor = cardColor();
    final middleBorder = cardBorder();
    expect(middleColor, isNot(lowColor));
    expect(middleBorder, isNot(lowBorder));
    expect(find.textContaining('zone centrale indicative'), findsOneWidget);

    change(() => glucose = 78);
    await tester.pump();
    expect(find.textContaining('proche de la limite basse'), findsOneWidget);

    change(() => glucose = 170);
    await tester.pump();
    expect(find.textContaining('proche de la limite haute'), findsOneWidget);

    change(() => glucose = 240);
    await tester.pump();
    expect(cardColor(), lowColor);
    expect(cardBorder(), lowBorder);
    expect(find.textContaining('au-dessus de la limite haute'), findsOneWidget);
    // High status must NOT display the low-glucose safety warning.
    expect(find.textContaining('Valeur basse détectée'), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
