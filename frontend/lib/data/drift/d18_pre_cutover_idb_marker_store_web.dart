// D18 Web PRE-CUTOVER ONLY. Browser bridge is injected by the Playwright
// test fixture, NEVER by the actual IAMINA application.
// ignore_for_file: experimental_member_use
import 'dart:convert';
import 'dart:js_interop';
import 'd18_pre_cutover_atomic_promotion.dart';
import 'patient_vault_scope.dart';

@JS('D18_CI_MARKER_STORE')
external _MarkerBridge? get _bridge;

extension type _MarkerBridge(JSObject _) implements JSObject {
  external JSPromise<JSString> read(JSString scope);
  external JSPromise<JSString> compareAndSwap(
    JSString scope, JSString expected, JSString next,
  );
}

/// No plaintext fallback, crypto secrets, or patient data. The test-only JS
/// adapter supplies an actual single-transaction IndexedDB compare-and-swap.
final class D18PreCutoverIndexedDbMarkerStore implements D18CutoverMarkerStore {
  const D18PreCutoverIndexedDbMarkerStore();
  static final RegExp _scope = RegExp(
    r'^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$');
  static final RegExp _hash = RegExp(r'^[a-f0-9]{64}$');

  static String _name(PatientVaultScope s) {
    final n = s.databaseName;
    if (!_scope.hasMatch(n)) throw StateError('D18_CI_MARKER_SCOPE_DENIED');
    return n;
  }

  static _MarkerBridge _api() {
    final b = _bridge;
    if (b == null) throw StateError('D18_CI_MARKER_JS_MISSING');
    return b;
  }

  static void _check(D18CutoverMarker m, String name) {
    if (m.sourceName != name ||
        m.targetName != name + '_d18_cipher_v1' ||
        m.schemaVersion != 12 ||
        !_hash.hasMatch(m.logicalSha256) ||
        !_hash.hasMatch(m.ciphertextSha256)) {
      throw StateError('D18_CI_MARKER_INVALID');
    }
  }

  static String _encode(D18CutoverMarker? m) {
    if (m == null) return 'null';
    return jsonEncode(<String,Object>{
      'v': 1, 'sourceName': m.sourceName, 'targetName': m.targetName,
      'logicalSha256': m.logicalSha256,
      'ciphertextSha256': m.ciphertextSha256,
      'schemaVersion': m.schemaVersion, 'phase': m.phase.name,
    });
  }

  static D18CutoverMarker? _decode(String json, String scope) {
    final data = jsonDecode(json);
    if (data == null) return null;
    const keys = <String>{'v','sourceName','targetName','logicalSha256',
      'ciphertextSha256','schemaVersion','phase'};
    if (data is! Map<String,dynamic> ||
        data.keys.toSet().difference(keys).isNotEmpty ||
        keys.difference(data.keys.toSet()).isNotEmpty ||
        data['v'] != 1 || data['sourceName'] is! String ||
        data['targetName'] is! String ||
        data['logicalSha256'] is! String ||
        data['ciphertextSha256'] is! String ||
        data['schemaVersion'] is! int ||
        data['phase'] is! String) {
      throw StateError('D18_CI_MARKER_CORRUPT');
    }
    final phase = data['phase'] as String;
    if (phase != D18CutoverPhase.prepared.name &&
        phase != D18CutoverPhase.ciphertextActive.name) {
      throw StateError('D18_CI_MARKER_UNKNOWN_PHASE');
    }
    final marker=D18CutoverMarker(
      sourceName:data['sourceName'] as String,
      targetName:data['targetName'] as String,
      logicalSha256:data['logicalSha256'] as String,
      ciphertextSha256:data['ciphertextSha256'] as String,
      schemaVersion:data['schemaVersion'] as int,
      phase:phase == D18CutoverPhase.prepared.name
        ? D18CutoverPhase.prepared : D18CutoverPhase.ciphertextActive,
    );
    _check(marker,scope);
    return marker;
  }

  @override
  Future<D18CutoverMarker?> read(PatientVaultScope scope) async {
    final name=_name(scope);
    final data=await _api().read(name.toJS).toDart;
    return _decode(data.toDart,name);
  }

  @override
  Future<bool> compareAndSwap({
    required PatientVaultScope scope,
    required D18CutoverMarker? expected,
    required D18CutoverMarker next,
  }) async {
    final name=_name(scope);
    _check(next,name);
    if(expected != null)_check(expected,name);
    if(expected == null) {
      if(next.phase != D18CutoverPhase.prepared)
        throw StateError('D18_CI_MARKER_BAD_CREATE');
    } else if(expected.phase != D18CutoverPhase.prepared ||
              next != expected.withPhase(D18CutoverPhase.ciphertextActive)) {
      throw StateError('D18_CI_MARKER_BAD_PROMOTION');
    }
    final ack=await _api().compareAndSwap(
      name.toJS,_encode(expected).toJS,_encode(next).toJS).toDart;
    if(ack.toDart=='true')return true;
    if(ack.toDart=='false')return false;
    throw StateError('D18_CI_MARKER_BAD_ACK');
  }
}
