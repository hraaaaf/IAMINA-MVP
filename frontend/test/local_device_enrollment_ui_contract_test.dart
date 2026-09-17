import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('default auth router selects local device enrollment', () {
    final source = File('lib/features/auth/login_screen.dart').readAsStringSync();

    expect(source, contains("import '../../services/auth_service.dart';"));
    expect(source, contains("import 'local_device_enrollment_screen.dart'"));
    expect(source, isNot(contains("../features/auth/")));
    expect(source, contains('kRemoteAccountEnrollmentEnabled'));
    expect(source, contains('LocalDeviceEnrollmentScreen'));
    expect(source, contains('certified_fr.LoginScreen'));
    expect(source, contains('mena.LoginScreen'));
  });

  test('local enrollment screen does not request remote credentials', () {
    final source = File(
      'lib/features/auth/local_device_enrollment_screen.dart',
    ).readAsStringSync();

    expect(source, contains('enrollLocalDevice()'));
    expect(source, contains("context.go('/app-lock/setup')"));
    expect(source, isNot(contains("context.go('/onboarding')")));
    expect(source, isNot(contains('registerWithEmail')));
    expect(source, isNot(contains('signInWithEmail')));
    expect(source, isNot(contains('TextField(')));
    expect(source, isNot(contains('password')));
    expect(source, isNot(contains('email')));
  });

  test('local enrollment copy keeps explicit EN FR AR parity', () {
    final source = File(
      'lib/core/localization/auth_localized_copy.dart',
    ).readAsStringSync();

    const getters = <String>[
      'localEnrollmentEyebrow',
      'localEnrollmentTitle',
      'localEnrollmentSubtitle',
      'localEnrollmentOffline',
      'localEnrollmentSecurity',
      'localEnrollmentAction',
      'localEnrollmentFooter',
      'localEnrollmentFailed',
    ];

    for (final getter in getters) {
      expect(source, contains('String get $getter'));
    }
    expect(source, contains("'ar' => ar"));
    expect(source, contains("'fr' => fr"));
    expect(source, contains('_ => en'));
  });
}
