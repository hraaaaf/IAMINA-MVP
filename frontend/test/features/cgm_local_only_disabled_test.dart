import 'package:amina/core/localization/import_localized_copy.dart';
import 'package:amina/features/import/cgm_connections_section.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/cgm_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

class _LocalOnlyCgmService extends CgmService {
  @override
  Future<CgmConnectionState> getConnection() async {
    throw const CgmServiceException('clinical_transport_disabled_local_only', 403);
  }

  @override
  void dispose() {}
}

void main() {
  for (final (locale, copy) in <(Locale, String)>[
    (const Locale('fr'), 'La connexion CGM est indisponible dans cette version locale. Aucune donnée du capteur n’est transmise.'),
    (const Locale('en'), 'Connected CGM is unavailable in this local-only version. No sensor data is sent.'),
    (const Locale('ar'), 'اتصال مستشعر السكر غير متاح في هذه النسخة المحلية. لا تُرسل بيانات المستشعر.'),
  ]) {
    testWidgets('L0 CGM refuses configuration in ${locale.languageCode}', (tester) async {
      await tester.pumpWidget(MaterialApp(
        locale: locale,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(body: CgmConnectionsSection(service: _LocalOnlyCgmService())),
      ));
      await tester.pumpAndSettle();
      expect(find.text(copy), findsOneWidget);
      final configure = find.widgetWithText(FilledButton, AppLocalizations.of(tester.element(find.byType(CgmConnectionsSection)))!.cgmConfigure);
      expect(configure, findsWidgets);
      for (final button in tester.widgetList<FilledButton>(configure)) {
        expect(button.onPressed, isNull);
      }
    });
  }
}
