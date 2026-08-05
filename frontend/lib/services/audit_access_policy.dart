import 'package:flutter/foundation.dart';

/// Compile-time policy for deterministic visual-certification access.
///
/// The mode is disabled unless the build explicitly opts in. Even then, it is
/// accepted only for loopback origins so an accidentally published bundle
/// cannot expose the audit session.
abstract final class AuditAccessPolicy {
  static const bool _compiledIn = bool.fromEnvironment(
    'IAMINA_AUDIT_ACCESS',
    defaultValue: false,
  );

  static bool isAllowed(Uri uri) {
    if (!_compiledIn || !kIsWeb) return false;
    if (uri.queryParameters['audit'] != 'visual-cert') return false;

    final host = uri.host.toLowerCase();
    return host == 'localhost' || host == '127.0.0.1' || host == '::1';
  }

  static bool get compiledIn => _compiledIn;
}
