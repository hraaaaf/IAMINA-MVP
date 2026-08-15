import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import 'mobile_page_header.dart';

/// Presentation-only bridge for task screens whose internal header cannot be
/// removed without touching sensitive workflow logic.
///
/// The child is laid out slightly taller, translated upward by the exact legacy
/// chrome extent and clipped. This preserves the complete task body and bottom
/// actions while replacing only the old top chrome with IAmina's canonical
/// patient-facing header.
class AminaLegacyPageHeaderBridge extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget child;
  final double legacyTopExtent;

  const AminaLegacyPageHeaderBridge({
    super.key,
    required this.title,
    this.subtitle,
    required this.child,
    required this.legacyTopExtent,
  });

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: AminaTheme.bg(context),
      child: Column(
        children: [
          AminaMobilePageHeader(title: title, subtitle: subtitle),
          Expanded(
            child: LayoutBuilder(
              builder: (context, constraints) {
                final bridgedHeight = constraints.maxHeight + legacyTopExtent;
                return ClipRect(
                  child: OverflowBox(
                    alignment: Alignment.topCenter,
                    minHeight: bridgedHeight,
                    maxHeight: bridgedHeight,
                    child: Transform.translate(
                      offset: Offset(0, -legacyTopExtent),
                      child: SizedBox(
                        height: bridgedHeight,
                        width: constraints.maxWidth,
                        child: child,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
