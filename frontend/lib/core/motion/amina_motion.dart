import 'package:flutter/material.dart';

/// Shared motion language for IAmina.
///
/// Motion clarifies hierarchy and state changes without competing with clinical
/// content. Durations resolve to zero when the platform requests reduced motion.
abstract final class AminaMotion {
  static const Duration instant = Duration.zero;
  static const Duration fast = Duration(milliseconds: 160);
  static const Duration standard = Duration(milliseconds: 220);
  static const Duration navSelection = Duration(milliseconds: 240);
  static const Duration emphasized = Duration(milliseconds: 280);

  static const Curve enter = Curves.easeOutCubic;
  static const Curve exit = Curves.easeInCubic;
  static const Curve standardCurve = Curves.easeInOutCubic;

  static bool reduce(BuildContext context) {
    final media = MediaQuery.maybeOf(context);
    return media?.disableAnimations == true ||
        media?.accessibleNavigation == true;
  }

  static Duration resolve(BuildContext context, Duration duration) {
    return reduce(context) ? instant : duration;
  }
}
