import 'package:flutter/material.dart';

import '../theme/amina_visual_language.dart';
import '../theme/app_theme.dart';

/// Canonical compact page chrome for patient-facing mobile surfaces.
///
/// The component owns safe-area spacing, visual hierarchy and directional
/// padding so screens inherit the same calm premium language as LOGIN.
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
    final dark = AminaTheme.isDark(context);

    return Container(
      decoration: BoxDecoration(
        color: AminaTheme.bg(context),
        border: Border(
          bottom: BorderSide(
            color: AminaTheme.divider(context).withValues(alpha: .7),
          ),
        ),
        gradient: dark
            ? null
            : LinearGradient(
                colors: [
                  AminaVisualLanguage.mintSurface.withValues(alpha: .34),
                  AminaTheme.paper.withValues(alpha: .98),
                  AminaTheme.paper,
                ],
                stops: const [0, .42, 1],
                begin: AlignmentDirectional.topStart,
                end: AlignmentDirectional.bottomEnd,
              ),
      ),
      padding: EdgeInsetsDirectional.fromSTEB(
        24,
        top + 14,
        24,
        bottom == null ? 16 : 13,
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
                  width: 3,
                  height: hasSubtitle ? 38 : 31,
                  decoration: BoxDecoration(
                    gradient: AminaVisualLanguage.primaryGradient,
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
                          color: AminaVisualLanguage.primaryText(context),
                          fontSize: 21,
                          height: 1.08,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -.45,
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
                          color: AminaVisualLanguage.secondary(context),
                          fontSize: 12.5,
                          height: 1.34,
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
