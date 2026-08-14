import 'package:flutter/material.dart';

import '../theme/amina_visual_language.dart';
import '../theme/app_theme.dart';

/// Shared first-use surface for truthful empty states.
///
/// This widget only presents copy and real actions supplied by the caller. It
/// never invents patient values, metrics, trends, recommendations or defaults.
class AminaFirstUsePanel extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  final String? eyebrow;
  final String? primaryActionLabel;
  final VoidCallback? onPrimaryAction;
  final String? secondaryActionLabel;
  final VoidCallback? onSecondaryAction;
  final String? note;
  final bool compact;

  const AminaFirstUsePanel({
    super.key,
    required this.icon,
    required this.title,
    required this.body,
    this.eyebrow,
    this.primaryActionLabel,
    this.onPrimaryAction,
    this.secondaryActionLabel,
    this.onSecondaryAction,
    this.note,
    this.compact = false,
  }) : assert(
         (primaryActionLabel == null) == (onPrimaryAction == null),
         'Primary action label and callback must be supplied together.',
       ),
       assert(
         (secondaryActionLabel == null) == (onSecondaryAction == null),
         'Secondary action label and callback must be supplied together.',
       );

  @override
  Widget build(BuildContext context) {
    final shortViewport = MediaQuery.sizeOf(context).height <= 600;
    final dense = compact || shortViewport;

    return LayoutBuilder(
      builder: (context, constraints) {
        final hasActions = primaryActionLabel != null;
        final wide = constraints.maxWidth >= 720 && !dense && hasActions;
        final iconSize = dense ? 46.0 : 54.0;
        final padding = dense ? 18.0 : 24.0;

        final intro = Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: iconSize,
              height: iconSize,
              decoration: AminaVisualLanguage.mintIconDecoration(context),
              child: Icon(
                icon,
                color: AminaTheme.isDark(context)
                    ? AminaTheme.teal400
                    : AminaVisualLanguage.actionGreen,
                size: dense ? 23 : 27,
              ),
            ),
            SizedBox(width: dense ? 14 : 18),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (eyebrow != null) ...[
                    Text(
                      eyebrow!,
                      style: TextStyle(
                        color: AminaTheme.isDark(context)
                            ? AminaTheme.teal400
                            : AminaVisualLanguage.actionGreen,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: .32,
                      ),
                    ),
                    const SizedBox(height: 5),
                  ],
                  Text(
                    title,
                    style: TextStyle(
                      color: AminaVisualLanguage.primaryText(context),
                      fontSize: dense ? 18 : 20,
                      height: 1.18,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -.3,
                    ),
                  ),
                  const SizedBox(height: 7),
                  Text(
                    body,
                    style: TextStyle(
                      color: AminaVisualLanguage.secondary(context),
                      fontSize: dense ? 12.5 : 13.5,
                      height: 1.46,
                    ),
                  ),
                ],
              ),
            ),
          ],
        );

        final actions = hasActions
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: AminaVisualLanguage.primaryGradient,
                      borderRadius: BorderRadius.circular(
                        AminaVisualLanguage.controlRadius,
                      ),
                      boxShadow: AminaVisualLanguage.controlShadowLight,
                    ),
                    child: FilledButton.icon(
                      onPressed: onPrimaryAction,
                      icon: const Icon(Icons.arrow_forward_rounded, size: 18),
                      label: Text(primaryActionLabel!),
                      style: FilledButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        foregroundColor: Colors.white,
                        shadowColor: Colors.transparent,
                        minimumSize: const Size.fromHeight(48),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(
                            AminaVisualLanguage.controlRadius,
                          ),
                        ),
                      ),
                    ),
                  ),
                  if (secondaryActionLabel != null) ...[
                    const SizedBox(height: 8),
                    SizedBox(
                      height: 48,
                      child: OutlinedButton(
                        onPressed: onSecondaryAction,
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AminaTheme.isDark(context)
                              ? AminaTheme.teal400
                              : AminaVisualLanguage.actionGreen,
                          side: BorderSide(
                            color: AminaTheme.isDark(context)
                                ? AminaTheme.teal400
                                : AminaVisualLanguage.actionGreen,
                            width: 1.15,
                          ),
                          backgroundColor:
                              AminaVisualLanguage.controlSurface(context),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(
                              AminaVisualLanguage.controlRadius,
                            ),
                          ),
                        ),
                        child: Text(secondaryActionLabel!),
                      ),
                    ),
                  ],
                ],
              )
            : null;

        final noteWidget = note == null
            ? null
            : Container(
                width: double.infinity,
                padding: const EdgeInsetsDirectional.fromSTEB(12, 10, 12, 10),
                decoration: BoxDecoration(
                  color: AminaVisualLanguage.mintSurface.withValues(
                    alpha: AminaTheme.isDark(context) ? .08 : .72,
                  ),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: AminaVisualLanguage.mintBorder.withValues(
                      alpha: AminaTheme.isDark(context) ? .3 : .72,
                    ),
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.verified_user_outlined,
                      size: 16,
                      color: AminaTheme.isDark(context)
                          ? AminaTheme.teal400
                          : AminaVisualLanguage.actionGreen,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        note!,
                        style: TextStyle(
                          color: AminaTheme.isDark(context)
                              ? AminaTheme.dark300
                              : AminaVisualLanguage.actionGreen,
                          fontSize: 11.5,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              );

        return Semantics(
          container: true,
          label: '$title. $body',
          child: Container(
            width: double.infinity,
            padding: EdgeInsets.all(padding),
            decoration: AminaVisualLanguage.cardDecoration(
              context,
              radius: AminaVisualLanguage.cardRadius,
            ),
            child: wide
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Expanded(flex: 6, child: intro),
                      const SizedBox(width: 28),
                      SizedBox(width: 260, child: actions),
                      if (noteWidget != null) ...[
                        const SizedBox(width: 18),
                        Expanded(flex: 4, child: noteWidget),
                      ],
                    ],
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      intro,
                      if (actions != null) ...[
                        SizedBox(height: dense ? 16 : 20),
                        actions,
                      ],
                      if (noteWidget != null) ...[
                        SizedBox(height: dense ? 12 : 16),
                        noteWidget,
                      ],
                    ],
                  ),
          ),
        );
      },
    );
  }
}
