import 'package:flutter/material.dart';

import '../theme/amina_visual_language.dart';
import '../theme/app_theme.dart';

/// Canonical patient-facing mobile page chrome.
///
/// Owns safe-area spacing, brand scale, title hierarchy and directional
/// padding so every patient surface speaks the same LOGIN-derived language.
class AminaMobilePageHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final Widget? bottom;
  final bool includeSafeArea;

  const AminaMobilePageHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.bottom,
    this.includeSafeArea = true,
  });

  @override
  Widget build(BuildContext context) {
    final top = includeSafeArea ? MediaQuery.paddingOf(context).top : 0.0;
    final hasSubtitle = subtitle != null && subtitle!.trim().isNotEmpty;
    final dark = AminaTheme.isDark(context);

    final chrome = Container(
      constraints: const BoxConstraints(minHeight: 96),
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
      padding: EdgeInsetsDirectional.fromSTEB(20, top + 14, 20, 18),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (leading != null) ...[
            ConstrainedBox(
              constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
              child: Align(
                alignment: AlignmentDirectional.centerStart,
                child: leading!,
              ),
            ),
            const SizedBox(width: 10),
          ],
          ExcludeSemantics(
            child: Container(
              width: 64,
              height: 64,
              padding: const EdgeInsets.all(5),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: .90),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.white.withValues(alpha: .95)),
                boxShadow: AminaVisualLanguage.cardShadowLight,
              ),
              child: Image.asset(
                'assets/images/logo_amina.png',
                fit: BoxFit.contain,
                filterQuality: FilterQuality.high,
              ),
            ),
          ),
          const SizedBox(width: 14),
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
                      fontSize: 24,
                      height: 1.05,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -.55,
                      decoration: TextDecoration.none,
                    ),
                  ),
                ),
                if (hasSubtitle) ...[
                  const SizedBox(height: 6),
                  Text(
                    subtitle!,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: AminaVisualLanguage.secondary(context),
                      fontSize: 13.5,
                      height: 1.36,
                      fontWeight: FontWeight.w500,
                      decoration: TextDecoration.none,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (trailing != null) ...[
            const SizedBox(width: 10),
            ConstrainedBox(
              constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
              child: Align(
                alignment: AlignmentDirectional.centerEnd,
                child: trailing!,
              ),
            ),
          ],
        ],
      ),
    );

    if (bottom == null) return chrome;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        chrome,
        ColoredBox(
          color: AminaTheme.bg(context),
          child: Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(20, 0, 20, 14),
            child: bottom!,
          ),
        ),
      ],
    );
  }
}
