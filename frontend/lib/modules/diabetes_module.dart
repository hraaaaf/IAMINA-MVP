import 'package:flutter/material.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/dashboard/dashboard_convergent_screen.dart';
import '../features/journal/journal_screen.dart';
import '../features/journal/ai_summary_screen.dart';
import '../features/journal/add_log_screen.dart';
import '../features/journal/edit_log_screen.dart';
import '../features/import/import_screen.dart';
import '../features/documents/document_import_screen.dart';
import 'module_config.dart';

/// The diabetes module — the one shipped condition. Declares the same screens,
/// routes, and nav destinations the app used to hardcode, now expressed as a
/// ModuleConfig so the chassis renders them generically.
final ModuleConfig diabetesModule = ModuleConfig(
  id: 'diabetes',
  navDestinations: [
    ModuleNavDestination(
      route: '/dashboard',
      icon: Icons.home_outlined,
      selectedIcon: Icons.home_rounded,
      label: (l) => l.navHome,
    ),
    ModuleNavDestination(
      route: '/summary',
      icon: Icons.auto_awesome_outlined,
      selectedIcon: Icons.auto_awesome,
      label: (l) => l.navIamina,
    ),
    ModuleNavDestination(
      route: '/journal',
      icon: Icons.history_rounded,
      selectedIcon: Icons.history_rounded,
      label: (l) => l.navJournal,
    ),
    ModuleNavDestination(
      route: '/importer',
      icon: Icons.upload_file_outlined,
      selectedIcon: Icons.upload_file,
      label: (l) => l.navImport,
    ),
  ],
  shellRoutes: [
    ModuleShellRoute(
      path: '/dashboard',
      builder: () => LayoutBuilder(
        builder: (context, constraints) => constraints.maxWidth < 700
            ? const DashboardConvergentScreen()
            : const DashboardScreen(),
      ),
    ),
    ModuleShellRoute(path: '/summary', builder: () => const AISummaryScreen()),
    ModuleShellRoute(path: '/journal', builder: () => const JournalScreen()),
    ModuleShellRoute(path: '/importer', builder: () => const ImportScreen()),
  ],
  fullScreenRoutes: [
    ModuleFullScreenRoute(path: '/ajouter', builder: (s) => const AddLogScreen()),
    ModuleFullScreenRoute(path: '/pulper', builder: (s) => const DocumentImportScreen()),
    ModuleFullScreenRoute(
      path: '/journal/:id/edit',
      builder: (s) => EditLogScreen(logId: int.parse(s.pathParameters['id']!)),
    ),
  ],
);
