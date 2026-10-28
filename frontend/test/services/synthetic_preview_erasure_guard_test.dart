import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/auth_service.dart';

void main() {
  test('erasure permits only exact synthetic QA account under both gates', () {
    bool allowed(String? email, {bool preview = true, bool enrolled = true}) =>
        syntheticPreviewAccountEraseAllowed(
          sameOriginPreview: preview,
          remoteAccountEnrollmentEnabled: enrolled,
          email: email,
        );

    expect(allowed('patient-a@example.invalid'), isTrue);
    expect(allowed('w01g5-bff-abc123@example.invalid'), isTrue);
    expect(allowed('patient@example.com'), isFalse);
    expect(allowed('patient@example.invalid.evil.com'), isFalse);
    expect(allowed('Patient@example.invalid'), isFalse);
    expect(allowed('patient@example.invalid '), isFalse);
    expect(allowed('sample+unsafe@example.invalid'), isFalse);
    expect(allowed(null), isFalse);
    expect(allowed('patient-a@example.invalid', preview: false), isFalse);
    expect(allowed('patient-a@example.invalid', enrolled: false), isFalse);
  });
}
