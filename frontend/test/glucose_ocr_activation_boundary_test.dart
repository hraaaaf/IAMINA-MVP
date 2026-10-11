import 'dart:io';

import 'package:amina/core/clinical/glucose_ocr_shield.dart';
import 'package:flutter_test/flutter_test.dart';

// Issue #923: characterize only the not-yet-connected OCR path.
// This is not a validation of optical unit provenance or clinical thresholds.
void main() {
  test('HI and LO remain nonnumeric and require explicit handling', () {
    for (final marker in ['HI', 'HIGH', 'LO', 'LOW']) {
      final result = GlucoseOcrShield.extract(marker);
      expect(result.value, isNull, reason: marker);
      expect(result.hasValue, isFalse, reason: marker);
      expect(result.needsConfirmation, isTrue, reason: marker);
    }
  });

  test('multiple numeric suggestions never qualify as high-confidence', () {
    final result = GlucoseOcrShield.extract('120 180 mg/dL');
    expect(result.hasValue, isTrue);
    expect(result.confidence, lessThan(0.80));
    expect(result.needsConfirmation, isTrue);
  });

  test('unreviewed Flutter screens cannot silently activate glucose OCR', () {
    final sourceFiles = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((file) => file.path.endsWith('.dart'));

    final activeCall = RegExp(r'\bGlucoseOcrShield\s*\.\s*extract\s*\(');
    final cloudCall = RegExp(r'\banalyzeGlucometerImage\s*\(');
    final unexpected = <String>[];

    for (final file in sourceFiles) {
      final path = file.path.replaceAll('\\', '/');
      if (path.endsWith('core/clinical/glucose_ocr_shield.dart') ||
          path.endsWith('services/api_client.dart')) {
        continue;
      }
      final content = file.readAsStringSync();
      if (activeCall.hasMatch(content) || cloudCall.hasMatch(content)) {
        unexpected.add(path);
      }
    }

    expect(
      unexpected,
      isEmpty,
      reason: 'A new patient OCR caller requires a separate reviewed '
          'capture/confirmation/storage and privacy test before activation.',
    );
  });
}
