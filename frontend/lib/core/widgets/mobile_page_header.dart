import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Canonical page chrome for patient-facing mobile surfaces.
///
/// UX-12 deliberately mirrors the certified Dashboard rhythm: warm canvas,
/// strong title hierarchy, quiet subtitle and a compact circular action surface.
/// The component owns safe-area spacing and directional padding so screens do
/// not invent competing mobile headers.
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
      color: Colors.transparent,
      padding: EdgeInsetsDirectional.fromSTEB(
        18,
        top + 10,
        18,
        bottom == null ? 10 : 8,
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
                          fontSize: 26,
                          height: 1.05,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.8,
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
                          color: AminaTheme.textSecondary(context),
                          fontSize: 13,
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
                Container(
                  width: 44,
                  height: 44,
                  constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
                  alignment: AlignmentDirectional.centerEnd,
                  decoration: BoxDecoration(
                    color: AminaTheme.surface(context),
                    shape: BoxShape.circle,
                    border: Border.all(color: AminaTheme.divider(context)),
                    boxShadow: AminaTheme.shadowClinical,
                  ),
                  child: trailing!,
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
