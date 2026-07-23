import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:amina/l10n/app_localizations.dart';

/// Resolves a localized nav label.
typedef L10nLabel = String Function(AppLocalizations l10n);

/// A navigation destination a module contributes to the shell nav.
class ModuleNavDestination {
  final String route; // e.g. '/dashboard'
  final IconData icon;
  final IconData selectedIcon;
  final L10nLabel label;

  const ModuleNavDestination({
    required this.route,
    required this.icon,
    required this.selectedIcon,
    required this.label,
  });
}

/// A route rendered inside the persistent shell (with nav chrome).
class ModuleShellRoute {
  final String path;
  final Widget Function() builder;
  const ModuleShellRoute({required this.path, required this.builder});
}

/// A full-screen route pushed above the shell (no nav chrome).
class ModuleFullScreenRoute {
  final String path;
  final Widget Function(GoRouterState state) builder;
  const ModuleFullScreenRoute({required this.path, required this.builder});
}

/// Frontend equivalent of the backend ModuleManifest — declares what a condition
/// module contributes to navigation and routing. The chassis (MainShell +
/// app_router) builds nav and routes from the registered modules instead of
/// hardcoding diabetes. See docs/architecture/platform-transformation-plan.md (P6 section).
class ModuleConfig {
  final String id; // matches backend module_name, e.g. 'diabetes'
  final List<ModuleNavDestination> navDestinations;
  final List<ModuleShellRoute> shellRoutes;
  final List<ModuleFullScreenRoute> fullScreenRoutes;

  const ModuleConfig({
    required this.id,
    this.navDestinations = const [],
    this.shellRoutes = const [],
    this.fullScreenRoutes = const [],
  });
}
