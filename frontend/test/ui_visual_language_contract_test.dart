import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('app root applies the certified LOGIN-derived visual language', () {
    final main = _read('lib/main.dart');
    final language = _read('lib/core/theme/amina_visual_language.dart');

    expect(main, contains('AminaVisualLanguage.harmonize(AminaTheme.light)'));
    expect(main, contains('AminaVisualLanguage.harmonize(AminaTheme.dark)'));
    expect(language, contains('class AminaVisualLanguage'));
    expect(language, contains('static const double cardRadius = 24'));
    expect(language, contains('static const double controlRadius = 12'));
    expect(language, contains('static const double fieldRadius = 10'));
    expect(language, contains('primaryGradient'));
    expect(language, contains('inputDecorationTheme:'));
    expect(language, contains('elevatedButtonTheme:'));
    expect(language, contains('filledButtonTheme:'));
    expect(language, contains('outlinedButtonTheme:'));
  });

  test('shared patient surfaces consume the canonical visual language', () {
    for (final path in <String>[
      'lib/core/widgets/clinical_card.dart',
      'lib/core/widgets/glass_card.dart',
      'lib/core/widgets/amina_button.dart',
      'lib/core/widgets/amina_text_field.dart',
      'lib/core/widgets/mobile_page_header.dart',
      'lib/core/widgets/first_use_panel.dart',
    ]) {
      final source = _read(path);
      expect(
        source,
        contains('amina_visual_language.dart'),
        reason: '$path must use the canonical presentation layer',
      );
    }
  });

  test('active premium patient surfaces use the certified brand asset', () {
    const logo = "assets/images/logo_amina.png";
    final dashboardEntry = _read(
      'lib/features/dashboard/dashboard_companion_entry_screen.dart',
    );
    final dashboard = _read(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    );
    final companion = _read(
      'lib/features/companion/companion_premium_screen.dart',
    );
    final header = _read('lib/core/widgets/mobile_page_header.dart');
    final module = _read('lib/modules/diabetes_module.dart');

    expect(dashboardEntry, contains('DashboardPremiumScreen'));
    expect(dashboardEntry, contains("ValueKey('dashboard-companion-primary-entry')"));
    expect(dashboardEntry, isNot(contains('DashboardConvergentScreen')));
    expect(dashboard, contains(logo));
    expect(companion, contains(logo));
    expect(header, contains(logo));
    expect(module, contains('CompanionPremiumScreen'));
  });

  test('visual certification harnesses stay isolated from production main', () {
    final main = _read('lib/main.dart');
    final golden = _read('test/ui_visual_screenshot_test.dart');
    final nativeWorkflow = _read('../.github/workflows/ui-screenshot-audit.yml');
    final browserMain = _read('lib/ui_browser_audit_main.dart');
    final browserWorkflow = _read(
      '../.github/workflows/ui-browser-screenshot.yml',
    );

    expect(main, isNot(contains('await db.seedDemoData()')));
    expect(main, isNot(contains('ui_browser_audit_main.dart')));

    expect(golden, contains('NativeDatabase.memory()'));
    expect(golden, contains('await db.seedDemoData()'));
    expect(golden, contains("bool.fromEnvironment('IAMINA_VISUAL_AUDIT')"));
    expect(golden, isNot(contains('precacheImage(')));
    expect(golden, isNot(contains("package:firebase_core/firebase_core.dart")));
    expect(nativeWorkflow, contains('--dart-define=IAMINA_VISUAL_AUDIT=true'));
    expect(nativeWorkflow, contains('--update-goldens'));
    expect(nativeWorkflow, contains('test/ui_visual_screenshot_test.dart'));

    expect(browserMain, contains('await db.seedDemoData()'));
    expect(browserMain, contains('auth.enterAuditSession()'));
    expect(browserMain, contains("queryParameters['surface']"));
    expect(browserWorkflow, contains('lib/ui_browser_audit_main.dart'));
    expect(browserWorkflow, contains('flutter build web --release'));
    expect(browserWorkflow, contains('--window-size=390,844'));
    expect(browserWorkflow, contains('iamina-ui-browser-cert-390x844'));
  });
}
