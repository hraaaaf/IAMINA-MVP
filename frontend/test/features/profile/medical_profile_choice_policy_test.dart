import 'package:amina/features/profile/medical_profile_choice_policy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D7 display options remain contextual and never exclusive', () {
    final pre = treatmentPresentation('pre');
    expect(pre.primary, ['lifestyle']);
    expect(pre.onRequest, contains('insulin'));
    expect(pre.onRequest, contains('tablets'));
    for (final type in knownDiabetesTypes) {
      final plan = treatmentPresentation(type);
      expect([...plan.primary, ...plan.onRequest].toSet(),
          declaredTreatmentChoices.toSet());
      expect(plan.primary.toSet().intersection(plan.onRequest.toSet()), isEmpty);
    }
  });
  test('D7 preserves self-declared unknown categories', () {
    expect(isValidPatientDeclaredDiabetesType('unknown'), isTrue);
    expect(isValidPatientDeclaredDiabetesType('other'), isTrue);
    expect(isValidPatientDeclaredTreatment('unknown'), isTrue);
    expect(isValidPatientDeclaredTreatment('other'), isTrue);
    expect(isValidPatientDeclaredTreatment('made-up'), isFalse);
  });
}
