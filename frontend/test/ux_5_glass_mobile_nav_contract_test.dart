import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'UX-5 mobile shell uses a glass navigation rail with a gliding pill',
    () {
      final source = File(
        'lib/features/navigation/main_shell.dart',
      ).readAsStringSync();

      expect(source, contains("import 'dart:ui';"));
      expect(source, contains('BackdropFilter('));
      expect(source, contains('ImageFilter.blur(sigmaX: 20, sigmaY: 20)'));
      expect(source, contains('AnimatedPositioned('));
      expect(source, contains('Duration(milliseconds: 240)'));
      expect(source, contains('HapticFeedback.selectionClick()'));
      expect(source, contains("ValueKey('mobile-nav-\${entry.route}')"));
      expect(source, contains('selected: selected'));
      expect(source, contains('label: label'));
      expect(source, contains('GoRouter.of(context).go(entries[index].route)'));
      expect(
        source,
        contains('EdgeInsets.symmetric(horizontal: 12).copyWith(bottom: 10)'),
      );
      expect(source, isNot(contains('EdgeInsets.fromLTRB')));
      expect(source, isNot(contains('child: NavigationBar(')));
    },
  );
}
