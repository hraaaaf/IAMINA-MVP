import 'package:amina/features/profile/medical_treatment_declaration_v1.dart';
import 'package:amina/features/profile/medical_treatment_multi_selector.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Widget harness(D7TreatmentDeclaration value, ValueChanged<D7TreatmentDeclaration> change,
    {String type = 'prediabetes', String lang = 'fr'}) => MaterialApp(
  locale: Locale(lang),
  supportedLocales: AppLocalizations.supportedLocales,
  localizationsDelegates: const [
    AppLocalizations.delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  home: Scaffold(body: SingleChildScrollView(child: MedicalTreatmentMultiSelector(
    diabetesType: type, value: value, onChanged: change,
  ))),
);

void main() {
  test('D7 v1 states are separate and never silently coerce treatments', () {
    for (final state in [
      D7TreatmentStatus.notAnswered,
      D7TreatmentStatus.unsure,
      D7TreatmentStatus.noneDeclared,
    ]) {
      final d = D7TreatmentDeclaration(state, const []);
      expect((d.toApiPatch()['treatment_declaration'] as Map)['state'],
          d7StateCode(state));
    }
    expect(
      () => D7TreatmentDeclaration(D7TreatmentStatus.unsure, ['insulin']),
      throwsArgumentError,
    );
    expect(
      () => D7TreatmentDeclaration(D7TreatmentStatus.declared,
          ['insulin', 'insulin']),
      throwsArgumentError,
    );
  });

  test('D7 six types never remove a patient reportable option', () {
    for (final type in ['type1','type2','gestational','prediabetes','other','unknown']) {
      final options = [...d7PrimaryOptions(type), ...d7OtherOptions(type)];
      expect(options.toSet(), d7TreatmentCodes.toSet());
    }
    expect(d7PrimaryOptions('prediabetes'), ['lifestyle']);
    expect(d7PrimaryOptions('type1'), ['insulin']);
    expect(d7PrimaryOptions('unknown'), isEmpty);
  });

  testWidgets('D7 prediabetes secondary insulin still reportable, multi-selected',
      (tester) async {
    var value = D7TreatmentDeclaration.later();
    Future<void> pump() async {
      await tester.pumpWidget(harness(value, (v) => value = v));
      await tester.pumpAndSettle();
    }
    await pump();
    expect(find.text('Insuline'), findsNothing);
    await tester.tap(find.byKey(const Key('d7-treatment-lifestyle')));
    await pump();
    expect(value.codes, ['lifestyle']);
    await tester.tap(find.byKey(const Key('d7-show-other')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('d7-treatment-insulin')));
    await pump();
    expect(value.codes, ['lifestyle','insulin']);
    await tester.tap(find.byKey(const Key('d7-later')));
    expect(value.state, D7TreatmentStatus.notAnswered);
    expect(value.codes, isEmpty);
  });

  testWidgets('D7 Arabic later and unsure are not one state', (tester) async {
    var value = D7TreatmentDeclaration.later();
    await tester.pumpWidget(harness(value, (v) => value = v,
        type: 'unknown', lang: 'ar'));
    await tester.pumpAndSettle();
    expect(find.text('سأجيب لاحقًا'), findsOneWidget);
    await tester.tap(find.byKey(const Key('d7-unsure')));
    expect(value.state, D7TreatmentStatus.unsure);
  });
}
