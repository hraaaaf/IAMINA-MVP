import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/amina_visual_language.dart';
import '../../../data/drift/database.dart';

class DashboardTrendPainter extends CustomPainter {
  final List<LogEntryData> logs;
  final List<MedicationEventData> medications;
  final DateTime start;
  final DateTime end;
  final double? low;
  final double? high;
  final int selectedLogId;
  final String unit;
  final String locale;
  final bool isDark;
  final bool dailySummary;

  const DashboardTrendPainter({
    required this.logs,
    required this.medications,
    required this.start,
    required this.end,
    required this.low,
    required this.high,
    required this.selectedLogId,
    required this.unit,
    required this.locale,
    required this.isDark,
    required this.dailySummary,
  });

  static const double leftInset = 46;
  static const double rightInset = 10;

  DateTime _recordedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  String _valueLabel(double mgDl) => unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

  @override
  void paint(Canvas canvas, Size size) {
    const top = 12.0;
    const bottom = 30.0;
    final rect = Rect.fromLTRB(
      leftInset,
      top,
      size.width - rightInset,
      size.height - bottom,
    );
    if (rect.width <= 0 || rect.height <= 0 || logs.isEmpty) return;

    final bounds = _valueBounds();
    final minY = bounds.$1;
    final maxY = bounds.$2;

    double yFor(double value) =>
        rect.bottom - ((value - minY) / (maxY - minY)) * rect.height;

    double xFor(DateTime time) {
      final total = end.millisecondsSinceEpoch - start.millisecondsSinceEpoch;
      if (total <= 0) return rect.left;
      final elapsed = time.millisecondsSinceEpoch - start.millisecondsSinceEpoch;
      final fraction = (elapsed / total).clamp(0.0, 1.0).toDouble();
      return rect.left + fraction * rect.width;
    }

    _paintTargetBand(canvas, rect, yFor);
    _paintGridAndAxes(canvas, rect, minY, maxY);
    _paintMedicationEvents(canvas, rect, xFor);

    if (dailySummary) {
      _paintDailySummary(canvas, rect, yFor);
    } else {
      _paintRecordedPoints(canvas, xFor, yFor);
    }
  }

  (double, double) _valueBounds() {
    final values = <double>[
      ...logs.map((log) => log.bloodSugar),
      if (low != null) low!,
      if (high != null) high!,
    ];
    final observedMax = values.reduce(math.max);
    final maxY = math.max(300.0, (observedMax / 50).ceil() * 50.0).toDouble();
    return (0.0, maxY);
  }

  void _paintTargetBand(
    Canvas canvas,
    Rect rect,
    double Function(double) yFor,
  ) {
    if (low == null || high == null || low! >= high!) return;
    final top = yFor(high!).clamp(rect.top, rect.bottom).toDouble();
    final bottom = yFor(low!).clamp(rect.top, rect.bottom).toDouble();
    final bandRect = Rect.fromLTRB(rect.left, top, rect.right, bottom);
    canvas.drawRect(
      bandRect,
      Paint()..color = AminaVisualLanguage.mintSurface.withValues(alpha: .55),
    );
    final edgePaint = Paint()
      ..color = AminaVisualLanguage.mintBorder.withValues(alpha: .78)
      ..strokeWidth = 1;
    _drawDashedLine(
      canvas,
      Offset(rect.left, top),
      Offset(rect.right, top),
      edgePaint,
    );
    _drawDashedLine(
      canvas,
      Offset(rect.left, bottom),
      Offset(rect.right, bottom),
      edgePaint,
    );
  }

  void _paintGridAndAxes(
    Canvas canvas,
    Rect rect,
    double minY,
    double maxY,
  ) {
    final gridPaint = Paint()
      ..color = (isDark ? Colors.white : const Color(0xFF123E35))
          .withValues(alpha: .08)
      ..strokeWidth = 1;
    final axisStyle = TextStyle(
      fontSize: 9.5,
      color: (isDark ? Colors.white : const Color(0xFF42655D))
          .withValues(alpha: .78),
    );

    final ticks = _axisTicks(minY, maxY);
    for (final value in ticks) {
      final fraction = (value - minY) / (maxY - minY);
      final y = rect.bottom - fraction * rect.height;
      canvas.drawLine(Offset(rect.left, y), Offset(rect.right, y), gridPaint);
      final painter = TextPainter(
        text: TextSpan(text: _valueLabel(value), style: axisStyle),
        textDirection: ui.TextDirection.ltr,
      )..layout(maxWidth: leftInset - 6);
      painter.paint(
        canvas,
        Offset(leftInset - painter.width - 7, y - painter.height / 2),
      );
    }

    if (dailySummary) {
      final summaries = _dailySummaries();
      for (var i = 0; i < summaries.length; i++) {
        final summary = summaries[i];
        final x = _xForSummaryIndex(i, summaries.length, rect);
        final guide = Paint()
          ..color = (isDark ? Colors.white : const Color(0xFF123E35))
              .withValues(alpha: .045)
          ..strokeWidth = 1;
        canvas.drawLine(Offset(x, rect.top), Offset(x, rect.bottom), guide);
        _paintXAxisLabel(
          canvas,
          DateFormat('d MMM', locale).format(summary.day),
          x,
          rect,
          axisStyle,
        );
      }
      return;
    }

    final range = end.difference(start);
    final times = [
      start,
      start.add(Duration(milliseconds: range.inMilliseconds ~/ 2)),
      end,
    ];
    for (var i = 0; i < times.length; i++) {
      final label = DateFormat('HH:mm', locale).format(times[i]);
      final x = rect.left + rect.width * (i / 2);
      _paintXAxisLabel(canvas, label, x, rect, axisStyle, edgeIndex: i);
    }
  }

  List<double> _axisTicks(double minY, double maxY) {
    if (minY == 0 && maxY == 300) return const [0, 70, 132, 210, 300];
    final step = (maxY - minY) / 4;
    return [minY, minY + step, minY + step * 2, minY + step * 3, maxY];
  }

  void _paintXAxisLabel(
    Canvas canvas,
    String label,
    double x,
    Rect rect,
    TextStyle style, {
    int? edgeIndex,
  }) {
    final painter = TextPainter(
      text: TextSpan(text: label, style: style),
      textDirection: ui.TextDirection.ltr,
    )..layout();
    var dx = x - painter.width / 2;
    if (edgeIndex == 0) dx = rect.left;
    if (edgeIndex == 2) dx = rect.right - painter.width;
    dx = dx.clamp(rect.left, rect.right - painter.width).toDouble();
    painter.paint(canvas, Offset(dx, rect.bottom + 8));
  }

  void _paintMedicationEvents(
    Canvas canvas,
    Rect rect,
    double Function(DateTime) xFor,
  ) {
    if (medications.isEmpty) return;
    final paint = Paint()
      ..color = const Color(0xFFC9852B).withValues(alpha: .8)
      ..strokeWidth = 1.5;
    for (final event in medications) {
      final x = dailySummary
          ? _xForDay(
              DateTime(event.takenAt.year, event.takenAt.month, event.takenAt.day),
              rect,
            )
          : xFor(event.takenAt);
      canvas.drawLine(Offset(x, rect.top), Offset(x, rect.top + 8), paint);
      canvas.drawCircle(Offset(x, rect.top + 1), 2.2, paint);
    }
  }

  void _paintDailySummary(
    Canvas canvas,
    Rect rect,
    double Function(double) yFor,
  ) {
    final summaries = _dailySummaries();
    if (summaries.isEmpty) return;

    final whiskerPaint = Paint()
      ..color = AminaVisualLanguage.forestDeep.withValues(alpha: .46)
      ..strokeWidth = 1.7
      ..strokeCap = StrokeCap.round;
    final linePaint = Paint()
      ..color = AminaVisualLanguage.forestDeep
      ..strokeWidth = 2.1
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final pointPaint = Paint()..color = AminaVisualLanguage.forestDeep;
    final selectedPaint = Paint()..color = AminaVisualLanguage.actionGreen;

    final points = <Offset>[];
    for (var i = 0; i < summaries.length; i++) {
      final summary = summaries[i];
      final x = _xForSummaryIndex(i, summaries.length, rect);
      final yMin = yFor(summary.min);
      final yMax = yFor(summary.max);
      canvas.drawLine(Offset(x, yMax), Offset(x, yMin), whiskerPaint);
      points.add(Offset(x, yFor(summary.median)));
    }

    if (points.length > 1) {
      final path = Path()..moveTo(points.first.dx, points.first.dy);
      for (var i = 0; i < points.length - 1; i++) {
        final current = points[i];
        final next = points[i + 1];
        final midX = (current.dx + next.dx) / 2;
        path.cubicTo(midX, current.dy, midX, next.dy, next.dx, next.dy);
      }
      canvas.drawPath(path, linePaint);
    }

    for (var i = 0; i < summaries.length; i++) {
      final summary = summaries[i];
      final point = points[i];
      final selected = summary.logIds.contains(selectedLogId);
      final latest = i == summaries.length - 1;

      if (selected || latest) {
        canvas.drawCircle(
          point,
          selected ? 8.0 : 7.0,
          Paint()..color = AminaVisualLanguage.mintSurface,
        );
      }
      canvas.drawCircle(
        point,
        selected ? 5.2 : latest ? 4.8 : 4.2,
        selected || latest ? selectedPaint : pointPaint,
      );
      if (latest) {
        canvas.drawCircle(
          point,
          9.5,
          Paint()
            ..color = AminaVisualLanguage.actionGreen
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1.5,
        );
      }
    }
  }

  double _xForSummaryIndex(int index, int count, Rect rect) {
    if (count <= 1) return rect.center.dx;
    final sidePadding = math.min(24.0, rect.width * .04);
    final usable = rect.width - sidePadding * 2;
    return rect.left + sidePadding + usable * (index / (count - 1));
  }

  double _xForDay(DateTime day, Rect rect) {
    final summaries = _dailySummaries();
    if (summaries.isEmpty) return rect.center.dx;
    var index = summaries.indexWhere((summary) => summary.day == day);
    if (index < 0) {
      index = 0;
      var bestDistance = (summaries.first.day.difference(day)).abs();
      for (var i = 1; i < summaries.length; i++) {
        final distance = summaries[i].day.difference(day).abs();
        if (distance < bestDistance) {
          bestDistance = distance;
          index = i;
        }
      }
    }
    return _xForSummaryIndex(index, summaries.length, rect);
  }

  List<_DailySummary> _dailySummaries() {
    final byDay = <DateTime, List<LogEntryData>>{};
    for (final log in logs) {
      final at = _recordedAt(log);
      final day = DateTime(at.year, at.month, at.day);
      byDay.putIfAbsent(day, () => <LogEntryData>[]).add(log);
    }
    final days = byDay.keys.toList()..sort();
    return days.map((day) {
      final dayLogs = byDay[day]!
        ..sort((a, b) => a.bloodSugar.compareTo(b.bloodSugar));
      final values = dayLogs.map((log) => log.bloodSugar).toList(growable: false);
      final median = values.length.isOdd
          ? values[values.length ~/ 2]
          : (values[values.length ~/ 2 - 1] + values[values.length ~/ 2]) / 2;
      return _DailySummary(
        day: day,
        median: median,
        min: values.first,
        max: values.last,
        logIds: dayLogs.map((log) => log.id).toSet(),
      );
    }).toList(growable: false);
  }

  void _paintRecordedPoints(
    Canvas canvas,
    double Function(DateTime) xFor,
    double Function(double) yFor,
  ) {
    final pointPaint = Paint()
      ..color = AminaVisualLanguage.forestDeep.withValues(alpha: .78);
    final selectedPaint = Paint()..color = AminaVisualLanguage.actionGreen;
    final latestId = logs
        .reduce((a, b) => _recordedAt(a).isAfter(_recordedAt(b)) ? a : b)
        .id;

    for (final log in logs) {
      final point = Offset(xFor(_recordedAt(log)), yFor(log.bloodSugar));
      final selected = log.id == selectedLogId;
      final latest = log.id == latestId;
      if (selected || latest) {
        canvas.drawCircle(
          point,
          selected ? 7 : 6.2,
          Paint()..color = AminaVisualLanguage.mintSurface,
        );
      }
      canvas.drawCircle(
        point,
        selected ? 4.8 : latest ? 4.4 : 3.0,
        selected || latest ? selectedPaint : pointPaint,
      );
    }
  }

  void _drawDashedLine(
    Canvas canvas,
    Offset startOffset,
    Offset endOffset,
    Paint paint,
  ) {
    const dash = 5.0;
    const gap = 4.0;
    var x = startOffset.dx;
    while (x < endOffset.dx) {
      final endX = math.min(x + dash, endOffset.dx);
      canvas.drawLine(
        Offset(x, startOffset.dy),
        Offset(endX, endOffset.dy),
        paint,
      );
      x += dash + gap;
    }
  }

  @override
  bool shouldRepaint(covariant DashboardTrendPainter oldDelegate) {
    return oldDelegate.logs != logs ||
        oldDelegate.medications != medications ||
        oldDelegate.start != start ||
        oldDelegate.end != end ||
        oldDelegate.low != low ||
        oldDelegate.high != high ||
        oldDelegate.selectedLogId != selectedLogId ||
        oldDelegate.unit != unit ||
        oldDelegate.locale != locale ||
        oldDelegate.isDark != isDark ||
        oldDelegate.dailySummary != dailySummary;
  }
}

class _DailySummary {
  final DateTime day;
  final double median;
  final double min;
  final double max;
  final Set<int> logIds;

  const _DailySummary({
    required this.day,
    required this.median,
    required this.min,
    required this.max,
    required this.logIds,
  });
}
