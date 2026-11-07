import 'dart:async';

import 'package:amina/services/web_refresh_c8_coordinator.dart';
import 'package:amina/services/web_refresh_c8_signal_contract.dart';
import 'package:flutter_test/flutter_test.dart';

const tokenA =
    'iamina-web.abcdefgh_1234567890.abcdef_1234567890';
const tokenB =
    'iamina-web.qrstuvwx_1234567890.qrstuvwxyz_123456';

class _FakeSignalBus implements WebRefreshC8SignalBus {
  final List<void Function()> handlers = [];
  int broadcastCount = 0;

  @override
  void listen(void Function() onRevoke) => handlers.add(onRevoke);

  @override
  void broadcastRevocation() {
    broadcastCount += 1;
    for (final callback in List<void Function()>.of(handlers)) {
      callback();
    }
  }

  @override
  void dispose() {}
}

CandidateWebRefreshReply reply(String token, {int ttl = 60}) =>
    CandidateWebRefreshReply(accessBearer: token, expiresInSeconds: ttl);

WebRefreshC8Coordinator make({
  required _FakeSignalBus bus,
  Future<CandidateWebRefreshReply> Function()? refresh,
  Future<bool> Function()? logout,
  bool enabled = true,
  DateTime Function()? clock,
}) =>
    WebRefreshC8Coordinator(
      enabled: enabled,
      signalBus: bus,
      refreshTransport: refresh ?? () async => reply(tokenB),
      logoutTransport: logout ?? () async => true,
      clock: clock,
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('C8 defaults off and refuses unverified/non-family tokens', () async {
    final bus = _FakeSignalBus();
    final disabled = make(bus: bus, enabled: false);
    expect(disabled.bootstrapVerifiedCandidate(
      reply(tokenA), verifiedByBackend: true,
    ), isFalse);
    expect(await disabled.refresh(), isNull);
    expect(disabled.getMemoryBearer(), isNull);
    disabled.dispose();

    final active = make(bus: bus);
    expect(active.bootstrapVerifiedCandidate(
      reply(tokenA), verifiedByBackend: false,
    ), isFalse);
    expect(active.bootstrapVerifiedCandidate(
      reply('iamina.native-token'), verifiedByBackend: true,
    ), isFalse);
    expect(active.bootstrapVerifiedCandidate(
      reply(tokenA, ttl: 901), verifiedByBackend: true,
    ), isFalse);
    expect(active.bootstrapVerifiedCandidate(
      reply(tokenA), verifiedByBackend: true,
    ), isTrue);
    expect(active.hasMemoryAccess, isTrue);
    active.dispose();
  });

  test('C8 single-flight refresh never publishes bearer after logout', () async {
    final bus = _FakeSignalBus();
    final futureReply = Completer<CandidateWebRefreshReply>();
    var calls = 0;
    final client = make(
      bus: bus,
      refresh: () {
        calls += 1;
        return futureReply.future;
      },
    );
    expect(client.bootstrapVerifiedCandidate(
      reply(tokenA), verifiedByBackend: true,
    ), isTrue);
    final a = client.refresh();
    final b = client.refresh();
    expect(calls, 1);
    final logout = client.signOut();
    expect(client.getMemoryBearer(), isNull);
    futureReply.complete(reply(tokenB));
    expect(await a, isNull);
    expect(await b, isNull);
    expect(await logout, isTrue);
    expect(client.getMemoryBearer(), isNull);
    expect(bus.broadcastCount, greaterThanOrEqualTo(1));
    client.dispose();
  });

  test('C8 two coordinators share logout signal without token bytes', () async {
    final bus = _FakeSignalBus();
    final a = make(bus: bus);
    final b = make(bus: bus);
    a.bootstrapVerifiedCandidate(reply(tokenA), verifiedByBackend: true);
    b.bootstrapVerifiedCandidate(reply(tokenB), verifiedByBackend: true);
    expect(a.hasMemoryAccess, isTrue);
    expect(b.hasMemoryAccess, isTrue);
    expect(await b.signOut(), isTrue);
    expect(a.getMemoryBearer(), isNull);
    expect(b.getMemoryBearer(), isNull);
    a.dispose();
    b.dispose();
  });

  test('C8 offline logout reports no remote confirmation yet loses access', () async {
    final bus = _FakeSignalBus();
    final client = make(
      bus: bus,
      logout: () async => throw StateError('offline synthetic'),
    );
    client.bootstrapVerifiedCandidate(reply(tokenA), verifiedByBackend: true);
    final confirmed = await client.signOut();
    expect(confirmed, isFalse);
    expect(client.getMemoryBearer(), isNull);
    client.dispose();
  });

  test('C8 explicit short expiry, reload/new instance never rehydrates', () {
    final bus = _FakeSignalBus();
    var now = DateTime.utc(2026, 11, 7);
    final a = make(bus: bus, clock: () => now);
    a.bootstrapVerifiedCandidate(
      reply(tokenA, ttl: 3), verifiedByBackend: true,
    );
    expect(a.getMemoryBearer(), tokenA);
    now = now.add(const Duration(seconds: 4));
    expect(a.getMemoryBearer(), isNull);
    a.dispose();
    final reloaded = make(bus: bus, clock: () => now);
    expect(reloaded.getMemoryBearer(), isNull);
    reloaded.dispose();
  });

  test('C8 late refresh cannot resurrect after received remote revocation', () async {
    final bus = _FakeSignalBus();
    final delayed = Completer<CandidateWebRefreshReply>();
    final a = make(bus: bus, refresh: () => delayed.future);
    final b = make(bus: bus);
    a.bootstrapVerifiedCandidate(reply(tokenA), verifiedByBackend: true);
    b.bootstrapVerifiedCandidate(reply(tokenB), verifiedByBackend: true);
    final pending = a.refresh();
    await b.signOut();
    delayed.complete(reply(tokenB));
    expect(await pending, isNull);
    expect(a.getMemoryBearer(), isNull);
    a.dispose();
    b.dispose();
  });
}
