import 'package:amina/features/import/cgm_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final copy = <String, String>{
    'fr': 'La connexion CGM est indisponible dans cette version locale. La configuration est désactivée et aucune donnée du capteur n’est transmise.',
    'en': 'Connected CGM is not available in this local-only version. Sensor setup is disabled and no CGM data is transmitted.',
    'ar': 'اتصال مستشعر السكر غير متاح في هذه النسخة المحلية. إعداد المستشعر معطّل ولا تُرسل أي بيانات منه.',
  };

  for (final locale in <String>['fr', 'en', 'ar']) {
    for (final size in <Size>[
      const Size(390, 844),
      const Size(768, 1024),
      const Size(1280, 900),
    ]) {
      testWidgets('L0 Web RELEASE CGM wizard disabled $locale $size', (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = size;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        await tester.pumpWidget(MaterialApp(
          locale: Locale(locale),
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          home: const CgmScreen(forceLocalOnlyDisabledForTests: true),
        ));
        await tester.pumpAndSettle();
        expect(find.text(copy[locale]!), findsOneWidget);
        expect(find.byKey(const ValueKey('cgm-wizard-local-only-disabled')), findsOneWidget);
        expect(find.byKey(const ValueKey('cgm-wizard-source-dexcom')), findsNothing);
        expect(find.byKey(const ValueKey('cgm-wizard-source-libre')), findsNothing);
        expect(find.byKey(const ValueKey('cgm-wizard-source-linx')), findsNothing);
        expect(find.byKey(const ValueKey('cgm-wizard-nightscout-yes')), findsNothing);
        expect(tester.takeException(), isNull);
      });
    }
  }
}
