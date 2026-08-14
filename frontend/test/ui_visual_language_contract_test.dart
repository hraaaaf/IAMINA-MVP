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

  test('visual certification stays deterministic and isolated from production main', () {
    final main = _read('lib/main.dart');
    final harness = _read('lib/ui_audit_main.dart');
    final workflow = _read('../.github/workflows/ui-screenshot-audit.yml');

    expect(main, isNot(contains('await db.seedDemoData()')));
    expect(harness, contains("import 'package:drift/wasm.dart';"));
    expect(harness, contains('await db.seedDemoData()'));
    expect(harness, isNot(contains("package:firebase_core/firebase_core.dart")));
    expect(
      workflow,
      contains('flutter build web --release -t lib/ui_audit_main.dart'),
    );
    expect(workflow, contains('Capture $NAME is suspiciously small'));
    expect(
      workflow,
      contains('Visual audit produced too few distinct mobile renders'),
    );
  });
}
