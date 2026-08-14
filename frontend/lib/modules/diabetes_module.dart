import 'package:flutter/material.dart';
import '../features/companion/companion_premium_screen.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/dashboard/dashboard_companion_entry_screen.dart';
import '../features/dashboard/widgets/add_log_sheet.dart';
import '../features/journal/journal_screen.dart';
import '../features/journal/ai_summary_screen.dart';
import '../features/journal/add_log_screen.dart';
import '../features/journal/edit_log_screen.dart';
import '../features/import/import_screen.dart';
import '../features/documents/document_import_screen.dart';
import '../features/medications/medication_screen.dart';
import '../features/reminders/reminders_screen.dart';
import '../l10n/app_localizations.dart';
import 'module_config.dart';

String _navText(AppLocalizations l, String fr, String en, String ar) {
  final code = l.localeName.split('_').first;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

AddLogFocus _focusFromState(String? value) => switch (value) {
  'meal' => AddLogFocus.meal,
  'activity' => AddLogFocus.activity,
  'insulin' => AddLogFocus.insulin,
  _ => AddLogFocus.none,
};

/// Diabetes condition module. Mobile navigation is filtered by MainShell
/// to preserve the approved four-destination + central-add composition;
/// Import remains available in desktop navigation and by direct route.
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
      route: '/journal',
      icon: Icons.show_chart_rounded,
      selectedIcon: Icons.show_chart_rounded,
      label: (l) => _navText(l, 'Mesures', 'Measurements', 'القياسات'),
    ),
    ModuleNavDestination(
      route: '/summary',
      icon: Icons.description_outlined,
      selectedIcon: Icons.description_rounded,
      label: (l) => _navText(l, 'Rapports', 'Reports', 'التقارير'),
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
            ? const DashboardCompanionEntryScreen()
            : const DashboardScreen(),
      ),
    ),
    ModuleShellRoute(path: '/journal', builder: () => const JournalScreen()),
    ModuleShellRoute(path: '/summary', builder: () => const AISummaryScreen()),
    ModuleShellRoute(path: '/importer', builder: () => const ImportScreen()),
  ],
  fullScreenRoutes: [
    ModuleFullScreenRoute(
      path: '/companion',
      builder: (s) => const CompanionPremiumScreen(),
    ),
    ModuleFullScreenRoute(
      path: '/ajouter',
      builder: (s) =>
          AddLogScreen(focus: _focusFromState(s.uri.queryParameters['focus'])),
    ),
    ModuleFullScreenRoute(
      path: '/medications',
      builder: (s) => const MedicationScreen(),
    ),
    ModuleFullScreenRoute(
      path: '/reminders',
      builder: (s) => const RemindersScreen(),
    ),
    ModuleFullScreenRoute(
      path: '/pulper',
      builder: (s) => const DocumentImportScreen(),
    ),
    ModuleFullScreenRoute(
      path: '/journal/:id/edit',
      builder: (s) => EditLogScreen(logId: int.parse(s.pathParameters['id']!)),
    ),
  ],
);
