import 'dart:io';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('audit access remains compile-time opt-in and loopback-only', () {
    final policy = _read('lib/services/audit_access_policy.dart');

    expect(policy, contains("'IAMINA_AUDIT_ACCESS'"));
    expect(policy, contains('defaultValue: false'));
    expect(policy, contains('!kIsWeb'));
    expect(policy, contains("queryParameters['audit'] != 'visual-cert'"));
    expect(policy, contains("host == 'localhost'"));
    expect(policy, contains("host == '127.0.0.1'"));
    expect(policy, contains("host == '::1'"));
  });

  test('application can enter audit access only through the policy', () {
    final main = _read('lib/main.dart');
    final auth = _read('lib/services/auth_service.dart');

    expect(main, contains('AuditAccessPolicy.isAllowed(Uri.base)'));
    expect(main, contains('authService.enterAuditSession()'));
    expect(
      main.indexOf('AuditAccessPolicy.isAllowed(Uri.base)'),
      lessThan(main.indexOf('authService.enterAuditSession()')),
    );

    expect(auth, contains('bool _auditSession = false'));
    expect(auth, contains('if (_auditSession) return null'));
    expect(auth, contains('_auditSession = false;'));
    expect(auth, isNot(contains('iamina.audit.')));
  });

  test('audit session is anonymous, in-memory and tokenless', () async {
    final auth = AuthService();
    await auth.initialize();

    auth.enterAuditSession();

    expect(auth.isAuthenticated, isTrue);
    expect(auth.isAnonymous, isTrue);
    expect(auth.isAuditSession, isTrue);
    expect(await auth.getIdToken(), isNull);
    expect(await auth.refreshToken(), isNull);

    await auth.signOut();
    expect(auth.isAuditSession, isFalse);
    auth.dispose();
  });
}
