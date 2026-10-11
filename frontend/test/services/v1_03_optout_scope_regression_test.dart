import 'dart:io';

import 'package:amina/services/consent_service.dart';
import 'package:flutter_test/flutter_test.dart';

// Issue #924: local decline is not a global server revocation.
// Restart / cross-device semantics remain a product/privacy decision.
void main() {
  test('local decline masks a currently verified consent without revoking it', () {
    final consent = ConsentService()..markVerifiedConsent();
    expect(consent.hasConsent, isTrue);

    consent.declineLocally();
    expect(consent.hasDeclinedLocally, isTrue);
    expect(consent.hasConsent, isFalse);

    // A newly verified acceptance is the only allowed local re-enable.
    consent.markVerifiedConsent();
    expect(consent.hasDeclinedLocally, isFalse);
    expect(consent.hasConsent, isTrue);
    consent.dispose();
  });

  test('production ApiClient must receive the shared ConsentService', () {
    final source = File('lib/main.dart').readAsStringSync();
    final constructor = source.substring(
      source.indexOf('final apiClient = ApiClient('),
      source.indexOf('final syncService = SyncService('),
    );
    expect(constructor, contains('consentService: consentService'));
  });

  test('patient conversation must inject ConsentService before send', () {
    final source = File(
      'lib/features/companion/companion_conversation_screen.dart',
    ).readAsStringSync();
    expect(source, contains('consentService: context.read<ConsentService>()'));
    expect(source, contains('_service.sendChatMessage(text)'));
  });

  test('isolated browser chat E2E injects synthetic consent explicitly', () {
    final harness = File('lib/ui_companion_chat_e2e_main.dart').readAsStringSync();
    expect(harness, contains('final testConsent = ConsentService()..markVerifiedConsent();'));
    expect(harness, contains('consentService: testConsent,'));

    // This fixture must not be imported into the ordinary app entrypoint.
    final production = File('lib/main.dart').readAsStringSync();
    expect(production, isNot(contains('ui_companion_chat_e2e_main.dart')));
    expect(production, isNot(contains('markVerifiedConsent();')));
  });

  test('device opt-out is restored before patient API clients initialize', () {
    final source = File('lib/main.dart').readAsStringSync();
    final read = source.indexOf('hasPersistedLocalDecline =');
    final consent = source.indexOf('final consentService = ConsentService(');
    final client = source.indexOf('final apiClient = ApiClient(');
    expect(read, greaterThanOrEqualTo(0));
    expect(consent, greaterThan(read));
    expect(client, greaterThan(consent));
    expect(source, contains('initiallyDeclinedLocally: hasPersistedLocalDecline'));
    expect(source, contains('hasPersistedLocalDecline = true;'));
  });

  test('declined patient can revisit consent only by deliberate navigation', () {
    final router = File('lib/routes/app_router.dart').readAsStringSync();
    final profile = File(
      'lib/features/profile/profile_screen_presentation.dart',
    ).readAsStringSync();
    expect(router, contains('if (hasConsent && isConsentPage) return _homeRoute();'));
    expect(
      router,
      isNot(contains('if ((hasConsent || hasDeclined) && isConsentPage)')),
    );
    expect(profile, contains("key: const ValueKey('profile-ai-reaccept')"));
    expect(profile, contains("onPressed: () => context.go('/consent')"));
    expect(profile, contains('if (consent.hasDeclinedLocally)'));
  });

  test('refusal is persisted before UI navigation and cleared after reaccept', () {
    final screen = File(
      'lib/features/auth/consent_screen.dart',
    ).readAsStringSync();
    final decline = screen.substring(
      screen.indexOf('Future<void> _declineWithoutAI()'),
      screen.indexOf('@override', screen.indexOf('Future<void> _declineWithoutAI()')),
    );
    expect(decline, contains('declineLocally(notify: false)'));
    expect(decline.indexOf('await evidenceStore.persistLocalDecline()'),
        lessThan(decline.indexOf("context.go('/dashboard')")));
    expect(screen.indexOf('await evidenceStore.clearPersistedLocalDecline()'),
        lessThan(screen.indexOf('consent.markVerifiedConsent()')));
  });

  test('Continue without AI stays distinct from profile server withdrawal', () {
    final onboarding = File(
      'lib/features/auth/consent_screen.dart',
    ).readAsStringSync();
    final decline = onboarding.substring(
      onboarding.indexOf('void _declineWithoutAI()'),
      onboarding.indexOf('@override', onboarding.indexOf('void _declineWithoutAI()')),
    );
    expect(decline, contains('declineLocally()'));
    expect(decline, isNot(contains('withdrawConsent()')));

    final profile = File(
      'lib/features/profile/profile_screen.dart',
    ).readAsStringSync();
    expect(profile, contains('final withdrawn = await api.withdrawConsent();'));
    expect(profile, contains('consent.clearVerifiedConsent();'));
  });
}
