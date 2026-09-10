import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'adaptive sidebar uses injected AuthService instead of raw FirebaseAuth',
    () {
      final source = File(
        'lib/features/navigation/main_shell.dart',
      ).readAsStringSync();
      expect(source, contains('context.watch<AuthService>().firebaseUser'));
      expect(source, isNot(contains('FirebaseAuth.instance.currentUser')));
      expect(
        source,
        isNot(contains("package:firebase_auth/firebase_auth.dart")),
      );
    },
  );
}
