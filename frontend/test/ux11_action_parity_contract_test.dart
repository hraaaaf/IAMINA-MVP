import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'UX-11 dashboard actions and mobile nav preserve approved semantics',
    () {
      final dash = File(
        'lib/features/dashboard/dashboard_convergent_screen.dart',
      ).readAsStringSync();
      for (final label in [
        'Journal',
        'Alimentation',
        'Activité',
        'Médicaments',
        'Rappels',
      ]) {
        expect(dash, contains("'$label'"));
      }
      expect(dash, contains("'/ajouter?focus=meal'"));
      expect(dash, contains("'/ajouter?focus=activity'"));
      expect(dash, contains("'/medications'"));
      expect(dash, contains("'/reminders'"));
      expect(dash, contains("go('/importer')"));

      final module = File(
        'lib/modules/diabetes_module.dart',
      ).readAsStringSync();
      expect(module, contains("'Mesures'"));
      expect(module, contains("'Rapports'"));
      expect(module, contains("route: '/importer'"));

      final shell = File(
        'lib/features/navigation/main_shell.dart',
      ).readAsStringSync();
      expect(shell, contains("entry.route != '/importer'"));
      expect(shell, contains("label: (l10n) => l10n.profile"));
      expect(shell, contains('mobile-nav-add'));
    },
  );
}
