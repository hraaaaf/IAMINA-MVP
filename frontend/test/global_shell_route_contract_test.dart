import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('persistent navigation is limited to root destinations', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();

    expect(module, contains("route: '/dashboard'"));
    expect(module, contains("route: '/journal'"));
    expect(module, contains("route: '/summary'"));
    expect(module, isNot(contains("route: '/importer'")));

    expect(
      module,
      contains("ModuleFullScreenRoute(\n      path: '/importer'"),
    );
    expect(
      module,
      isNot(contains("ModuleShellRoute(path: '/importer'")),
    );
  });

  test('browser visual audit certifies roots through MainShell only', () {
    final audit = File('lib/ui_browser_audit_main.dart').readAsStringSync();

    expect(audit, contains("import 'features/navigation/main_shell.dart';"));
    expect(
      audit,
      contains('builder: (context, state, child) => MainShell(child: child)'),
    );

    for (final path in ['/dashboard', '/journal', '/summary', '/profile']) {
      expect(audit, contains("path: '$path'"));
    }

    final shellStart = audit.indexOf('ShellRoute(');
    final deepImport = audit.indexOf("path: '/importer'");
    expect(shellStart, greaterThanOrEqualTo(0));
    expect(deepImport, greaterThan(shellStart));

    final shellBlockEnd = audit.indexOf("path: '/importer'");
    final shellBlock = audit.substring(shellStart, shellBlockEnd);
    expect(shellBlock, isNot(contains("path: '/importer'")));
  });
}
