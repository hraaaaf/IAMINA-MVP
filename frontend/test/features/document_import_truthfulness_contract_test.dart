import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Document preview confirms only data the store actually persists', () {
    final model = File(
      'lib/data/models/document_models.dart',
    ).readAsStringSync();

    final usefulDataStart = model.indexOf('bool get hasUsefulData');
    final factoryStart = model.indexOf('factory PulperPreview.fromJson');
    expect(usefulDataStart, greaterThanOrEqualTo(0));
    expect(factoryStart, greaterThan(usefulDataStart));

    final usefulData = model.substring(usefulDataStart, factoryStart);
    expect(usefulData, contains('glucoseReadings.isNotEmpty'));
    expect(usefulData, contains('!labValues.isEmpty'));
    expect(usefulData, contains('clinicalNotes.isNotEmpty'));
    expect(usefulData, isNot(contains('medications.isNotEmpty')));
  });

  test('Medication extraction is explicitly marked preview-only', () {
    final copy = File(
      'lib/core/localization/document_import_localized_copy.dart',
    ).readAsStringSync();

    expect(copy, contains('Medications detected — not imported'));
    expect(copy, contains('Médicaments détectés — non importés'));
    expect(copy, contains('أدوية مكتشفة — لن يتم استيرادها'));
    expect(copy, contains('No importable medical data'));
  });

  test('Privacy copy matches local extraction and pseudonymized text egress', () {
    final screen = File(
      'lib/features/documents/document_import_screen.dart',
    ).readAsStringSync();
    final copy = File(
      'lib/core/localization/document_import_localized_copy.dart',
    ).readAsStringSync();

    expect(screen, contains('l10n.privacyProcessingBody'));
    expect(screen, isNot(contains('l10n.documentPrivacyBody')));
    expect(copy, contains('The file is processed locally first.'));
    expect(copy, contains('Le fichier est d’abord traité localement.'));
    expect(copy, contains('تتم معالجة الملف محليًا أولًا.'));
    expect(copy, contains('pseudonymized text'));
  });

  test('Photo format chip uses localized copy', () {
    final screen = File(
      'lib/features/documents/document_import_screen.dart',
    ).readAsStringSync();

    expect(screen, contains('AuditedPageCopy.of(context).photo'));
    expect(screen, isNot(contains("label: 'Photo'")));
  });

  test('Document confirmation endpoint matches backend route', () {
    final client = File('lib/services/api_client.dart').readAsStringSync();
    expect(
      client,
      contains("Uri.parse('/api/v1/documents/confirm/\$batchId')"),
    );
  });
}
