import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Importer routes to the dedicated live CGM connections page', () {
    final importSource = File(
      'lib/features/import/import_screen.dart',
    ).readAsStringSync();
    final cgmSource = File(
      'lib/features/import/cgm_screen.dart',
    ).readAsStringSync();
    final moduleSource = File(
      'lib/modules/diabetes_module.dart',
    ).readAsStringSync();

    expect(importSource, contains("context.push('/cgm')"));
    expect(importSource, isNot(contains('const CgmConnectionsSection()')));
    expect(cgmSource, contains("import 'cgm_connections_section.dart';"));
    expect(cgmSource, contains('CgmConnectionsSection(service: service)'));
    expect(moduleSource, contains("path: '/cgm'"));
    expect(moduleSource, contains('builder: (s) => const CgmScreen()'));
    expect(importSource, isNot(contains('const _UnavailableAction()')));
    expect(importSource, isNot(contains("title: 'Abbott LibreLink'")));
  });

  test('CGM UI states vendor path truthfully and avoids clinical interpretation', () {
    final source = File(
      'lib/features/import/cgm_connections_section.dart',
    ).readAsStringSync();

    expect(source, contains("id: 'dexcom'"));
    expect(source, contains("id: 'libre'"));
    expect(source, contains("id: 'linx'"));
    expect(source, contains('cgmViaNightscout'));
    expect(source, contains('cgmBridgeDisclosure'));
    expect(source, contains('glucoseMgDl'));
    expect(source, isNot(contains('targetRange')));
    expect(source, isNot(contains('urgent')));
    expect(source, isNot(contains('dose')));
    expect(source, isNot(contains('treatment')));
  });

  test('credential entry is obscured and never prefilled from stored state', () {
    final source = File(
      'lib/features/import/cgm_connections_section.dart',
    ).readAsStringSync();

    expect(source, contains('obscureText: _obscure'));
    expect(source, contains('final _credential = TextEditingController()'));
    expect(source, isNot(contains('encryptedCredential')));
    expect(source, isNot(contains('credentialSet ?')));
  });
}
