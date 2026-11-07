// CI-only W02-F07: REAL two-tab Web + deliberate double local-storage fault.
// No PHI, token values, or patient IDs are exposed to the browser harness.
// ignore_for_file: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/services/auth_service.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const _email = String.fromEnvironment('W02_CI_EMAIL');
const _password = String.fromEnvironment('W02_CI_PASS');
const _bearerKey = 'iamina_native_access_token';
const _fenceKey = 'iamina_auth_logout_pending_v1';

// Delegates all normal reads/writes/deletes to actual browser secure storage.
// Only after "arm" does it inject THREE independent persistent-operation
// faults: (1) durable pending-logout fence write; (2) bearer deletion;
// (3) fallback bearer-tombstone write. This intentionally preserves the
// original RAW bearer to keep the hardest Web cold-boot adversarial gate.
// Unlike an in-memory fake, the original encrypted browser bytes remain.
class _FaultedBrowserStorage implements FlutterSecureStorage {
  final FlutterSecureStorage _delegate = const FlutterSecureStorage();
  bool active = false;

  Future<String?> _read(String key) => _delegate.read(key: key);

  Future<void> _write(String key, String value) {
    if (active && key == _fenceKey) {
      throw StateError('Synthetic logout fence write unavailable');
    }
    if (active && key == _bearerKey) {
      // Force even the new F05B fallback to fail. The browser test must
      // still prove zero remote authority when the RAW bearer survives.
      throw StateError('Synthetic bearer tombstone write unavailable');
    }
    return _delegate.write(key: key, value: value);
  }

  Future<void> _delete(String key) {
    if (active && key == _bearerKey) {
      throw StateError('Synthetic bearer delete unavailable');
    }
    return _delegate.delete(key: key);
  }

  Future<bool> hasPersistedBearer() async {
    final stored = await _read(_bearerKey);
    return stored != null && stored.startsWith('iamina.');
  }

  @override
  dynamic noSuchMethod(Invocation invocation) {
    final key = invocation.namedArguments[#key] as String?;
    switch (invocation.memberName) {
      case #read:
        return _read(key!);
      case #write:
        return _write(key!, invocation.namedArguments[#value] as String);
      case #delete:
        return _delete(key!);
      default:
        return super.noSuchMethod(invocation);
    }
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  html.document.title = 'IAMINA_W02_F07_LOADING';
  if (_email.isEmpty || _password.isEmpty) {
    html.document.title = 'IAMINA_W02_F07_INVALID_FIXTURE';
    return;
  }

  final _FaultedBrowserStorage? storage =
      Uri.base.queryParameters['fault_storage'] == '1'
          ? _FaultedBrowserStorage()
          : null;
  final auth = AuthService(storage: storage);
  final state = html.DivElement()..id = 'w02-f07-state';
  final login = html.ButtonElement()
    ..id = 'w02-f07-login'
    ..text = 'Synthetic sign in';
  final arm = html.ButtonElement()
    ..id = 'w02-f07-arm'
    ..text = 'Arm synthetic storage failures';
  final logout = html.ButtonElement()
    ..id = 'w02-f07-logout'
    ..text = 'Synthetic logout';
  final sample = html.ButtonElement()
    ..id = 'w02-f07-sample'
    ..text = 'Inspect Boolean authority';
  html.document.body!
    ..append(state)
    ..append(login)
    ..append(arm)
    ..append(logout)
    ..append(sample);

  void publish() {
    final active = auth.hasRemoteApiCredential;
    state.dataset['remote'] = active ? 'true' : 'false';
    state.dataset['bound'] = auth.boundNativeAccountId == null
        ? 'false'
        : 'true';
    final confirmation = auth.lastRemoteLogoutConfirmed;
    state.dataset['serverConfirmed'] = confirmation == null
        ? 'unavailable'
        : confirmation ? 'true' : 'false';
    html.document.title =
        active ? 'IAMINA_W02_F07_ACTIVE' : 'IAMINA_W02_F07_LOCKED';
  }

  Future<void> reportPersistentBytes() async {
    if (storage != null) {
      state.dataset['persistentBearer'] =
          (await storage.hasPersistedBearer()) ? 'true' : 'false';
    } else {
      state.dataset['persistentBearer'] = 'not_instrumented';
    }
  }

  auth.addListener(publish);
  await auth.initialize();
  publish();
  await reportPersistentBytes();

  login.onClick.listen((_) async {
    state.dataset['loginResult'] = 'in_progress';
    try {
      await auth.signInWithEmail(_email, _password);
      publish();
      await reportPersistentBytes();
      state.dataset['loginResult'] = auth.hasRemoteApiCredential
          ? 'success'
          : 'no_remote_authority';
    } catch (error) {
      state.dataset['loginResult'] = error.runtimeType.toString();
      html.document.title = 'IAMINA_W02_F07_LOGIN_FAILED';
    }
  });

  arm.onClick.listen((_) {
    if (storage == null) {
      state.dataset['faultArmed'] = 'not_instrumented';
    } else {
      storage.active = true;
      state.dataset['faultArmed'] = 'true';
    }
  });

  logout.onClick.listen((_) async {
    state.dataset['logoutResult'] = 'in_progress';
    try {
      await auth.signOut();
      state.dataset['logoutResult'] = 'success';
    } catch (_) {
      // The exception type is minified by Flutter release builds.
      // Report the *fact* of a thrown error, not an unstable class name.
      // This remains a hard assertion in the separate browser harness.
      state.dataset['logoutResult'] = 'error';
    } finally {
      publish();
      await reportPersistentBytes();
      state.dataset['logoutSettled'] = 'true';
    }
  });

  sample.onClick.listen((_) async {
    state.dataset['sampleResult'] = 'in_progress';
    try {
      final bearer = await auth.getIdToken();
      final scope = await auth.resolvePatientVaultScope();
      state.dataset['tokenPresent'] = bearer == null ? 'false' : 'true';
      state.dataset['scopePresent'] = scope == null ? 'false' : 'true';
      await reportPersistentBytes();
      state.dataset['sampleResult'] = 'success';
    } catch (error) {
      state.dataset['sampleResult'] = error.runtimeType.toString();
    }
  });
}
