import 'package:amina/features/notifications/d2_notification_center_screen.dart';
import 'package:amina/services/d2_consent_gateway.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

D2ConsentStatus sample({bool enabled = false}) => D2ConsentStatus(
  optedIn: enabled,
  noticeText: 'Synthetic preview notice — no delivery',
  noticeVersion: '2026-10-20.d2.1',
  noticeHash: 'a' * 64,
  locale: 'fr',
);

class FakeGateway implements D2ConsentGateway {
  bool failRead = false;
  int grants = 0;
  int withdrawals = 0;
  D2ConsentStatus current = sample();
  @override
  Future<D2ConsentStatus> read(String locale) async {
    if (failRead) throw StateError('offline');
    return current;
  }
  @override
  Future<D2ConsentStatus> grant(D2ConsentStatus notice) async {
    grants++;
    current = sample(enabled: true);
    return current;
  }
  @override
  Future<D2ConsentStatus> withdraw(String locale) async {
    withdrawals++;
    current = sample();
    return current;
  }
}

void main() {
  test('reject malformed backend payload or delivery-enabled flag', () {
    final valid = <String, dynamic>{
      'purpose': 'proactive_in_app_preview',
      'opted_in': false,
      'delivery_enabled': false,
      'browser_push_enabled': false,
      'notice_text': 'synthetic',
      'notice_version': 'v1',
      'notice_hash': 'a' * 64,
      'locale': 'fr',
      'granted_at': null,
    };
    expect(D2ConsentStatus.fromResponse(valid).optedIn, isFalse);
    expect(() => D2ConsentStatus.fromResponse({
      ...valid, 'browser_push_enabled': true,
    }), throwsStateError);
    expect(() => D2ConsentStatus.fromResponse({
      ...valid, 'delivery_enabled': true,
    }), throwsStateError);
  });

  testWidgets('preview consent requires notice acknowledgment, can revoke',
      (tester) async {
    final gateway = FakeGateway();
    await tester.pumpWidget(MaterialApp(
      home: D2NotificationCenterScreen(gateway: gateway),
    ));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d2-empty-inbox')), findsOneWidget);
    expect(find.text('Synthetic preview notice — no delivery'), findsOneWidget);
    final enable = tester.widget<FilledButton>(
      find.byKey(const Key('d2-enable-preview-only')),
    );
    expect(enable.onPressed, isNull);
    await tester.tap(find.byKey(const Key('d2-acknowledge-notice')));
    await tester.pump();
    expect(tester.widget<FilledButton>(
      find.byKey(const Key('d2-enable-preview-only')),
    ).onPressed, isNotNull);
    await tester.ensureVisible(find.byKey(const Key('d2-enable-preview-only')));
    await tester.tap(find.byKey(const Key('d2-enable-preview-only')));
    await tester.pumpAndSettle();
    expect(gateway.grants, 1);
    expect(find.byKey(const Key('d2-withdraw-consent')), findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('d2-withdraw-consent')));
    await tester.tap(find.byKey(const Key('d2-withdraw-consent')));
    await tester.pumpAndSettle();
    expect(gateway.withdrawals, 1);
    expect(gateway.current.optedIn, false);
  });

  testWidgets('offline failure does not create a fake consent',
      (tester) async {
    final gateway = FakeGateway()..failRead = true;
    await tester.pumpWidget(MaterialApp(
      home: D2NotificationCenterScreen(gateway: gateway),
    ));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d2-error')), findsOneWidget);
    expect(find.byKey(const Key('d2-enable-preview-only')), findsNothing);
    expect(gateway.grants, 0);
  });
}
