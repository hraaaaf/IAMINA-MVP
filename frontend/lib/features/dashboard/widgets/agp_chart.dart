import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Shared AGP (Ambulatory Glucose Profile) chart primitives
//
// Used by:
//  • GlucoseChartWithEvents (dashboard) — local readings, computed percentiles
//  • AISummaryScreen (journal)          — server-side percentile data
//
// Public surface:
//   AgpPoint   — canonical per-hour percentile data class
//   AgpPainter — CustomPainter: renders ADA AGP bands + colored zones
//   AgpYAxis   — Y-axis label column
//   AgpXAxis   — X-axis hour labels
// ─────────────────────────────────────────────────────────────────────────────

// ── Data class ────────────────────────────────────────────────────────────────

/// One hour's worth of percentile data for an AGP chart.
/// [hour] is 0–23.  All glucose values are in mg/dL.
class AgpPoint {
  final double hour;
  final double p5, p25, p50, p75, p95;

  const AgpPoint({
    required this.hour,
    required this.p5,
    required this.p25,
    required this.p50,
    required this.p75,
    required this.p95,
  });
}

// ── CustomPainter ─────────────────────────────────────────────────────────────

/// Renders ADA-standard AGP percentile bands with coloured glycaemic zones.
///
/// Bands drawn:
///   5–95%   (outer, low opacity)
///   25–75%  (inner, higher opacity)
///   p50     (median line, 2.5 stroke)
///
/// Zone fills:
///   > [high]          orange tint
///   [low]–[high]      green tint  (target)
///   < [low]           red tint
class AgpPainter extends CustomPainter {
  final List<AgpPoint> points;
  final double minY, maxY;
  final double low, high;
  final bool isDark;

  /// Horizontal grid lines (mg/dL values).  Default: ADA clinical targets.
  final List<double> gridLines;

  const AgpPainter({
    required this.points,
    required this.minY,
    required this.maxY,
    required this.low,
    required this.high,
    required this.isDark,
    this.gridLines = const [70.0, 110.0, 180.0, 250.0],
  });

  // ── coordinate helpers ────────────────────────────────────────────────────

  double _toY(double val, double h) =>
      h - ((val - minY) / (maxY - minY)) * h;

  double _toX(double hour, double w) => (hour / 23.0) * w;

  // ── path builders ─────────────────────────────────────────────────────────

  /// Closed filled band between [topFn] and [botFn] curves.
  Path _band(
    List<AgpPoint> pts,
    double Function(AgpPoint) topFn,
    double Function(AgpPoint) botFn,
    double w,
    double h,
  ) {
    final path = Path();
    for (var i = 0; i < pts.length; i++) {
      final x = _toX(pts[i].hour, w);
      final y = _toY(topFn(pts[i]), h);
      i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
    }
    for (var i = pts.length - 1; i >= 0; i--) {
      path.lineTo(_toX(pts[i].hour, w), _toY(botFn(pts[i]), h));
    }
    path.close();
    return path;
  }

  /// Smooth (cubic Bézier) open curve for a single percentile.
  Path _curve(List<AgpPoint> pts, double Function(AgpPoint) valFn,
      double w, double h) {
    final path = Path();
    for (var i = 0; i < pts.length; i++) {
      final x = _toX(pts[i].hour, w);
      final y = _toY(valFn(pts[i]), h);
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        final px = _toX(pts[i - 1].hour, w);
        final py = _toY(valFn(pts[i - 1]), h);
        final cx = (px + x) / 2;
        path.cubicTo(cx, py, cx, y, x, y);
      }
    }
    return path;
  }

  void _dashedH(Canvas canvas, double w, double y, Color color) {
    final paint = Paint()
      ..color = color.withValues(alpha: 0.75)
      ..strokeWidth = 1.5;
    const dash = 5.0, gap = 4.0;
    for (var x = 0.0; x < w; x += dash + gap) {
      canvas.drawLine(
        Offset(x, y), Offset(math.min(x + dash, w), y), paint);
    }
  }

  // ── paint ─────────────────────────────────────────────────────────────────

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final yHigh = _toY(high, h);
    final yLow  = _toY(low,  h);

    // 1. Zone backgrounds
    canvas.drawRect(
      Rect.fromLTRB(0, _toY(maxY, h), w, yHigh),
      Paint()..color = const Color(0xFFFB923C).withValues(alpha: isDark ? 0.12 : 0.08),
    );
    canvas.drawRect(
      Rect.fromLTRB(0, yHigh, w, yLow),
      Paint()..color = AminaTheme.teal500.withValues(alpha: isDark ? 0.10 : 0.07),
    );
    canvas.drawRect(
      Rect.fromLTRB(0, yLow, w, _toY(minY, h)),
      Paint()..color = AminaTheme.dangerRed.withValues(alpha: isDark ? 0.15 : 0.08),
    );

    // 2. Horizontal grid
    final gridPaint = Paint()
      ..color = (isDark ? Colors.white : Colors.black).withValues(alpha: 0.07)
      ..strokeWidth = 1;
    for (final v in gridLines) {
      if (v < minY || v > maxY) continue;
      canvas.drawLine(Offset(0, _toY(v, h)), Offset(w, _toY(v, h)), gridPaint);
    }

    // 3. Target dashed boundary lines
    _dashedH(canvas, w, yHigh, const Color(0xFFE4A85B));
    _dashedH(canvas, w, yLow,  const Color(0xFFE4A85B));

    if (points.isEmpty) return;

    // 4. 5–95% band (outer, low opacity)
    canvas.drawPath(
      _band(points, (p) => p.p95, (p) => p.p5, w, h),
      Paint()..color = AminaTheme.teal500.withValues(alpha: isDark ? 0.18 : 0.13),
    );

    // 5. 25–75% band (inner, higher opacity)
    canvas.drawPath(
      _band(points, (p) => p.p75, (p) => p.p25, w, h),
      Paint()..color = AminaTheme.teal500.withValues(alpha: isDark ? 0.35 : 0.28),
    );

    // 6. Band borders
    final border = Paint()
      ..color = AminaTheme.teal400.withValues(alpha: 0.45)
      ..strokeWidth = 1
      ..style = PaintingStyle.stroke;
    canvas.drawPath(_curve(points, (p) => p.p95, w, h), border);
    canvas.drawPath(_curve(points, (p) => p.p5,  w, h), border);

    // 7. Median line (p50)
    canvas.drawPath(
      _curve(points, (p) => p.p50, w, h),
      Paint()
        ..color = isDark ? Colors.white : AminaTheme.teal700
        ..strokeWidth = 2.5
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(AgpPainter old) =>
      old.points != points || old.isDark != isDark ||
      old.minY != minY || old.maxY != maxY;
}

// ── Y-Axis ────────────────────────────────────────────────────────────────────

/// Vertical labels for an AGP chart.
///
/// [labels] defaults to ADA clinical targets: 70, 110, 180, 250.
/// Only labels within [minY]–[maxY] are shown.
class AgpYAxis extends StatelessWidget {
  final double minY, maxY;
  final bool isDark;
  final List<int> labels;

  const AgpYAxis({
    super.key,
    required this.minY,
    required this.maxY,
    required this.isDark,
    this.labels = const [70, 110, 180, 250],
  });

  @override
  Widget build(BuildContext context) {
    final visible = labels.where((v) => v >= minY && v <= maxY).toList();
    return LayoutBuilder(builder: (_, c) {
      return Stack(
        children: visible.map((v) {
          final frac = 1 - ((v - minY) / (maxY - minY));
          return Positioned(
            top: frac * (c.maxHeight - 16),
            right: 2,
            child: Text(
              '$v',
              style: TextStyle(
                fontSize: 8,
                color: isDark ? AminaTheme.ink300 : AminaTheme.ink400,
              ),
            ),
          );
        }).toList(),
      );
    });
  }
}

// ── X-Axis ────────────────────────────────────────────────────────────────────

/// Horizontal hour labels (0h–23h) for an AGP chart.
class AgpXAxis extends StatelessWidget {
  final bool isDark;

  const AgpXAxis({super.key, required this.isDark});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (_, c) {
      return Stack(
        children: [0, 6, 12, 18, 23].map((h) {
          final x = (h / 23.0) * c.maxWidth;
          return Positioned(
            left: x - 8,
            top: 2,
            child: Text(
              '${h}h',
              style: TextStyle(
                fontSize: 8,
                color: isDark ? AminaTheme.ink300 : AminaTheme.ink400,
              ),
            ),
          );
        }).toList(),
      );
    });
  }
}
