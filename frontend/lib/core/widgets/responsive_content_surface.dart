import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Centers a route body on wide canvases while preserving the full available
/// width on tablet and mobile. The child still receives a finite, truthful
/// viewport and is never artificially scaled.
class ResponsiveContentSurface extends StatelessWidget {
  final Widget child;
  final double maxWidth;

  const ResponsiveContentSurface({
    super.key,
    required this.child,
    required this.maxWidth,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = math.min(constraints.maxWidth, maxWidth);
        return Align(
          alignment: AlignmentDirectional.topCenter,
          child: SizedBox(
            width: width,
            height: constraints.maxHeight,
            child: child,
          ),
        );
      },
    );
  }
}
