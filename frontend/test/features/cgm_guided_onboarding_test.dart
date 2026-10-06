import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/features/import/cgm_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/cgm_service.dart';


class _AuthRequiredCgmService extends CgmService {
  @override
  Future<CgmConnectionState> getConnection() async {
    throw const CgmServiceException('authentication_required', 401);
  }
}

class _GuidedCgmService extends CgmService {
  @override
  Future<CgmConnectionState> getConnection() async =>
      const CgmConnectionState(connected: false);
}

Future<void> _pumpGuide(
  WidgetTester tester, {
  required Size size,
  Locale locale = const Locale('fr'),
}) async {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  await tester.pumpWidget(
    MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AminaVisualLanguage.harmonize(AminaTheme.light),
      locale: locale,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      home: CgmScreen(service: _GuidedCgmService()),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 250));
}


Future<void> _pumpAuthRequiredGuide(WidgetTester tester) async {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = const Size(390, 844);
  await tester.pumpWidget(
    MaterialApp(
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
      home: CgmScreen(service: _AuthRequiredCgmService()),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 250));
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  tearDown(() {
    final binding = TestWidgetsFlutterBinding.instance;
    binding.platformDispatcher.views.first.resetPhysicalSize();
    binding.platformDispatcher.views.first.resetDevicePixelRatio();
  });

  testWidgets('novice CGM wizard reveals only the selected source path', (
    tester,
  ) async {
    await _pumpGuide(tester, size: const Size(390, 844));

    expect(find.text('Connecter mon CGM'), findsOneWidget);
    expect(find.text('Quel capteur utilisez-vous ?'), findsOneWidget);
    expect(find.text('Dexcom G6/G7'), findsOneWidget);
    expect(find.text('FreeStyle Libre'), findsOneWidget);
    expect(find.text('LinX / AiDEX X'), findsOneWidget);
    expect(find.text('Je n’ai pas encore Nightscout'), findsNothing);

    await tester.tap(find.byKey(const ValueKey('cgm-wizard-source-dexcom')));
    await tester.pumpAndSettle();

    expect(
      find.textContaining('Avez-vous déjà Nightscout pour Dexcom G6/G7'),
      findsOneWidget,
    );
    expect(find.text('FreeStyle Libre'), findsNothing);
    expect(find.text('LinX / AiDEX X'), findsNothing);

    await tester.tap(find.byKey(const ValueKey('cgm-wizard-nightscout-no')));
    await tester.pumpAndSettle();

    expect(find.text('Préparez Nightscout pour ce capteur'), findsOneWidget);
    expect(find.text('Je n’ai pas encore Nightscout'), findsOneWidget);
    expect(find.text('nightscout.github.io'), findsOneWidget);
    expect(find.textContaining('Partage/Share'), findsOneWidget);
    expect(find.textContaining('Nightscout Connect'), findsWidgets);
    expect(find.textContaining('IAMINA ne demande jamais votre mot de passe'), findsNothing);

    expect(tester.takeException(), isNull);
  });

  testWidgets('auth-required CGM state stays truthful after wizard selection', (
    tester,
  ) async {
    await _pumpAuthRequiredGuide(tester);

    await tester.tap(find.byKey(const ValueKey('cgm-wizard-source-dexcom')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('cgm-wizard-nightscout-yes')));
    await tester.pumpAndSettle();

    expect(
      find.textContaining('un compte IAMINA authentifié est requis'),
      findsOneWidget,
    );

    final configureButtons = tester
        .widgetList<FilledButton>(find.byType(FilledButton))
        .where((button) {
          final child = button.child;
          return child is Text && child.data == 'Configurer';
        })
        .toList();

    expect(configureButtons, hasLength(1));
    expect(configureButtons.single.onPressed, isNull);
    expect(find.byTooltip('Mode d’emploi'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('guided CGM page does not overflow certified viewports', (tester) async {
    for (final size in const [
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      await _pumpGuide(tester, size: size);
      expect(find.text('Connecter mon CGM'), findsOneWidget);
      expect(tester.takeException(), isNull, reason: 'viewport $size');
    }
  });

  testWidgets('guided CGM page keeps English and Arabic copy parity', (tester) async {
    await _pumpGuide(
      tester,
      size: const Size(390, 844),
      locale: const Locale('en'),
    );
    expect(find.text('Connect my CGM'), findsOneWidget);
    expect(find.text('Which sensor do you use?'), findsOneWidget);

    await _pumpGuide(
      tester,
      size: const Size(390, 844),
      locale: const Locale('ar'),
    );
    expect(find.text('ربط جهاز CGM'), findsOneWidget);
    expect(find.text('ما المستشعر الذي تستخدمه؟'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
