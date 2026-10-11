import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/clinical/glucose_ocr_shield.dart';

void main() {
  test('unlabelled OCR numbers cannot suggest a glucose unit or value', () {
    for (final text in ['120', '6.5', '120 UNKNOWN', '6.5 mmol']) {
      final result = GlucoseOcrShield.extract(text);
      expect(result.hasValue, isFalse, reason: text);
      expect(result.needsConfirmation, isTrue, reason: text);
      expect(result.confidence, 0.0, reason: text);
    }
  });

  test('mixed unit labels are ambiguous and fail closed', () {
    final result = GlucoseOcrShield.extract('120 mg/dL 6.5 mmol/L');
    expect(result.hasValue, isFalse);
    expect(result.needsConfirmation, isTrue);
  });

  test('visible mg/dL and mmol/L units preserve accepted numeric parsing', () {
    final mgdl = GlucoseOcrShield.extract('120 mg/dL');
    expect(mgdl.hasValue, isTrue);
    expect(mgdl.value, 120.0);
    expect(mgdl.unitWasMmol, isFalse);

    final mmol = GlucoseOcrShield.extract('6.5 mmol/L');
    expect(mmol.hasValue, isTrue);
    expect(mmol.value, closeTo(117.0, 0.01));
    expect(mmol.unitWasMmol, isTrue);
  });
}
