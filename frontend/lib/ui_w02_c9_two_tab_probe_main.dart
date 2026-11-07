// W02-F09-C9: CI-ONLY actual Flutter Web two-tab C8 browser probe.
// NEVER imported by the product's real main.dart. No API, cookies, patients,
// storage or real access tokens: only generated shape-correct synthetic bytes.
// ignore_for_file: avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:html' as html;

import 'package:amina/services/web_refresh_c8_coordinator.dart';
import 'package:flutter/widgets.dart';

const _syntheticA =
    'iamina-web.C9_Synthetic_Only_Access_First_1234567890';
const _syntheticB =
    'iamina-web.C9_Synthetic_Only_Access_Next_1234567890';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final body = html.document.body!;
  final state = html.DivElement()..id = 'w02-c9-state';
  final activate = html.ButtonElement()
    ..id = 'w02-c9-activate'
    ..text = 'Synthetic bootstrap';
  final refresh = html.ButtonElement()
    ..id = 'w02-c9-refresh'
    ..text = 'Synthetic delayed refresh';
  final logout = html.ButtonElement()
    ..id = 'w02-c9-logout'
    ..text = 'Synthetic logout';
  final offline = html.ButtonElement()
    ..id = 'w02-c9-offline'
    ..text = 'Simulate no network';
  body
    ..append(state)
    ..append(activate)
    ..append(refresh)
    ..append(logout)
    ..append(offline);

  final isArabic = Uri.base.queryParameters['lang'] == 'ar';
  html.document.documentElement!.dir = isArabic ? 'rtl' : 'ltr';
  state.dataset['lang'] = isArabic ? 'ar' : 'fr';
  state.dataset['direction'] = html.document.documentElement!.dir;

  bool outage = false;
  final coordinator = WebRefreshC8Coordinator(
    enabled: true, // Test-only harness. Product AuthService remains untouched.
    refreshTransport: () async {
      await Future<void>.delayed(const Duration(milliseconds: 750));
      if (outage) throw StateError('Synthetic fetch interrupted');
      return const CandidateWebRefreshReply(
        accessBearer: _syntheticB, expiresInSeconds: 40,
      );
    },
    logoutTransport: () async {
      await Future<void>.delayed(const Duration(milliseconds: 30));
      if (outage) throw StateError('Synthetic logout unreachable');
      return true;
    },
  );

  void publish() {
    final active = coordinator.hasMemoryAccess;
    state.dataset['access'] = active ? 'true' : 'false';
    state.dataset['tokenPresent'] =
        coordinator.getMemoryBearer() == null ? 'false' : 'true';
    html.document.title =
        active ? 'IAMINA_W02_C9_ACTIVE' : 'IAMINA_W02_C9_LOCKED';
  }

  coordinator.addListener(publish);
  publish();

  activate.onClick.listen((_) {
    final ok = coordinator.bootstrapVerifiedCandidate(
      const CandidateWebRefreshReply(
        accessBearer: _syntheticA, expiresInSeconds: 40,
      ),
      verifiedByBackend: true, // synthetic test precondition, NOT attestation
    );
    state.dataset['activateResult'] = ok ? 'success' : 'denied';
    publish();
  });

  refresh.onClick.listen((_) async {
    state.dataset['refreshResult'] = 'pending';
    final value = await coordinator.refresh();
    state.dataset['refreshResult'] = value == null ? 'denied' : 'success';
    publish();
  });

  logout.onClick.listen((_) async {
    state.dataset['logoutResult'] = 'pending';
    final confirmed = await coordinator.signOut();
    state.dataset['logoutResult'] =
        confirmed ? 'confirmed' : 'not_confirmed';
    publish();
  });

  offline.onClick.listen((_) {
    outage = true;
    state.dataset['outage'] = 'true';
  });
}
