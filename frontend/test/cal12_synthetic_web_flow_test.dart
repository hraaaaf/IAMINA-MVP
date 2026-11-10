import 'package:amina/features/journal/synthetic_doctor_export_web_flow.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final lang in const ['fr', 'ar']) {
    for (final size in const [
      Size(390, 844), Size(768, 1024), Size(1280, 900),
    ]) {
      testWidgets('CAL12 Web fictional flow A-B-A $lang $size',
          (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(MaterialApp(
          locale: Locale(lang),
          supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: SyntheticDoctorExportWebFlow(languageCode: lang),
        ));
        await tester.pumpAndSettle();

        final start = find.byKey(const ValueKey('cal12-preview-next'));
        expect(find.byKey(const ValueKey('cal12-step-preview')), findsOneWidget);
        expect(find.text('142 mg/dL'), findsOneWidget);
        await tester.ensureVisible(start);
        await tester.tap(start);
        await tester.pumpAndSettle();

        final consentNext = find.byKey(const ValueKey('cal12-consent-next'));
        expect(tester.widget<FilledButton>(consentNext).onPressed, isNull);
        await tester.ensureVisible(
            find.byKey(const ValueKey('cal12-consent-checkbox')));
        await tester.tap(find.byKey(const ValueKey('cal12-consent-checkbox')));
        await tester.pumpAndSettle();
        expect(tester.widget<FilledButton>(consentNext).onPressed, isNotNull);
        await tester.ensureVisible(consentNext);
        await tester.tap(consentNext);
        await tester.pumpAndSettle();

        final simulate = find.byKey(const ValueKey('cal12-simulate'));
        expect(tester.widget<FilledButton>(simulate).onPressed, isNull);
        final doctor = find.byKey(const ValueKey('cal12-recipient-doctorOne'));
        await tester.ensureVisible(doctor);
        await tester.tap(doctor);
        await tester.pumpAndSettle();
        expect(tester.widget<FilledButton>(simulate).onPressed, isNull);
        final confirm = find.byKey(
            const ValueKey('cal12-recipient-confirm'));
        await tester.ensureVisible(confirm);
        await tester.tap(confirm);
        await tester.pumpAndSettle();
        expect(tester.widget<FilledButton>(simulate).onPressed, isNotNull);
        await tester.ensureVisible(simulate);
        await tester.tap(simulate);
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('cal12-step-done')), findsOneWidget);
        expect(find.text('142 mg/dL'), findsOneWidget);

        // An owner switch must immediately forget the A consent, selection and
        // generated in-memory preview. B is a DIFFERENT fictional reading.
        final ownerB = find.byKey(const ValueKey('cal12-owner-beta'));
        await tester.ensureVisible(ownerB);
        await tester.tap(ownerB);
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('cal12-step-preview')), findsOneWidget);
        expect(find.text('119 mg/dL'), findsOneWidget);
        expect(find.text('142 mg/dL'), findsNothing);
        expect(find.byKey(const ValueKey('cal12-step-done')), findsNothing);

        final ownerA = find.byKey(const ValueKey('cal12-owner-alpha'));
        await tester.ensureVisible(ownerA);
        await tester.tap(ownerA);
        await tester.pumpAndSettle();
        expect(find.text('142 mg/dL'), findsOneWidget);
        expect(find.text('119 mg/dL'), findsNothing);
        await tester.ensureVisible(start);
        await tester.tap(start);
        await tester.pumpAndSettle();
        expect(tester.widget<FilledButton>(consentNext).onPressed, isNull);
        expect(tester.takeException(), isNull);
      });
    }
  }

  testWidgets('CAL12 revoke resets simulated authorization', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: SyntheticDoctorExportWebFlow(languageCode: 'fr'),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('cal12-preview-next')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('cal12-consent-checkbox')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('cal12-consent-next')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('cal12-recipient-doctorOne')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('cal12-recipient-confirm')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('cal12-revoke')));
    await tester.tap(find.byKey(const ValueKey('cal12-revoke')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('cal12-step-preview')), findsOneWidget);
    expect(find.byKey(const ValueKey('cal12-step-done')), findsNothing);
  });
}
