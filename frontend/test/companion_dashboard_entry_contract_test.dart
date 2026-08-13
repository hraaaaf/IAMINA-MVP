import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('dashboard primary insight opens companion without changing nav', () {
    final source = File(
      'lib/features/dashboard/dashboard_convergent_screen.dart',
    ).readAsStringSync();

    expect(source, contains("ValueKey('dashboard-companion-insight')"));
    expect(
      source,
      contains("onTap: () => GoRouter.of(context).go('/companion')"),
    );
  });
}
