import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('hosted review routes marker-only sessions back to remote login', () {
    final source = File('lib/routes/app_router.dart').readAsStringSync();

    expect(source, contains('kRemoteAccountEnrollmentEnabled'));
    expect(source, contains('!authService.hasRemoteCredential'));
    expect(
      source,
      contains("if (requiresRemoteCredential && !isLoginPage) return '/login';"),
    );
    expect(
      source,
      contains(
        'if (isLoggedIn && isLoginPage && !requiresRemoteCredential)',
      ),
    );
  });
}
