import 'dart:async';

// Browser-only binding to the SAME script used by real Flutter Web.
import 'dart:js_interop';

import 'd18_source_lock_lease.dart';

@JS('IAMINA_D18_SOURCE_BARRIER')
external _SourceBarrierBridge? get _bridge;

extension type _SourceBarrierBridge(JSObject _) implements JSObject {
  external JSPromise<JSString> acquireLegacy();
  external JSPromise<JSString> acquireAuditGuest();
  external JSPromise<JSString> acquirePatient(JSString scope);
  external JSPromise<JSBoolean> release(JSString slot);
}

_SourceBarrierBridge _api() {
  final bridge = _bridge;
  if (bridge == null) throw StateError('D18_SOURCE_LOCK_BRIDGE_MISSING');
  return bridge;
}

Future<D18SourceLockLease> _lease(JSPromise<JSString> request) async {
  final slot = (await request.toDart).toDart;
  if (!RegExp(r'^[0-9a-f-]{36}$').hasMatch(slot)) {
    throw StateError('D18_SOURCE_LOCK_BAD_ACK');
  }
  return D18SourceLockLease(() async {
    final released = await _api().release(slot.toJS).toDart;
    if (!released.toDart) throw StateError('D18_SOURCE_LOCK_NOT_RELEASED');
  });
}

Future<D18SourceLockLease> acquireLegacy() => _lease(_api().acquireLegacy());

Future<D18SourceLockLease> acquireAuditGuest() =>
    _lease(_api().acquireAuditGuest());

Future<D18SourceLockLease> acquirePatient(String scope) =>
    _lease(_api().acquirePatient(scope.toJS));
