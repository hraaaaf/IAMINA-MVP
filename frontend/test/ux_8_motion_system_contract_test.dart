import 'dart:io';

import 'package:amina/core/motion/amina_motion.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'UX-8 centralizes premium motion and honors reduced-motion settings',
    () {
      final motion = File(
        'lib/core/motion/amina_motion.dart',
      ).readAsStringSync();
      final router = File('lib/routes/app_router.dart').readAsStringSync();
      final shell = File(
        'lib/features/navigation/main_shell.dart',
      ).readAsStringSync();

      expect(motion, contains('standard = Duration(milliseconds: 220)'));
      expect(motion, contains('navSelection = Duration(milliseconds: 240)'));
      expect(motion, contains('emphasized = Duration(milliseconds: 280)'));
      expect(motion, contains('disableAnimations == true'));
      expect(motion, contains('accessibleNavigation == true'));
      expect(motion, contains('return reduce(context) ? instant : duration'));

      expect(router, contains("import '../core/motion/amina_motion.dart';"));
      expect(router, contains('transitionDuration: AminaMotion.standard'));
      expect(router, contains('reverseTransitionDuration: AminaMotion.fast'));
      expect(router, contains('if (AminaMotion.reduce(context)) return child'));
      expect(router, contains('begin: const Offset(0, 0.018)'));
      expect(router, isNot(contains('Duration(milliseconds: 300)')));

      expect(shell, contains("import '../../core/motion/amina_motion.dart';"));
      expect(shell, contains('AminaMotion.navSelection'));
      expect(shell, contains('AminaMotion.fast'));
      expect(shell, contains('AminaMotion.standardCurve'));
      expect(shell, isNot(contains('Duration(milliseconds: 240)')));
    },
  );

  testWidgets('UX-8 resolves standard motion to zero when animations are disabled', (
    tester,
  ) async {
    Duration? resolved;
    bool? reduced;

    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(disableAnimations: true),
        child: MaterialApp(
          home: Builder(
            builder: (context) {
              reduced = AminaMotion.reduce(context);
              resolved = AminaMotion.resolve(context, AminaMotion.standard);
              return const SizedBox.shrink();
            },
          ),
        ),
      ),
    );

    expect(reduced, isTrue);
    expect(resolved, Duration.zero);
  });

  testWidgets('UX-8 also reduces motion for accessible navigation', (
    tester,
  ) async {
    Duration? resolved;

    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(accessibleNavigation: true),
        child: MaterialApp(
          home: Builder(
            builder: (context) {
              resolved = AminaMotion.resolve(
                context,
                AminaMotion.navSelection,
              );
              return const SizedBox.shrink();
            },
          ),
        ),
      ),
    );

    expect(resolved, Duration.zero);
  });
}
