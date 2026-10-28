import 'dart:js_interop';
import 'dart:typed_data';

/// W02 Chrome-only test bridge. This library is NEVER imported by application
/// routes or AppDatabase; no clinical authorization or recovery is supplied.
/// The JS module is loaded only from the audited loopback fixture server.
@JS()
extension type _SyntheticW02BrowserModule._(JSObject _) implements JSObject {
  external JSString createSyntheticSecret();
  external JSString createSyntheticSlot();
  external JSPromise<_SyntheticW02Session> openSyntheticBrowserBridge(
    JSString vaultId,
    JSString slot,
    JSString recoverySecret,
    JSNumber minimumRevision,
    JSBoolean allowEmpty,
  );
}

@JS()
extension type _SyntheticW02Session._(JSObject _) implements JSObject {
  external JSUint8Array? get snapshot;
  external JSNumber get revision;
  external JSPromise<JSNumber> commit(JSUint8Array bytes);
  external JSPromise<JSString> envelopeSha256();
  external void close();
}

/// JS-backed ciphertext session with in-memory SQLite snapshots transferred as
/// typed arrays, never as JSON/base64 text. AppDatabase remains fail-closed.
final class W02SyntheticBrowserBridge {
  final _SyntheticW02BrowserModule _module;
  const W02SyntheticBrowserBridge._(this._module);

  static Future<W02SyntheticBrowserBridge> load(Uri url) async {
    if (url.scheme != 'http' ||
        url.host != '127.0.0.1' ||
        url.port != 7399 ||
        url.path != '/iamina_w02_browser_bridge_probe.mjs' ||
        url.hasQuery ||
        url.hasFragment) {
      throw StateError('w02_test_bridge_must_be_loopback');
    }
    final jsModule = await importModule(url.toString().toJS).toDart;
    return W02SyntheticBrowserBridge._(_SyntheticW02BrowserModule._(jsModule));
  }

  String newSyntheticSecret() => _module.createSyntheticSecret().toDart;
  String newSyntheticSlot() => _module.createSyntheticSlot().toDart;

  Future<W02SyntheticBrowserSession> open({
    required String vaultId,
    required String slot,
    required String secret,
    required int revisionFloor,
    required bool allowSyntheticEmpty,
  }) async {
    final jsSession = await _module
        .openSyntheticBrowserBridge(
          vaultId.toJS,
          slot.toJS,
          secret.toJS,
          revisionFloor.toJS,
          allowSyntheticEmpty.toJS,
        )
        .toDart;
    return W02SyntheticBrowserSession._(jsSession);
  }
}

final class W02SyntheticBrowserSession {
  final _SyntheticW02Session _session;
  bool _closed = false;
  W02SyntheticBrowserSession._(this._session);

  Uint8List? takeAuthenticatedSnapshot() {
    if (_closed) throw StateError('w02_browser_bridge_closed');
    final jsBytes = _session.snapshot;
    if (jsBytes == null) return null;
    // Copy the bytes; the JS-owned buffer is zeroized on session.close().
    return Uint8List.fromList(jsBytes.toDart);
  }

  int get revision {
    if (_closed) throw StateError('w02_browser_bridge_closed');
    return _session.revision.toDartInt;
  }

  Future<int> commit(Uint8List snapshot) async {
    if (_closed) throw StateError('w02_browser_bridge_closed');
    if (snapshot.isEmpty) throw StateError('w02_empty_snapshot');
    // JSUint8Array marshaling; no plaintext JSON or persistent temporary file.
    return (await _session.commit(snapshot.toJS).toDart).toDartInt;
  }

  /// SHA-256 digest of the authenticated encrypted envelope only.
  /// Matches the server Option A canonical [format,version,revision,nonce,ciphertext].
  Future<String> envelopeSha256() async {
    if (_closed) throw StateError('w02_browser_bridge_closed');
    return (await _session.envelopeSha256().toDart).toDart;
  }

  void close() {
    if (_closed) return;
    _closed = true;
    _session.close();
  }
}
