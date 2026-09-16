import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch16Ids = <String>{
  'medfouna_rissani',
  'tafernout_bread',
  'berkoukes',
};

bool hasCodeFoodPictogramBatch16(String foodId) =>
    codeFoodPictogramBatch16Ids.contains(foodId);

class FoodPictogramPainterBatch16 extends CustomPainter {
  final String foodId;
  const FoodPictogramPainterBatch16(this.foodId);

  Paint _fill(Color color) => Paint()..color = color..isAntiAlias = true;
  Paint _stroke(Color color, double width) => Paint()
    ..color = color
    ..style = PaintingStyle.stroke
    ..strokeWidth = width
    ..strokeCap = StrokeCap.round
    ..strokeJoin = StrokeJoin.round
    ..isAntiAlias = true;

  void _shadow(Canvas canvas) => canvas.drawShadow(
        Path()..addOval(const Rect.fromLTWH(20, 76, 60, 7)),
        Colors.black.withValues(alpha: .14),
        4,
        false,
      );

  @override
  void paint(Canvas canvas, Size size) {
    final side = math.min(size.width, size.height);
    canvas.save();
    canvas.translate((size.width - side) / 2, (size.height - side) / 2);
    canvas.scale(side / 100, side / 100);
    switch (foodId) {
      case 'medfouna_rissani':
        _medfouna(canvas);
        break;
      case 'tafernout_bread':
        _tafernout(canvas);
        break;
      case 'berkoukes':
        _berkoukes(canvas);
        break;
    }
    canvas.restore();
  }

  void _medfouna(Canvas canvas) {
    _shadow(canvas);
    canvas.drawOval(const Rect.fromLTWH(20, 45, 60, 30), _fill(const Color(0xFFF3F6F4)));
    canvas.drawOval(const Rect.fromLTWH(25, 35, 50, 32), _fill(const Color(0xFFD7A55D)));
    canvas.drawArc(const Rect.fromLTWH(25, 35, 50, 32), .1, math.pi - .2, false, _stroke(const Color(0xFF9D683A), 2));
    canvas.drawPath(
      Path()..moveTo(50, 36)..lineTo(50, 66)..moveTo(50, 50)..lineTo(72, 55),
      _stroke(const Color(0xFFF0D49B), 2),
    );
    for (final p in const [Offset(56, 49), Offset(62, 54), Offset(57, 58)]) {
      canvas.drawCircle(p, 2.5, _fill(const Color(0xFF7B4B36)));
    }
  }

  void _tafernout(Canvas canvas) {
    _shadow(canvas);
    final bread = Path()
      ..moveTo(22, 58)
      ..quadraticBezierTo(27, 33, 51, 31)
      ..quadraticBezierTo(76, 34, 79, 58)
      ..quadraticBezierTo(54, 72, 22, 58)
      ..close();
    canvas.drawPath(bread, _fill(const Color(0xFFC9924F)));
    for (final p in const [Offset(34, 48), Offset(46, 42), Offset(59, 48), Offset(68, 43), Offset(50, 57)]) {
      canvas.drawCircle(p, 3.2, _fill(const Color(0xFF8A633F)));
      canvas.drawCircle(p, 1.5, _fill(const Color(0xFFE8C27F)));
    }
  }

  void _berkoukes(Canvas canvas) {
    _shadow(canvas);
    canvas.drawOval(const Rect.fromLTWH(18, 44, 64, 35), _fill(const Color(0xFFE5ECEA)));
    canvas.drawOval(const Rect.fromLTWH(24, 37, 52, 28), _fill(const Color(0xFFB65F42)));
    for (final p in const [
      Offset(34, 48), Offset(43, 44), Offset(52, 50), Offset(61, 44), Offset(67, 53), Offset(42, 56), Offset(57, 57)
    ]) {
      canvas.drawCircle(p, 3.3, _fill(const Color(0xFFE0C17D)));
    }
    canvas.drawCircle(const Offset(36, 54), 2.4, _fill(const Color(0xFF7FA05D)));
    canvas.drawCircle(const Offset(63, 49), 2.4, _fill(const Color(0xFF7FA05D)));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch16 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
