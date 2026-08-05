import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

/// Compile-time policy for deterministic visual-certification access.
///
/// The mode is disabled unless the build explicitly opts in. Even then, it is
/// accepted only for loopback origins so an accidentally published bundle
/// cannot expose the audit session or its locale override.
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

  static Locale? requestedLocale(Uri uri) {
    if (!isAllowed(uri)) return null;

    switch (uri.queryParameters['lang']) {
      case 'ar':
        return const Locale('ar');
      case 'fr':
        return const Locale('fr');
      default:
        return null;
    }
  }

  static bool get compiledIn => _compiledIn;
}
