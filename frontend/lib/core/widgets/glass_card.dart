import 'dart:ui';
import 'package:flutter/material.dart';
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
    this.opacity = 0.75,
    this.padding,
    this.color,
    this.border,
    this.width,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(
          borderRadius ?? AminaTheme.radius2XL,
        ),
        boxShadow: AminaTheme.shadowGlass(isDark),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(
          borderRadius ?? AminaTheme.radius2XL,
        ),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color:
                  (color ??
                          (isDark ? AminaTheme.surfaceDarkCard : Colors.white))
                      .withValues(alpha: opacity),
              borderRadius: BorderRadius.circular(
                borderRadius ?? AminaTheme.radius2XL,
              ),
              border:
                  border ??
                  Border.all(
                    color: (isDark ? const Color(0xFF38BDF8) : Colors.white)
                        .withValues(alpha: isDark ? 0.15 : 0.3),
                  ),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}
