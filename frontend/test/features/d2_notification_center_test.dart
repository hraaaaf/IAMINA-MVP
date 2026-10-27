import 'package:amina/features/notifications/d2_notification_center_screen.dart';
import 'package:amina/services/d2_consent_gateway.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

D2ConsentStatus sample({bool enabled = false}) => D2ConsentStatus(
  optedIn: enabled,
  noticeText: 'Synthetic preview notice — no delivery',
  noticeVersion: '2026-10-20.d2.1',
  noticeHash: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  locale: 'fr',
);

class FakeGateway implements D2ConsentGateway {
  bool failRead = false;
  int grants = 0;
  int withdrawals = 0;
  D2ConsentStatus current = sample();
  int previewReads = 0;
  D2ObservationPreview? preview;
  int inboxReads = 0;
  int saves = 0;
  int reads = 0;
  int deletes = 0;
  List<D2SavedNotice> saved = const [];
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
    saved = const [];
    return current;
  }
  @override
  Future<List<D2SavedNotice>> inbox() async {
    inboxReads++;
    return saved;
  }
  @override
  Future<List<D2SavedNotice>> savePreview() async {
    saves++;
    saved = [const D2SavedNotice(id: 1, kind: 'meal')];
    return saved;
  }
  @override
  Future<List<D2SavedNotice>> markRead(int id) async {
    reads++;
    saved = [D2SavedNotice(id: id, kind: 'meal', read: true)];
    return saved;
  }
  @override
  Future<List<D2SavedNotice>> removeNotice(int id) async {
    deletes++;
    saved = const [];
    return saved;
  }
  @override
  Future<D2ObservationPreview?> readPreview() async {
    previewReads++;
    return preview;
  }
}

void main() {
  d2PreviewContractTests();
  test('reject inbox claims of real delivery and malformed items', () {
    final valid = <String, dynamic>{
      'delivery_enabled': false,
      'items': [<String, dynamic>{
        'id': 1, 'kind': 'context',
        'created_at': '2026-10-27T10:00:00Z',
        'expires_at': '2026-11-03T10:00:00Z',
        'read_at': null,
      }],
    };
    expect(D2SavedNotice.parseInbox(valid).single.kind, 'context');
    expect(() => D2SavedNotice.parseInbox(
        {...valid, 'delivery_enabled': true}), throwsStateError);
    expect(() => D2SavedNotice.parseInbox({
      ...valid, 'items': [<String, dynamic>{
        ...((valid['items'] as List).single as Map<String, dynamic>),
        'kind': 'emergency',
      }],
    }), throwsStateError);
  });
  test('reject malformed backend payload or delivery-enabled flag', () {
    final valid = <String, dynamic>{
      'purpose': 'proactive_in_app_preview',
      'opted_in': false,
      'delivery_enabled': false,
      'browser_push_enabled': false,
      'notice_text': 'synthetic',
      'notice_version': 'v1',
      'notice_hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
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
    await tester.ensureVisible(find.byKey(const Key('d2-acknowledge-notice')));
    await tester.tap(find.byKey(const Key('d2-acknowledge-notice')));
    await tester.pump();
    expect(tester.widget<FilledButton>(
      find.byKey(const Key('d2-enable-preview-only')),
    ).onPressed, isNotNull);
    await tester.ensureVisible(find.byKey(const Key('d2-enable-preview-only')));
    await tester.tap(find.byKey(const Key('d2-enable-preview-only')));
    await tester.pumpAndSettle();
    expect(gateway.grants, 1);
    expect(gateway.previewReads, 1);
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
    expect(gateway.previewReads, 0);
    expect(gateway.inboxReads, 0);
    expect(gateway.saves, 0);
  });

  testWidgets('governed preview appears only with server opt-in', (tester) async {
    final gateway = FakeGateway()
      ..current = sample(enabled: true)
      ..preview = const D2ObservationPreview(
        kind: 'meal', state: 'new', allowedNextStep: 'MONITOR');
    await tester.pumpWidget(MaterialApp(
      home: D2NotificationCenterScreen(gateway: gateway),
    ));
    await tester.pumpAndSettle();
    expect(gateway.previewReads, 1);
    expect(find.byKey(const Key('d2-governed-preview')), findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('d2-save-preview')));
    await tester.tap(find.byKey(const Key('d2-save-preview')));
    await tester.pumpAndSettle();
    expect(gateway.saves, 1);
    expect(find.byKey(const Key('d2-inbox-item-1')), findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('d2-inbox-item-1')));
    await tester.tap(find.byTooltip('Marquer comme lu'));
    await tester.pumpAndSettle();
    expect(gateway.reads, 1);
    await tester.tap(find.byTooltip('Supprimer'));
    await tester.pumpAndSettle();
    expect(gateway.deletes, 1);
    expect(find.byKey(const Key('d2-empty-inbox')), findsOneWidget);
  });
}


void d2PreviewContractTests() {
  test('only governed nonurgent read-only previews may be rendered', () {
    final valid = <String, dynamic>{
      'status': 'available',
      'attention_budget': 'one_non_urgent_item_per_24h',
      'item': <String, dynamic>{
        'kind': 'meal',
        'state': 'monitoring',
        'allowed_next_step': 'MONITOR',
        'source_version': 'proactive.personal-response.lifecycle.v1',
        'surface_now': false,
        'escalation_class': 'none',
        'evidence_id': 'synthetic-existing-evidence',
        'priority': <String, dynamic>{
          'safety_time_sensitivity': 'non_urgent_observation',
        },
      },
    };
    expect(D2ObservationPreview.fromResponse(valid)!.kind, 'meal');
    expect(D2ObservationPreview.fromResponse({
      ...valid, 'status': 'no_change', 'item': null,
    }), isNull);
    expect(() => D2ObservationPreview.fromResponse({
      ...valid,
      'item': {...(valid['item'] as Map<String, dynamic>),
        'escalation_class': 'emergency'},
    }), throwsStateError);
    expect(() => D2ObservationPreview.fromResponse({
      ...valid,
      'item': {...(valid['item'] as Map<String, dynamic>),
        'source_version': 'unverified'},
    }), throwsStateError);
  });
}
