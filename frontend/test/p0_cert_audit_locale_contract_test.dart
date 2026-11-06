import 'dart:io';

import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('audit locale is available only behind the certified access policy', () {
    final policy = _read('lib/services/audit_access_policy.dart');

    expect(policy, contains('static Locale? requestedLocale(Uri uri)'));
    expect(policy, contains('if (!isAllowed(uri)) return null'));
    expect(policy, contains("queryParameters['lang']"));
    expect(policy, contains("case 'fr':"));
    expect(policy, contains("case 'ar':"));
    expect(policy, isNot(contains("case 'en':")));
    expect(policy, contains('default:'));
    expect(policy, contains('return null;'));
  });

  test('audit locale bypasses remote preference lookup and has top priority', () {
    final localeService = _read('lib/services/locale_preference_service.dart');
    final main = _read('lib/main.dart');

    expect(localeService, contains('final Locale? _auditLocale'));
    expect(localeService, contains('auditLocale: _auditLocale'));
    expect(localeService, contains('LocaleResolutionSource.audit'));
    // The remote-account policy is deliberately evaluated *before* a
    // patient-profile request; keep the audit exclusion as executable policy.
    expect(
      shouldFetchRemoteAccountLocale(
        hasVerifiedRemoteAccount: true,
        isAuditLocale: true,
        isOfflineDemo: false,
      ),
      isFalse,
    );
    expect(localeService, contains('isAuditLocale: _auditLocale != null'));
    expect(
      localeService.indexOf('shouldFetchRemoteAccountLocale(',
          localeService.indexOf('Future<void> refresh()')),
      lessThan(localeService.indexOf("Uri.parse('/api/v1/profile/locale')")),
    );

    expect(main, contains('AuditAccessPolicy.requestedLocale(Uri.base)'));
    expect(main, contains('auditLocale: auditAllowed'));
  });

  testWidgets('certified Arabic locale resolves to RTL', (tester) async {
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
