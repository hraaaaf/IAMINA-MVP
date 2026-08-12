import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class ClinicalCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double? borderRadius;
  final Border? border;
  final double? width;
  final double? height;
  final Color? backgroundColor;

  const ClinicalCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.borderRadius,
    this.border,
    this.width,
    this.height,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      padding: padding,
      decoration: BoxDecoration(
        color: backgroundColor ?? AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(borderRadius ?? 22),
        border: border ?? Border.all(color: AminaTheme.divider(context)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF064E52).withValues(alpha: 0.045),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: child,
    );
  }
}

class CardHead extends StatelessWidget {
  final String title;
  final String? meta;
  final Widget? trailing;

  const CardHead({super.key, required this.title, this.meta, this.trailing});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Flexible(
          child: Text(
            title,
            style: TextStyle(
              fontSize: 15.5,
              fontWeight: FontWeight.w800,
              color: AminaTheme.textPrimary(context),
              letterSpacing: -0.25,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
        const SizedBox(width: 8),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (meta != null)
              Text(
                meta!,
                style: TextStyle(
                  fontSize: 11.5,
                  color: AminaTheme.textSecondary(context),
                  fontWeight: FontWeight.w600,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
            if (trailing != null) ...[
              if (meta != null) const SizedBox(width: 8),
              trailing!,
            ],
          ],
        ),
      ],
    );
  }
}
