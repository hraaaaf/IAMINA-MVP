import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D10 Web cannot opt out until clinical vault encryption is certified',
      () async {
    final lock = AppLockService();
    addTearDown(lock.dispose);

    if (!kIsWeb) {
      // Native functionality is not changed by the Web-only release gate.
      expect(lock.canOptOutOfAppLock, isTrue);
      return;
    }

    // Executed by TD-014 with Flutter test --platform chrome, not inferred
    // from source inspection or a browser-local preference flag.
    expect(lock.canOptOutOfAppLock, isFalse);
    final refusal = isA<AppLockException>().having(
      (error) => error.code,
      'code',
      'web_encrypted_vault_required',
    );
    await expectLater(lock.continueWithoutAppLock(), throwsA(refusal));
    await expectLater(lock.disableForCurrentVault(), throwsA(refusal));
    expect(lock.isUnlocked, isFalse);
    expect(lock.isExplicitlySkipped, isFalse);
  });
}
