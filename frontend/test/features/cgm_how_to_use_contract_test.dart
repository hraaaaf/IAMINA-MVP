import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('each CGM card exposes guided source-specific how-to wiring', () {
    final source = File('lib/features/import/cgm_connections_section.dart').readAsStringSync();
    expect(source, contains('Future<void> _showHowTo'));
    expect(source, contains('Icons.help_outline_rounded'));
    expect(source, contains('label: Text(l10n.cgmHowToUse)'));
    expect(source, contains('class _CgmHowToDialog'));
    expect(source, contains('for (var i = 0; i < steps.length; i++)'));
    expect(source, contains("'dexcom' => l10n.cgmHowToDexcomBridge"));
    expect(source, contains("'libre' => l10n.cgmHowToLibreBridge"));
    expect(source, contains("'linx' => l10n.cgmHowToLinxBridge"));
    expect(source, contains('Navigator.pop(context, true)'));
  });

  test('how-to copy has FR EN AR parity and concrete truthful bridge guidance', () {
    final copy = File('lib/core/localization/import_localized_copy.dart').readAsStringSync();
    expect(copy, contains("en: 'How to use'"));
    expect(copy, contains("fr: 'Mode d’emploi'"));
    expect(copy, contains("ar: 'طريقة الاستخدام'"));
    expect(copy, contains('Dexcom Share/Connect'));
    expect(copy, contains('Juggluco'));
    expect(copy, contains('xDrip/xDrip4iOS'));
    expect(copy, contains('Never enter your Dexcom, Abbott or MicroTech password in IAMINA'));
    expect(copy, contains('Ne saisissez jamais votre mot de passe Dexcom, Abbott ou MicroTech dans IAMINA'));
  });

  test('dedicated CGM guide remains the novice entry point', () {
    final importer = File('lib/features/import/import_screen.dart').readAsStringSync();
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final guide = File('lib/features/import/cgm_screen.dart').readAsStringSync();

    expect(importer, contains("context.push('/cgm')"));
    expect(module, contains("path: '/cgm'"));
    expect(guide, contains('nightscout.github.io'));
    expect(guide, contains('Dexcom app + Share'));
    expect(guide, contains('Juggluco'));
    expect(guide, contains('xDrip'));
  });
}
