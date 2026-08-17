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
  });

  static const double leftInset = 42;
  static const double rightInset = 8;

  DateTime _recordedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  String _valueLabel(double mgDl) => unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

  @override
  void paint(Canvas canvas, Size size) {
    const top = 10.0;
    const bottom = 28.0;
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
    _paintRecordedTrajectory(canvas, xFor, yFor);
    _paintRecordedPoints(canvas, xFor, yFor);
  }

  (double, double) _valueBounds() {
    final values = <double>[
      ...logs.map((log) => log.bloodSugar),
      if (low != null) low!,
      if (high != null) high!,
    ];
    var minY = values.reduce(math.min);
    var maxY = values.reduce(math.max);
    final rawSpan = maxY - minY;
    final padding = math.max(15.0, rawSpan * .12).toDouble();
    minY = math.max(0.0, minY - padding).toDouble();
    maxY += padding;
    if (maxY - minY < 20) {
      final center = (maxY + minY) / 2;
      minY = math.max(0.0, center - 10).toDouble();
      maxY = center + 10;
    }
    return (minY, maxY);
  }

  void _paintTargetBand(
    Canvas canvas,
    Rect rect,
    double Function(double) yFor,
  ) {
    if (low == null || high == null || low! >= high!) return;
    final top = yFor(high!).clamp(rect.top, rect.bottom).toDouble();
    final bottom = yFor(low!).clamp(rect.top, rect.bottom).toDouble();
    canvas.drawRect(
      Rect.fromLTRB(rect.left, top, rect.right, bottom),
      Paint()..color = AminaVisualLanguage.mintSurface.withValues(alpha: .48),
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
          .withValues(alpha: .09)
      ..strokeWidth = 1;
    final axisStyle = TextStyle(
      fontSize: 9.5,
      color: (isDark ? Colors.white : const Color(0xFF42655D))
          .withValues(alpha: .78),
    );

    for (final fraction in const [0.0, .5, 1.0]) {
      final y = rect.top + rect.height * fraction;
      canvas.drawLine(Offset(rect.left, y), Offset(rect.right, y), gridPaint);
      final value = maxY - (maxY - minY) * fraction;
      final painter = TextPainter(
        text: TextSpan(text: _valueLabel(value), style: axisStyle),
        textDirection: ui.TextDirection.ltr,
      )..layout(maxWidth: leftInset - 6);
      painter.paint(
        canvas,
        Offset(leftInset - painter.width - 6, y - painter.height / 2),
      );
    }

    final range = end.difference(start);
    final times = [
      start,
      start.add(Duration(milliseconds: range.inMilliseconds ~/ 2)),
      end,
    ];
    for (var i = 0; i < times.length; i++) {
      final label = range.inHours <= 24
          ? DateFormat('HH:mm', locale).format(times[i])
          : DateFormat('d MMM', locale).format(times[i]);
      final painter = TextPainter(
        text: TextSpan(text: label, style: axisStyle),
        textDirection: ui.TextDirection.ltr,
      )..layout();
      final x = rect.left + rect.width * (i / 2);
      final dx = i == 0
          ? x
          : i == 2
              ? x - painter.width
              : x - painter.width / 2;
      painter.paint(canvas, Offset(dx, rect.bottom + 7));
    }
  }

  void _paintMedicationEvents(
    Canvas canvas,
    Rect rect,
    double Function(DateTime) xFor,
  ) {
    final paint = Paint()
      ..color = const Color(0xFFC9852B)
      ..strokeWidth = 1.5;
    for (final event in medications) {
      final x = xFor(event.takenAt);
      canvas.drawLine(Offset(x, rect.top), Offset(x, rect.top + 10), paint);
      canvas.drawCircle(Offset(x, rect.top + 2), 2.5, paint);
    }
  }

  void _paintRecordedTrajectory(
    Canvas canvas,
    double Function(DateTime) xFor,
    double Function(double) yFor,
  ) {
    if (logs.length < 2) return;

    final ordered = List<LogEntryData>.from(logs)
      ..sort((a, b) => _recordedAt(a).compareTo(_recordedAt(b)));
    final windowMs = end.millisecondsSinceEpoch - start.millisecondsSinceEpoch;
    if (windowMs <= 0) return;

    // A large temporal hole is shown as a break rather than as invented
    // continuity. This threshold is visual only: one sixth of the selected
    // window, never a clinical inference or glucose rule.
    final maxConnectedGapMs = windowMs ~/ 6;
    final linePaint = Paint()
      ..color = AminaVisualLanguage.actionGreen.withValues(alpha: .72)
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    for (var i = 1; i < ordered.length; i++) {
      final previous = ordered[i - 1];
      final current = ordered[i];
      final previousAt = _recordedAt(previous);
      final currentAt = _recordedAt(current);
      final gapMs = currentAt.millisecondsSinceEpoch - previousAt.millisecondsSinceEpoch;
      if (gapMs <= 0 || gapMs > maxConnectedGapMs) continue;

      canvas.drawLine(
        Offset(xFor(previousAt), yFor(previous.bloodSugar)),
        Offset(xFor(currentAt), yFor(current.bloodSugar)),
        linePaint,
      );
    }
  }

  void _paintRecordedPoints(
    Canvas canvas,
    double Function(DateTime) xFor,
    double Function(double) yFor,
  ) {
    final pointPaint = Paint()
      ..color = AminaVisualLanguage.forestDeep.withValues(alpha: .82);
    final selectedPaint = Paint()..color = AminaVisualLanguage.actionGreen;
    final latestId = logs.reduce((a, b) =>
            _recordedAt(a).isAfter(_recordedAt(b)) ? a : b)
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
        selected ? 4.8 : latest ? 4.4 : 3.2,
        selected || latest ? selectedPaint : pointPaint,
      );
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
        oldDelegate.isDark != isDark;
  }
}
