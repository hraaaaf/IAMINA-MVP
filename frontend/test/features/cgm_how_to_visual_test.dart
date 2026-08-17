import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/features/import/cgm_connections_section.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/cgm_service.dart';

const _visualAuditEnabled = bool.fromEnvironment('IAMINA_VISUAL_AUDIT');

class _HowToVisualCgmService extends CgmService {
  @override
  Future<CgmConnectionState> getConnection() async =>
      const CgmConnectionState(connected: false);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('premium CGM how-to dialog is visually certified at 390x844', (
    tester,
  ) async {
    if (!_visualAuditEnabled) return;

    // This golden is the release gate for first-view mobile CTA visibility.
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(390, 844);
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    final service = _HowToVisualCgmService();
    addTearDown(service.dispose);
    const captureKey = ValueKey<String>('cgm-how-to-dialog-390x844');

    await tester.pumpWidget(
      RepaintBoundary(
        key: captureKey,
        child: MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: AminaVisualLanguage.harmonize(AminaTheme.light),
          locale: const Locale('fr'),
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          home: Scaffold(
            backgroundColor: const Color(0xFFF4FBF9),
            body: SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: CgmConnectionsSection(service: service),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('Mode d’emploi'), findsNWidgets(3));

    await tester.tap(find.text('Mode d’emploi').first);
    await tester.pumpAndSettle();
    expect(find.text('Connecter Dexcom G6/G7'), findsOneWidget);
    expect(find.text('Préparer votre bridge'), findsOneWidget);
    expect(find.text('Récupérer l’accès sécurisé'), findsOneWidget);
    expect(find.text('Connecter IAMINA'), findsOneWidget);

    await expectLater(
      find.byKey(captureKey),
      matchesGoldenFile('../ui_audit_output/cgm-how-to-dialog-390x844.png'),
    );
  });
}
