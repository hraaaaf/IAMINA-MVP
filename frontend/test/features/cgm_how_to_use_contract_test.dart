import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('each CGM card exposes premium how-to dialog wiring', () {
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

  test('how-to copy has French English Arabic parity and truthful bridge language', () {
    final copy = File('lib/core/localization/import_localized_copy.dart').readAsStringSync();
    expect(copy, contains("en: 'How to use'"));
    expect(copy, contains("fr: 'Mode d’emploi'"));
    expect(copy, contains("ar: 'طريقة الاستخدام'"));
    expect(copy, contains('Juggluco'));
    expect(copy, contains('does not sign in directly to the sensor manufacturer'));
    expect(copy, contains('ne se connecte pas directement au fabricant du capteur'));
  });
}
