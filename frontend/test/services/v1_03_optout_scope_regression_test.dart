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
