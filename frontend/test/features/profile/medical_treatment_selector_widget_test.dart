import 'package:amina/features/profile/medical_treatment_selector.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _harness(String type, ValueChanged<String> onChoose) => MaterialApp(
  locale: const Locale('fr'),
  localizationsDelegates: const [
    AppLocalizations.delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: SingleChildScrollView(child: MedicalTreatmentSelector(
    diabetesType: type, selectedTreatment: null, onSelected: onChoose,
  ))),
);

void main() {
  testWidgets('D7 prediabetes first view does not display insulin', (tester) async {
    String? declared;
    await tester.pumpWidget(_harness('pre', (s) => declared = s));
    await tester.pumpAndSettle();
    expect(find.text('Habitudes de vie'), findsOneWidget);
    expect(find.text('Insuline'), findsNothing);
    await tester.tap(find.byKey(const Key('medical-show-other-declarations')));
    await tester.pumpAndSettle();
    expect(find.text('Insuline'), findsOneWidget);
    await tester.tap(find.byKey(const Key('declared-treatment-insulin')));
    expect(declared, 'insulin'); // Patient declaration is still possible.
  });

  testWidgets('D7 type1 foregrounds insulin; type2 starts with usual categories', (tester) async {
    await tester.pumpWidget(_harness('type1', (_) {}));
    await tester.pumpAndSettle();
    expect(find.text('Insuline'), findsOneWidget);
    await tester.pumpWidget(_harness('type2', (_) {}));
    await tester.pumpAndSettle();
    expect(find.text('Habitudes de vie'), findsOneWidget);
    expect(find.text('Médicaments déclarés'), findsOneWidget);
    expect(find.text('Insuline'), findsNothing);
  });
}
