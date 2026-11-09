import 'package:amina/features/profile/medical_treatment_declaration_v1.dart';
import 'package:amina/features/profile/medical_treatment_multi_selector.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

/// D7 Web widget journey. These are synthetic, non-patient declarations:
/// neither clinical guidance nor patient-vault browser persistence is claimed.
Widget _harness({
  required String language,
  required String diabetesType,
  required D7TreatmentDeclaration declaration,
  required ValueChanged<D7TreatmentDeclaration> onChanged,
}) =>
    MaterialApp(
      locale: Locale(language),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: Scaffold(
        body: SafeArea(
          child: SingleChildScrollView(
            child: MedicalTreatmentMultiSelector(
              diabetesType: diabetesType,
              value: declaration,
              onChanged: onChanged,
            ),
          ),
        ),
      ),
    );

void main() {
  const viewports = <Size>[
    Size(390, 844),
    Size(768, 1024),
    Size(1280, 900),
  ];
  const languages = ['fr', 'en', 'ar'];

  for (final viewport in viewports) {
    for (final language in languages) {
      testWidgets(
        'D7 Web: no implicit edit, accessible explicit choices '
        '${viewport.width.toInt()}x${viewport.height.toInt()} $language',
        (tester) async {
          tester.view.devicePixelRatio = 1;
          tester.view.physicalSize = viewport;
          addTearDown(tester.view.resetDevicePixelRatio);
          addTearDown(tester.view.resetPhysicalSize);

          var declaration = D7TreatmentDeclaration(
            D7TreatmentStatus.declared,
            const ['oral_meds', 'insulin'],
          );
          var explicitEdits = 0;
          void onChanged(D7TreatmentDeclaration next) {
            declaration = next;
            explicitEdits++;
          }

          Future<void> show(String diabetesType) async {
            await tester.pumpWidget(_harness(
              language: language,
              diabetesType: diabetesType,
              declaration: declaration,
              onChanged: onChanged,
            ));
            await tester.pumpAndSettle();
            expect(tester.takeException(), isNull);
          }

          await show('type2');
          expect(declaration.codes, ['oral_meds', 'insulin']);
          expect(explicitEdits, 0);

          // A type switch may change presentation/order, not a reported
          // treatment. Secondary, previously selected codes remain visible.
          await show('type1');
          expect(declaration.codes, ['oral_meds', 'insulin']);
          expect(explicitEdits, 0);
          expect(find.byKey(const Key('d7-treatment-oral_meds')), findsOneWidget);
          expect(find.byKey(const Key('d7-treatment-insulin')), findsOneWidget);

          final direction = Directionality.of(
            tester.element(find.byType(MedicalTreatmentMultiSelector)),
          );
          expect(direction,
              language == 'ar' ? TextDirection.rtl : TextDirection.ltr);

          // Only an explicit action can clear the declaration.
          final none = find.byKey(const Key('d7-none'));
          await tester.ensureVisible(none);
          await tester.tap(none);
          expect(declaration.state, D7TreatmentStatus.noneDeclared);
          expect(declaration.codes, isEmpty);
          expect(explicitEdits, 1);

          // Unknown type does not fabricate a new choice after "none".
          await show('unknown');
          expect(declaration.state, D7TreatmentStatus.noneDeclared);
          expect(declaration.codes, isEmpty);
          expect(explicitEdits, 1);

          // A new patient action can report a treatment for unknown type.
          final insulin = find.byKey(const Key('d7-treatment-insulin'));
          await tester.ensureVisible(insulin);
          await tester.tap(insulin);
          expect(declaration.state, D7TreatmentStatus.declared);
          expect(declaration.codes, ['insulin']);
          expect(explicitEdits, 2);

          // Another type switch preserves the explicit value.
          await show('gestational');
          expect(declaration.codes, ['insulin']);
          expect(explicitEdits, 2);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }
}
