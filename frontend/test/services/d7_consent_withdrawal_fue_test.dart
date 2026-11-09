import 'dart:async';
import 'dart:convert';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/d7_consent_withdrawal.dart';
import 'package:chopper/chopper.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _WithdrawalClient extends ApiClient {
  _WithdrawalClient(this.transport) : super(baseUrl: 'http://localhost:8000');
  final ChopperClient transport;
  @override
  ChopperClient get client => transport;
}

void main() {
  group('D7 FUE C05 — withdrawal is fail-closed and retryable', () {
    late ConsentService consent;
    late List<String> events;
    setUp(() {
      consent = ConsentService()..markVerifiedConsent();
      events = <String>[];
    });
    tearDown(() => consent.dispose());

    Future<void> mark() async { events.add('pending'); }
    Future<void> evidence() async { events.add('evidence'); }
    Future<void> local() async { events.add('local'); }
    Future<void> done() async { events.add('clear_pending'); }

    test('server-confirmed DELETE clears evidence and timestamp in order', () async {
      final result = await withdrawD7AiConsent(
        consent: consent,
        markPending: mark,
        revokeServer: () async {
          events.add('remote');
          expect(consent.hasConsent, isFalse);
          expect(consent.hasWithdrawalPending, isTrue);
          return true;
        },
        clearEvidence: evidence,
        clearLocalRecord: local,
        clearPending: done,
      );
      expect(result, D7WithdrawalResult.confirmed);
      expect(events, ['pending','remote','evidence','local','clear_pending']);
      expect(consent.hasConsent, isFalse);
      expect(consent.hasWithdrawalPending, isFalse);
      expect(consent.hasDeclinedLocally, isTrue);
    });

    test('offline or rejected remote DELETE retains retry and no false receipt', () async {
      final result = await withdrawD7AiConsent(
        consent: consent,
        markPending: mark,
        revokeServer: () async { events.add('remote'); return false; },
        clearEvidence: evidence,
        clearLocalRecord: local,
        clearPending: done,
      );
      expect(result, D7WithdrawalResult.awaitingServer);
      expect(consent.hasConsent, isFalse);
      expect(consent.hasWithdrawalPending, isTrue);
      expect(events, ['pending','remote']);
      final retry = await withdrawD7AiConsent(
        consent: consent,
        markPending: mark,
        revokeServer: () async { events.add('retry_remote'); return true; },
        clearEvidence: evidence,
        clearLocalRecord: local,
        clearPending: done,
      );
      expect(retry, D7WithdrawalResult.confirmed);
      expect(consent.hasWithdrawalPending, isFalse);
      expect(events.last, 'clear_pending');
    });

    test('network exception is unconfirmed rather than a successful revocation', () async {
      final result = await withdrawD7AiConsent(
        consent: consent,
        markPending: mark,
        revokeServer: () async { throw const FormatException('offline'); },
        clearEvidence: evidence,
        clearLocalRecord: local,
        clearPending: done,
      );
      expect(result, D7WithdrawalResult.awaitingServer);
      expect(consent.hasWithdrawalPending, isTrue);
      expect(events, ['pending']);
    });

    test('owner-scoped pending marker write failure blocks request', () async {
      final result = await withdrawD7AiConsent(
        consent: consent,
        markPending: () async { throw StateError('secure storage unavailable'); },
        revokeServer: () async { events.add('remote'); return true; },
        clearEvidence: evidence,
        clearLocalRecord: local,
        clearPending: done,
      );
      expect(result, D7WithdrawalResult.localSafetyFailed);
      expect(consent.hasConsent, isFalse);
      expect(events, isEmpty);
    });

    test('failed local cleanup never clears durable pending flag', () async {
      final result = await withdrawD7AiConsent(
        consent: consent,
        markPending: mark,
        revokeServer: () async { events.add('remote'); return true; },
        clearEvidence: evidence,
        clearLocalRecord: () async { throw StateError('disk full'); },
        clearPending: done,
      );
      expect(result, D7WithdrawalResult.localSafetyFailed);
      expect(consent.hasWithdrawalPending, isTrue);
      expect(events, ['pending','remote','evidence']);
    });

    test('pending state remains denied even after a later profile update', () async {
      consent.markWithdrawalPending();
      expect(consent.hasConsent, isFalse);
      expect(consent.hasDeclinedLocally, isTrue);
      consent.clearVerifiedConsent();
      expect(consent.hasConsent, isFalse);
      expect(consent.hasWithdrawalPending, isTrue);
    });
  });

  group('D7 server evidence must explicitly report revoked state', () {
    late ChopperClient chopper;
    late _WithdrawalClient api;
    http.Response response(Map<String,dynamic> data, int status) =>
        http.Response(jsonEncode(data),status, headers: const {'content-type':'application/json'});

    tearDown(() => chopper.dispose());

    Future<bool> withdraw(Map<String,dynamic> data, int status) async {
      chopper = ChopperClient(
        baseUrl: Uri.parse('http://localhost:8000'),
        client: MockClient((req) async {
          expect(req.method, 'DELETE');
          expect(req.url.path, '/api/v1/account/consent');
          return response(data,status);
        }),
        converter: const JsonConverter(),
      );
      api = _WithdrawalClient(chopper);
      return api.withdrawConsent();
    }

    test('only explicit ai_consent_given false with cleared notice is accepted', () async {
      expect(await withdraw({
        'ai_consent_given': false,
        'notice_version': null,
        'notice_hash': null,
        'locale': null,
      },200), isTrue);
    });
    test('200 with consent still true is never a verified withdrawal', () async {
      expect(await withdraw({
        'ai_consent_given': true,
        'notice_version': 'current',
        'notice_hash': 'abc',
        'locale': 'fr',
      },200), isFalse);
    });
    test('failed HTTP status is not server confirmation', () async {
      expect(await withdraw({'ai_consent_given': false},422), isFalse);
    });
  });
}
