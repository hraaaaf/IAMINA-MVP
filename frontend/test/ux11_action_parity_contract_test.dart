import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'UX-11 dashboard actions and mobile nav preserve approved semantics',
    () {
      final today = File(
        'lib/features/dashboard/widgets/dashboard_today_section.dart',
      ).readAsStringSync();
      expect(today, contains("ValueKey('dashboard-secondary-companion')"));
      expect(today, contains("context.go('/companion')"));
      expect(today, contains("ValueKey('dashboard-secondary-import')"));
      expect(today, contains("context.go('/importer')"));

      final module = File(
        'lib/modules/diabetes_module.dart',
      ).readAsStringSync();
      final navBlock = module.split('shellRoutes:').first;
      expect(module, contains("'Mesures'"));
      expect(module, contains("'Rapports'"));
      expect(navBlock, isNot(contains("route: '/importer'")));
      expect(module, contains("path: '/importer'"));
      expect(module, contains('const DashboardCompanionEntryScreen()'));

      final shell = File(
        'lib/features/navigation/main_shell.dart',
      ).readAsStringSync();
      expect(shell, contains("label: (l10n) => l10n.profile"));
      expect(shell, contains('mobile-nav-add'));
    },
  );
}
