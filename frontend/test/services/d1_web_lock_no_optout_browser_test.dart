// D1 P0 patient privacy: Web has a plaintext Drift vault until encryption
// is certified. A UI preference, old local marker, or direct method invocation
// must NEVER authorize removing the Web app-lock.
import 'package:amina/features/auth/app_lock_setup_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';

class _MockLock extends Mock implements AppLockService {}

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

  testWidgets('P0 Web first-use screen does not render a no-lock bypass',
      (tester) async {
    if (!kIsWeb) return;
    final lock = _MockLock();
    when(() => lock.capability())
        .thenAnswer((_) async => AppLockCapability.supported);
    when(() => lock.canOptOutOfAppLock).thenReturn(false);

    final router = GoRouter(
      initialLocation: '/app-lock/setup',
      routes: [
        GoRoute(
          path: '/app-lock/setup',
          builder: (_, __) => const AppLockSetupScreen(),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(ChangeNotifierProvider<AppLockService>.value(
      value: lock,
      child: MaterialApp.router(
        routerConfig: router,
        locale: const Locale('fr'),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d30-skip-app-lock')), findsNothing);
    expect(find.text('Continuer sans verrouillage'), findsNothing);
    verifyNever(() => lock.continueWithoutAppLock());
  });

  test('P0: Web unlock is not implied by an app-lock preference', () {
    final lock = AppLockService();
    addTearDown(lock.dispose);
    expect(lock.isUnlocked, isFalse);
    if (kIsWeb) expect(lock.canOptOutOfAppLock, isFalse);
  });
}
