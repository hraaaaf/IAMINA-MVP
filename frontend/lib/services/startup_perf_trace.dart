import 'package:flutter/foundation.dart' show kIsWeb;

import 'startup_perf_trace_stub.dart'
    if (dart.library.js_interop) 'startup_perf_trace_web.dart' as browser;

/// Opt-in, web-only performance marks: no patient data, accounts or egress.
/// Both the explicit build flag and ?startup_perf=1 must be present.
abstract final class StartupPerfTrace {
  static const bool compiledIn = bool.fromEnvironment(
    'IAMINA_STARTUP_TRACE', defaultValue: false,
  );

  static bool get enabled =>
      compiledIn && kIsWeb && Uri.base.queryParameters['startup_perf'] == '1';

  static void mark(String phase) {
    if (!enabled) return;
    const phases = <String>{
      'main_enter', 'binding_ready', 'firebase_stage_ready', 'auth_ready',
      'legacy_probe_ready', 'scoped_probe_ready', 'lock_ready',
      'locale_refresh_started', 'vault_reconcile_ready', 'runapp_begin',
      'runapp_return', 'vault_binding_begin', 'vault_binding_ready',
      'guest_shell_post_frame', 'patient_shell_post_frame',
      'pending_shell_post_frame', 'unlock_event',
    };
    if (!phases.contains(phase)) return;
    browser.mark('iamina.startup.$phase');
  }
}
