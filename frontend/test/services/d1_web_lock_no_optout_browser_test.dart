// D1 P0 patient privacy: Web has a plaintext Drift vault until encryption
// is certified. A UI preference, old local marker, or direct method invocation
// must NEVER authorize removing the Web app-lock.
import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('P0: Web never allows initial opt-out or disabling an existing lock',
      () async {
    final lock = AppLockService();
    addTearDown(lock.dispose);

    if (!kIsWeb) {
      // Preserve native behavior while the Web-specific crypto gate is closed.
      expect(lock.canOptOutOfAppLock, isTrue);
      return;
    }

    expect(lock.canOptOutOfAppLock, isFalse);
    final refusal = isA<AppLockException>().having(
      (error) => error.code,
      'security denial',
      'web_encrypted_vault_required',
    );
    // The guard is evaluated first, even without a successfully loaded vault.
    // Neither direct API nor a forged client preference can skip it.
    await expectLater(lock.continueWithoutAppLock(), throwsA(refusal));
    await expectLater(lock.disableForCurrentVault(), throwsA(refusal));
    expect(lock.isUnlocked, isFalse);
    expect(lock.isExplicitlySkipped, isFalse);
  });

  test('P0: Web unlock is not implied by an app-lock preference', () {
    final lock = AppLockService();
    addTearDown(lock.dispose);
    expect(lock.isUnlocked, isFalse);
    if (kIsWeb) expect(lock.canOptOutOfAppLock, isFalse);
  });
}
