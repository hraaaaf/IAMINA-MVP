import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Document import keeps ingest orchestration out of presentation part', () {
    final state = File(
      'lib/features/documents/document_import_screen.dart',
    ).readAsStringSync();
    final presentation = File(
      'lib/features/documents/document_import_screen_presentation.dart',
    ).readAsStringSync();

    expect(state, contains("part 'document_import_screen_presentation.dart';"));
    expect(state, contains('class _DocumentImportScreenState'));
    expect(state, contains('Future<void> _pickFile()'));
    expect(state, contains('Future<void> _ingest('));
    expect(state, contains('Future<void> _confirm()'));
    expect(state, contains('context.read<ApiClient>()'));
    expect(state, isNot(contains('class _PrivacyGateNotice')));
    expect(state, isNot(contains('class _GlucoseReadingsList')));
    expect(state, isNot(contains('class _LabValuesCard')));
    expect(state, isNot(contains('class _MedicationTile')));

    expect(presentation, contains('class _PrivacyGateNotice'));
    expect(presentation, contains('class _GlucoseReadingsList'));
    expect(presentation, contains('class _LabValuesCard'));
    expect(presentation, contains('class _MedicationTile'));
    expect(presentation, isNot(contains('context.read<ApiClient>()')));
    expect(presentation, isNot(contains('Future<void> _ingest(')));
    expect(presentation, isNot(contains("import 'package:")));
  });
}
