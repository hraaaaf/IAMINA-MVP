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
        color: backgroundColor ?? AminaTheme.cardBg,
        borderRadius: BorderRadius.circular(borderRadius ?? AminaTheme.radius2XL),
        border: border ?? Border.all(color: AminaTheme.ink100),
        boxShadow: AminaTheme.shadowClinical,
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
            title.toUpperCase(),
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: AminaTheme.ink500,
              letterSpacing: 0.08,
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
                style: const TextStyle(
                  fontSize: 12,
                  color: AminaTheme.ink400,
                  fontFeatures: [FontFeature.tabularFigures()],
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
