import 'package:flutter/material.dart';

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
        final padding = dense ? 18.0 : 22.0;

        final intro = Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: dense ? 44 : 50,
              height: dense ? 44 : 50,
              decoration: BoxDecoration(
                color: const Color(0xFFE5F5EF),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                icon,
                color: const Color(0xFF064E52),
                size: dense ? 22 : 25,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (eyebrow != null) ...[
                    Text(
                      eyebrow!,
                      style: const TextStyle(
                        color: Color(0xFF0A766B),
                        fontSize: 10.5,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.35,
                      ),
                    ),
                    const SizedBox(height: 4),
                  ],
                  Text(
                    title,
                    style: TextStyle(
                      color: AminaTheme.textPrimary(context),
                      fontSize: dense ? 18 : 20,
                      height: 1.15,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.35,
                    ),
                  ),
                  const SizedBox(height: 7),
                  Text(
                    body,
                    style: TextStyle(
                      color: AminaTheme.textSecondary(context),
                      fontSize: dense ? 12.5 : 13.5,
                      height: 1.45,
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
                  FilledButton.icon(
                    onPressed: onPrimaryAction,
                    icon: const Icon(Icons.arrow_forward_rounded, size: 18),
                    label: Text(primaryActionLabel!),
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF064E52),
                      foregroundColor: Colors.white,
                      minimumSize: const Size.fromHeight(48),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                  ),
                  if (secondaryActionLabel != null) ...[
                    const SizedBox(height: 8),
                    OutlinedButton(
                      onPressed: onSecondaryAction,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF064E52),
                        minimumSize: const Size.fromHeight(48),
                        side: BorderSide(color: AminaTheme.divider(context)),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      child: Text(secondaryActionLabel!),
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
                  color: const Color(0xFFF0F7F4),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.verified_user_outlined,
                      size: 16,
                      color: Color(0xFF064E52),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        note!,
                        style: const TextStyle(
                          color: Color(0xFF355E59),
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
            padding: EdgeInsetsDirectional.fromSTEB(
              padding,
              padding,
              padding,
              padding,
            ),
            decoration: BoxDecoration(
              color: AminaTheme.surface(context),
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: AminaTheme.divider(context)),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF064E52).withValues(alpha: 0.06),
                  blurRadius: 22,
                  offset: const Offset(0, 10),
                ),
              ],
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
