import 'dart:ui';

import 'package:flutter/material.dart';

import '../theme/amina_visual_language.dart';
import '../theme/app_theme.dart';

class GlassCard extends StatelessWidget {
  final Widget child;
  final double? borderRadius;
  final double opacity;
  final EdgeInsetsGeometry? padding;
  final Color? color;
  final Border? border;
  final double? width;
  final double? height;

  const GlassCard({
    super.key,
    required this.child,
    this.borderRadius,
    this.opacity = 0.92,
    this.padding,
    this.color,
    this.border,
    this.width,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final radius = borderRadius ?? AminaVisualLanguage.cardRadius;

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        boxShadow: AminaVisualLanguage.cardShadow(context),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 22, sigmaY: 22),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: (color ?? AminaVisualLanguage.cardSurface(context))
                  .withValues(alpha: opacity),
              borderRadius: BorderRadius.circular(radius),
              border: border ??
                  Border.all(
                    color: dark
                        ? AminaTheme.dark600.withValues(alpha: .55)
                        : Colors.white.withValues(alpha: .9),
                  ),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}
