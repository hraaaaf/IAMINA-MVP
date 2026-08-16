import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Importer mounts the live CGM connections section', () {
    final source = File('lib/features/import/import_screen.dart').readAsStringSync();

    expect(source, contains("import 'cgm_connections_section.dart';"));
    expect(source, contains('const CgmConnectionsSection()'));
    expect(source, isNot(contains('const _UnavailableAction()')));
    expect(source, isNot(contains("title: 'Abbott LibreLink'")));
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
