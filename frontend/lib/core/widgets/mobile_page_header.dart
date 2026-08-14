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
        gradient: dark
            ? null
            : LinearGradient(
                colors: [
                  AminaVisualLanguage.mintWaveLight.withValues(alpha: .72),
                  AminaTheme.paper.withValues(alpha: .98),
                  AminaTheme.paper,
                ],
                stops: const [0, .50, 1],
                begin: AlignmentDirectional.topStart,
                end: AlignmentDirectional.bottomEnd,
              ),
      ),
      padding: EdgeInsetsDirectional.fromSTEB(
        20,
        top + 12,
        20,
        bottom == null ? 16 : 13,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              ExcludeSemantics(
                child: Container(
                  width: 48,
                  height: 54,
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: .88),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white.withValues(alpha: .92)),
                    boxShadow: AminaVisualLanguage.cardShadowLight,
                  ),
                  child: Image.asset(
                    'assets/images/logo_amina.png',
                    fit: BoxFit.contain,
                    filterQuality: FilterQuality.high,
                  ),
                ),
              ),
              const SizedBox(width: 13),
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
                          fontFamily: 'Georgia',
                          color: AminaVisualLanguage.primaryText(context),
                          fontSize: 23,
                          height: 1.05,
                          fontWeight: FontWeight.w700,
                          letterSpacing: -.55,
                        ),
                      ),
                    ),
                    if (hasSubtitle) ...[
                      const SizedBox(height: 5),
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
          if (bottom != null) ...[const SizedBox(height: 12), bottom!],
        ],
      ),
    );
  }
}
