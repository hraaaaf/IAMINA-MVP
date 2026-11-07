// W02-F06 security adversarial probe. Real Flutter AuthService instances in two
// distinct Chrome tabs, against disposable localhost Django/PostgreSQL users.
// CI only: no PHI, no hosted deployment, no real identity provider.
// ignore_for_file: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/services/auth_service.dart';
import 'package:flutter/widgets.dart';

const _email = String.fromEnvironment('W02_CI_EMAIL');
const _password = String.fromEnvironment('W02_CI_PASS');

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  html.document.title = 'IAMINA_W02_F06_LOADING';
  if (_email.isEmpty || _password.isEmpty) {
    html.document.title = 'IAMINA_W02_F06_INVALID_FIXTURE';
    return;
  }

  final auth = AuthService();
  final state = html.DivElement()..id = 'w02-f06-state';
  final login = html.ButtonElement()
    ..id = 'w02-f06-login'
    ..text = 'Synthetic sign in';
  final logout = html.ButtonElement()
    ..id = 'w02-f06-logout'
    ..text = 'Synthetic sign out';
  final sample = html.ButtonElement()
    ..id = 'w02-f06-sample'
    ..text = 'Inspect authority';
  html.document.body!
    ..append(state)
    ..append(login)
    ..append(logout)
    ..append(sample);

  void publish() {
    final live = auth.hasRemoteApiCredential;
    state.dataset['remote'] = live ? 'true' : 'false';
    state.dataset['bound'] = auth.boundNativeAccountId == null
        ? 'false' : 'true';
    html.document.title =
        live ? 'IAMINA_W02_F06_ACTIVE' : 'IAMINA_W02_F06_LOCKED';
  }

  auth.addListener(publish);
  await auth.initialize();
  publish();

  login.onClick.listen((_) async {
    state.dataset['loginResult'] = 'in_progress';
    try {
      await auth.signInWithEmail(_email, _password);
      publish();
      state.dataset['loginResult'] = auth.hasRemoteApiCredential
          ? 'success' : 'no_remote_authority';
    } catch (error) {
      state.dataset['loginResult'] = error.runtimeType.toString();
      html.document.title = 'IAMINA_W02_F06_LOGIN_FAILED';
    }
  });

  logout.onClick.listen((_) async {
    state.dataset['logoutResult'] = 'in_progress';
    try {
      await auth.signOut();
      state.dataset['logoutResult'] = 'success';
      publish();
    } catch (error) {
      state.dataset['logoutResult'] = error.runtimeType.toString();
      publish();
    }
  });

  sample.onClick.listen((_) async {
    state.dataset['sampleResult'] = 'in_progress';
    try {
      final token = await auth.getIdToken();
      final scope = await auth.resolvePatientVaultScope();
      // Never return token bytes or patient IDs to the browser proof.
      state.dataset['tokenPresent'] = token == null ? 'false' : 'true';
      state.dataset['scopePresent'] = scope == null ? 'false' : 'true';
      state.dataset['sampleResult'] = 'success';
    } catch (error) {
      state.dataset['sampleResult'] = error.runtimeType.toString();
    }
  });
}
