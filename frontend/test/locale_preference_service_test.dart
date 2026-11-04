import 'dart:io';

import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:amina/services/api_client.dart';
import 'package:chopper/chopper.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

// A client getter spy proves whether refresh even attempts to construct a
// remote request. It never opens a network connection or patient storage.
class _CountingApiClient extends ApiClient {
  _CountingApiClient() : super(baseUrl: 'http://localhost:8000');
  int clientAccesses = 0;

  @override
  ChopperClient get client {
    clientAccesses++;
    throw StateError('Synthetic test: network must never be used');
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('guest refresh preserves local Arabic without even accessing API client',
      () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina.ui_language': 'ar',
      'iamina.locale_explicitly_selected': 'true',
    });
    final api = _CountingApiClient();
    final service = LocalePreferenceService(
      api,
      systemLocale: const Locale('fr'),
    );
    addTearDown(service.dispose);

    await service.refresh();
    expect(api.clientAccesses, 0);
    expect(service.locale.languageCode, 'ar');
    expect(service.resolutionSource, LocaleResolutionSource.explicitLocal);
  });

  test('remote locale access tracks revocable verified-session permission',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    var verifiedAccount = false;
    final api = _CountingApiClient();
    final service = LocalePreferenceService(
      api,
      canFetchRemoteAccountLocale: () => verifiedAccount,
      systemLocale: const Locale('fr'),
    );
    addTearDown(service.dispose);

    await service.refresh();
    expect(api.clientAccesses, 0, reason: 'guest before sign-in');

    verifiedAccount = true;
    await service.refresh();
    expect(api.clientAccesses, 1, reason: 'verified session may try remote');

    verifiedAccount = false;
    await service.refresh();
    expect(api.clientAccesses, 1, reason: 'logout must block new requests');
    expect(service.locale.languageCode, 'fr');
  });

  test('audit locale cannot access remote client even if callback allows it',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    final api = _CountingApiClient();
    final service = LocalePreferenceService(
      api,
      auditLocale: const Locale('ar'),
      canFetchRemoteAccountLocale: () => true,
      systemLocale: const Locale('fr'),
    );
    addTearDown(service.dispose);

    await service.refresh();
    expect(api.clientAccesses, 0);
    expect(service.resolutionSource, LocaleResolutionSource.audit);
    expect(service.locale.languageCode, 'ar');
  });

  test('remote account locale is denied by default for guests and audit', () {
    // D37-A: a missing verified remote identity can never authorize a fetch.
    for (final audit in [false, true]) {
      for (final demo in [false, true]) {
        expect(
          shouldFetchRemoteAccountLocale(
            hasVerifiedRemoteAccount: false,
            isAuditLocale: audit,
            isOfflineDemo: demo,
          ),
          isFalse,
        );
      }
    }
    expect(
      shouldFetchRemoteAccountLocale(
        hasVerifiedRemoteAccount: true,
        isAuditLocale: true,
        isOfflineDemo: false,
      ),
      isFalse,
    );
    expect(
      shouldFetchRemoteAccountLocale(
        hasVerifiedRemoteAccount: true,
        isAuditLocale: false,
        isOfflineDemo: true,
      ),
      isFalse,
    );
  });

  test('verified remote account is the sole eligible profile locale state', () {
    expect(
      shouldFetchRemoteAccountLocale(
        hasVerifiedRemoteAccount: true,
        isAuditLocale: false,
        isOfflineDemo: false,
      ),
      isTrue,
    );
  });

  test('production locale wiring checks native credential, proof and scope', () {
    // Source-level regression pin; focused network/browser test remains
    // required in the L01 synthetic FUE matrix.
    final app = File('lib/main.dart').readAsStringSync();
    expect(app, contains('canFetchRemoteAccountLocale: () =>'));
    expect(app, contains('authService.hasRemoteApiCredential'));
    expect(app, contains('authService.isRemoteCredentialVerified'));
    expect(app, contains('authService.boundNativeAccountId != null'));

    final service = File('lib/services/locale_preference_service.dart')
        .readAsStringSync();
    expect(service, contains('_canFetchRemoteAccountLocale?.call() ?? false'));
    expect(service, contains('epoch == AuthService.authEpoch'));
  });

  test('unsupported language is rejected before deterministic resolution', () {
    expect(LocalePreferenceService.supportedLocale(null), isNull);
    expect(LocalePreferenceService.supportedLocale('es-MA'), isNull);

    final fallback = LocalePreferenceService.resolveLocale(
      systemLocale: const Locale('es', 'MA'),
    );
    expect(fallback.locale.languageCode, 'fr');
    expect(fallback.source, LocaleResolutionSource.baseline);
  });

  test('confirmed languages and regional variants map independently', () {
    expect(
      LocalePreferenceService.supportedLocale('fr')?.languageCode,
      'fr',
    );
    expect(
      LocalePreferenceService.supportedLocale('en-GB')?.languageCode,
      'en',
    );
    expect(
      LocalePreferenceService.supportedLocale('ar-MA')?.languageCode,
      'ar',
    );
  });

  testWidgets('Arabic locale produces RTL directionality', (tester) async {
    TextDirection? direction;

    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('ar'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Builder(
          builder: (context) {
            direction = Directionality.of(context);
            return const SizedBox.shrink();
          },
        ),
      ),
    );

    expect(direction, TextDirection.rtl);
  });
}
