import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('hosted review requires verified remote credential before protected routes', () {
    final source = File('lib/routes/app_router.dart').readAsStringSync();

    expect(source, contains('kRemoteAccountEnrollmentEnabled'));
    expect(source, contains('!authService.isRemoteCredentialVerified'));
    expect(source, contains("return isLoginPage ? null : '/login';"));
  });
}
