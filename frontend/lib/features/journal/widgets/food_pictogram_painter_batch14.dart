import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch14Ids = <String>{
  'sandwich',
  'tacos_wrap',
  'chicken_caesar_salad',
  'tuna_salad',
  'greek_salad',
  'chorba',
  'lentil_soup',
  'vegetable_soup',
  'chicken_soup',
  'tomato_soup',
};

bool hasCodeFoodPictogramBatch14(String foodId) =>
    codeFoodPictogramBatch14Ids.contains(foodId);

class FoodPictogramPainterBatch14 extends CustomPainter {
  final String foodId;
  const FoodPictogramPainterBatch14(this.foodId);

  Paint _fill(Color c) => Paint()..color = c..isAntiAlias = true;
  Paint _stroke(Color c, double w) => Paint()
    ..color = c
    ..style = PaintingStyle.stroke
    ..strokeWidth = w
    ..strokeCap = StrokeCap.round
    ..strokeJoin = StrokeJoin.round
    ..isAntiAlias = true;

  void _shadow(Canvas c) => c.drawShadow(
    Path()..addOval(const Rect.fromLTWH(20, 76, 60, 7)),
    Colors.black.withValues(alpha: .14), 4, false,
  );

  void _plate(Canvas c) {
    _shadow(c);
    c.drawOval(const Rect.fromLTWH(19, 47, 62, 31), _fill(const Color(0xFFF8FBFA)));
  }

  @override
  void paint(Canvas canvas, Size size) {
    final side = math.min(size.width, size.height);
    canvas.save();
    canvas.translate((size.width - side) / 2, (size.height - side) / 2);
    canvas.scale(side / 100, side / 100);
    switch (foodId) {
      case 'sandwich': _sandwich(canvas); break;
      case 'tacos_wrap': _wrap(canvas); break;
      case 'chicken_caesar_salad': _salad(canvas, const Color(0xFF7DA766), chicken: true); break;
      case 'tuna_salad': _salad(canvas, const Color(0xFF78A4A3), fish: true); break;
      case 'greek_salad': _salad(canvas, const Color(0xFF79A866), feta: true); break;
      case 'chorba': _soup(canvas, const Color(0xFFB85D3E), herb: true); break;
      case 'lentil_soup': _soup(canvas, const Color(0xFFB58A45)); break;
      case 'vegetable_soup': _soup(canvas, const Color(0xFFAA7B49), vegetables: true); break;
      case 'chicken_soup': _soup(canvas, const Color(0xFFD1A95C), chicken: true); break;
      case 'tomato_soup': _soup(canvas, const Color(0xFFC64E40)); break;
      default: break;
    }
    canvas.restore();
  }

  void _sandwich(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(29, 38, 43, 14), const Radius.circular(7)), _fill(const Color(0xFFD9A35F)));
    c.drawRect(const Rect.fromLTWH(32, 51, 37, 6), _fill(const Color(0xFF6FA161)));
    c.drawRect(const Rect.fromLTWH(34, 57, 33, 5), _fill(const Color(0xFFD7C45C)));
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(29, 62, 43, 12), const Radius.circular(6)), _fill(const Color(0xFFC89054)));
  }

  void _wrap(Canvas c) {
    _plate(c);
    final shell = Path()
      ..moveTo(34, 36)
      ..quadraticBezierTo(50, 31, 67, 38)
      ..lineTo(60, 72)
      ..lineTo(42, 72)
      ..close();
    c.drawPath(shell, _fill(const Color(0xFFE3C98B)));
    c.drawCircle(const Offset(44, 44), 4, _fill(const Color(0xFF77A365)));
    c.drawCircle(const Offset(53, 42), 4, _fill(const Color(0xFFC64F43)));
    c.drawCircle(const Offset(61, 46), 4, _fill(const Color(0xFFD9B558)));
  }

  void _salad(Canvas c, Color base, {bool chicken = false, bool fish = false, bool feta = false}) {
    _shadow(c);
    c.drawOval(const Rect.fromLTWH(20, 45, 60, 34), _fill(const Color(0xFFE4ECE9)));
    c.drawOval(const Rect.fromLTWH(25, 38, 50, 23), _fill(base));
    for (final p in const <Offset>[Offset(37, 47), Offset(47, 52), Offset(59, 46), Offset(65, 53)]) {
      c.drawCircle(p, 3.5, _fill(p.dx.round().isEven ? const Color(0xFFD95C4C) : const Color(0xFFE1D267)));
    }
    if (chicken) c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(43, 42, 19, 8), const Radius.circular(4)), _fill(const Color(0xFFD3A068)));
    if (fish) c.drawOval(const Rect.fromLTWH(42, 42, 22, 9), _fill(const Color(0xFF9BB7B2)));
    if (feta) for (final p in const <Offset>[Offset(43, 43), Offset(57, 50)]) c.drawRect(Rect.fromCenter(center: p, width: 7, height: 6), _fill(const Color(0xFFF3EBD7)));
  }

  void _soup(Canvas c, Color soup, {bool herb = false, bool vegetables = false, bool chicken = false}) {
    _shadow(c);
    c.drawOval(const Rect.fromLTWH(19, 45, 62, 34), _fill(const Color(0xFFE4ECE9)));
    c.drawOval(const Rect.fromLTWH(24, 37, 52, 25), _fill(soup));
    c.drawArc(const Rect.fromLTWH(23, 36, 54, 27), 0, math.pi, false, _stroke(const Color(0xFF1F9E7A), 1.5));
    if (herb) for (final p in const <Offset>[Offset(42, 46), Offset(55, 50), Offset(62, 44)]) c.drawOval(Rect.fromCenter(center: p, width: 7, height: 4), _fill(const Color(0xFF6F9B5D)));
    if (vegetables) for (final p in const <Offset>[Offset(40, 47), Offset(51, 44), Offset(61, 50)]) c.drawCircle(p, 3, _fill(p.dx.round().isEven ? const Color(0xFFE39B42) : const Color(0xFF79A568)));
    if (chicken) c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(42, 44, 18, 7), const Radius.circular(3)), _fill(const Color(0xFFE4C18C)));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch14 oldDelegate) => oldDelegate.foodId != foodId;
}
