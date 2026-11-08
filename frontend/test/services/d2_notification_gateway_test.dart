import 'package:amina/services/d2_notification_gateway.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> envelope({
  bool proactive = false,
  List<Map<String, dynamic>> items = const [],
  int unread = 0,
}) => {
  'purpose': 'd2_in_app_notifications',
  'in_app_enabled': true,
  'browser_push_enabled': false,
  'proactive_opt_in': proactive,
  'unread_count': unread,
  'consent': {
    'locale': 'fr',
    'notice_version': 'd2.inapp.proactivity.2026-11-08.v1',
    'notice_digest': 'a' * 64,
    'notice_text': 'Deux informations non medicales max par semaine.',
  },
  'items': items,
};

Map<String, dynamic> item({
  int id = 1,
  String kind = 'event',
  String code = 'ai_consent_given',
  String? readAt,
}) => {
  'id': id,
  'kind': kind,
  'code': code,
  'created_at': '2026-11-08T18:00:00+00:00',
  'expires_at': '2026-11-15T18:00:00+00:00',
  'read_at': readAt,
};

void main() {
  test('empty is honest and proactive off by default', () {
    final state = D2InboxState.parse(envelope());
    expect(state.items, isEmpty);
    expect(state.proactivityEnabled, isFalse);
    expect(state.unreadCount, 0);
  });

  test('verified event and proactive codes parse, read count stays real', () {
    final state = D2InboxState.parse(envelope(
      proactive: true,
      unread: 1,
      items: [
        item(),
        item(
          id: 2,
          kind: 'proactive',
          code: 'language_pref_available',
          readAt: '2026-11-08T18:01:00+00:00',
        ),
      ],
    ));
    expect(state.items.length, 2);
    expect(state.unreadCount, 1);
    expect(state.items[1].kind, 'proactive');
  });

  test('invented unread count and duplicate identity fail closed', () {
    expect(
      () => D2InboxState.parse(envelope(items: [item()], unread: 0)),
      throwsStateError,
    );
    expect(
      () => D2InboxState.parse(
        envelope(items: [item(), item()], unread: 2),
      ),
      throwsStateError,
    );
  });

  test('unknown events, misleading kinds, and clinical codes rejected', () {
    for (final value in [
      item(code: 'hypoglycemia_urgent'),
      item(code: 'treatment_reminder'),
      item(kind: 'proactive', code: 'ai_consent_given'),
      item(kind: 'event', code: 'language_pref_available'),
      item(kind: 'OS_push'),
    ]) {
      expect(
        () => D2InboxState.parse(envelope(items: [value], unread: 1)),
        throwsStateError,
      );
    }
  });

  test('expired or malformed notice timestamps are refused', () {
    final invalid = item()..['expires_at'] = '2026-11-07T18:00:00+00:00';
    expect(
      () => D2InboxState.parse(envelope(items: [invalid], unread: 1)),
      throwsStateError,
    );
    final naive = item()..['created_at'] = '2026-11-08T18:00:00';
    expect(
      () => D2InboxState.parse(envelope(items: [naive], unread: 1)),
      throwsStateError,
    );
  });

  test('push enabled, unknown notice digest and forged envelope fail closed', () {
    final pushed = envelope()..['browser_push_enabled'] = true;
    expect(() => D2InboxState.parse(pushed), throwsStateError);
    final forged = envelope()..['purpose'] = 'medical_emergency_alerts';
    expect(() => D2InboxState.parse(forged), throwsStateError);
    final wrong = envelope()..['consent'] = <String, dynamic>{
      'locale': 'fr',
      'notice_version': 'not-approved',
      'notice_digest': 'a' * 64,
      'notice_text': 'Unknown',
    };
    expect(() => D2InboxState.parse(wrong), throwsStateError);
  });
}
