import 'package:amina/features/profile/medical_treatment_declaration_v1.dart';
import 'package:amina/features/profile/medical_treatment_multi_selector.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _webHarness({
  required String diabetesType,
  required D7TreatmentDeclaration value,
  required ValueChanged<D7TreatmentDeclaration> onChanged,
  String language = 'fr',
}) {
  return MaterialApp(
    locale: Locale(language),
    supportedLocales: AppLocalizations.supportedLocales,
    localizationsDelegates: const [
      AppLocalizations.delegate,
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    home: Scaffold(
      body: SingleChildScrollView(
        child: MedicalTreatmentMultiSelector(
          diabetesType: diabetesType,
          value: value,
          onChanged: onChanged,
        ),
      ),
    ),
  );
}

void main() {
  testWidgets(
    'D7 Web: switching declared diabetes type never silently rewrites treatments',
    (tester) async {
      var declaration = D7TreatmentDeclaration(
        D7TreatmentStatus.declared,
        const ['oral_meds', 'insulin'],
      );
      var explicitEdits = 0;
      void onChanged(D7TreatmentDeclaration next) {
        declaration = next;
        explicitEdits++;
      }

      await tester.pumpWidget(_webHarness(
        diabetesType: 'type2',
        value: declaration,
        onChanged: onChanged,
      ));
      await tester.pumpAndSettle();

      // The same patient's reported treatments must survive a change in the
      // type field; primary choices are presentation, not treatment advice.
      await tester.pumpWidget(_webHarness(
        diabetesType: 'type1',
        value: declaration,
        onChanged: onChanged,
      ));
      await tester.pumpAndSettle();
      expect(explicitEdits, 0);
      expect(declaration.state, D7TreatmentStatus.declared);
      expect(declaration.codes, const ['oral_meds', 'insulin']);
      expect(find.byKey(const Key('d7-treatment-insulin')), findsOneWidget);
      expect(find.byKey(const Key('d7-treatment-oral_meds')), findsOneWidget);

      // Only an actual patient action may change a declaration.
      await tester.tap(find.byKey(const Key('d7-treatment-oral_meds')));
      expect(explicitEdits, 1);
      expect(declaration.codes, const ['insulin']);

      await tester.pumpWidget(_webHarness(
        diabetesType: 'unknown',
        value: declaration,
        onChanged: onChanged,
        language: 'ar',
      ));
      await tester.pumpAndSettle();
      expect(explicitEdits, 1);
      expect(declaration.codes, const ['insulin']);
      expect(find.byKey(const Key('d7-treatment-insulin')), findsOneWidget);

      // Explicitly declining to declare medication is distinct from "unknown"
      // or "answer later", including in Arabic / RTL.
      await tester.tap(find.byKey(const Key('d7-none')));
      expect(declaration.state, D7TreatmentStatus.noneDeclared);
      expect(declaration.codes, isEmpty);
      expect(explicitEdits, 2);
    },
  );
}
