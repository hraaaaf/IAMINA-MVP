import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Canonical compact page chrome for patient-facing mobile surfaces.
///
/// The component intentionally owns safe-area spacing, visual hierarchy and
/// directional padding so each screen does not invent its own mobile header.
class AminaMobilePageHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final Widget? bottom;
  final bool includeSafeArea;

  const AminaMobilePageHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.trailing,
    this.bottom,
    this.includeSafeArea = true,
  });

  @override
  Widget build(BuildContext context) {
    final top = includeSafeArea ? MediaQuery.paddingOf(context).top : 0.0;
    final hasSubtitle = subtitle != null && subtitle!.trim().isNotEmpty;

    return Container(
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        border: Border(bottom: BorderSide(color: AminaTheme.divider(context))),
      ),
      padding: EdgeInsetsDirectional.fromSTEB(
        20,
        top + 12,
        20,
        bottom == null ? 14 : 12,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            crossAxisAlignment: hasSubtitle
                ? CrossAxisAlignment.start
                : CrossAxisAlignment.center,
            children: [
              ExcludeSemantics(
                child: Container(
                  width: 4,
                  height: hasSubtitle ? 38 : 30,
                  decoration: BoxDecoration(
                    gradient: AminaTheme.heroGradient,
                    borderRadius: BorderRadius.circular(99),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Semantics(
                      header: true,
                      child: Text(
                        title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: AminaTheme.textPrimary(context),
                          fontSize: 20,
                          height: 1.1,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.35,
                        ),
                      ),
                    ),
                    if (hasSubtitle) ...[
                      const SizedBox(height: 4),
                      Text(
                        subtitle!,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: AminaTheme.textSecondary(context),
                          fontSize: 12.5,
                          height: 1.3,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (trailing != null) ...[
                const SizedBox(width: 10),
                ConstrainedBox(
                  constraints: const BoxConstraints(
                    minWidth: 44,
                    minHeight: 44,
                  ),
                  child: Align(
                    alignment: AlignmentDirectional.centerEnd,
                    child: trailing!,
                  ),
                ),
              ],
            ],
          ),
          if (bottom != null) ...[const SizedBox(height: 10), bottom!],
        ],
      ),
    );
  }
}
