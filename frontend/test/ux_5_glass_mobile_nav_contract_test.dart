import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('UX-5 mobile shell uses a glass navigation rail with a gliding pill', () {
    final source = File(
      'lib/features/navigation/main_shell.dart',
    ).readAsStringSync();

    expect(source, contains("import 'dart:ui';"));
    expect(source, contains('BackdropFilter('));
    expect(source, contains('ImageFilter.blur(sigmaX: 20, sigmaY: 20)'));
    expect(source, contains('AnimatedPositioned('));
    expect(source, contains('AminaMotion.navSelection'));
    final motion = File('lib/core/motion/amina_motion.dart').readAsStringSync();
    expect(motion, contains('navSelection = Duration(milliseconds: 240)'));
    expect(source, contains('HapticFeedback.selectionClick()'));
    expect(source, contains("ValueKey('mobile-nav-\${entry.route}')"));
    expect(source, contains('selected: selected'));
    expect(source, contains('label: label'));
    expect(
      RegExp(
        r'GoRouter\.of\(\s*context,?\s*\)\s*\.go\(mobileEntries\[index\]\.route\)',
      ).hasMatch(source),
      isTrue,
    );
    expect(source, contains("entry.route != '/importer'"));
    expect(source, contains("ValueKey('mobile-nav-add')"));
    expect(
      source,
      contains('EdgeInsets.symmetric(horizontal: 18).copyWith(bottom: 6)'),
    );
    expect(source, isNot(contains('EdgeInsets.fromLTRB')));
    expect(source, isNot(contains('child: NavigationBar(')));
  });
}
