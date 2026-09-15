import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch12Ids = <String>{
  'coconut_water', 'sparkling_water', 'juice', 'orange_juice', 'apple_juice',
  'milkshake', 'protein_shake', 'smoothie', 'soft_drink', 'diet_soft_drink',
  'black_tea', 'green_tea', 'baklava', 'basbousa', 'cookie', 'chebakia',
  'chocolate', 'dark_chocolate', 'jam', 'gazelle_horns', 'croissant',
  'atayef_moroccan', 'ghriyba', 'ice_cream',
};

bool hasCodeFoodPictogramBatch12(String foodId) =>
    codeFoodPictogramBatch12Ids.contains(foodId);

class FoodPictogramPainterBatch12 extends CustomPainter {
  final String foodId;
  const FoodPictogramPainterBatch12(this.foodId);

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
      case 'coconut_water': _glass(canvas, const Color(0xFFE9F3EE), coconut: true); break;
      case 'sparkling_water': _glass(canvas, const Color(0xFFDDF1F8), bubbles: true); break;
      case 'juice': _juice(canvas, const Color(0xFFE6A748)); break;
      case 'orange_juice': _juice(canvas, const Color(0xFFEA922D)); break;
      case 'apple_juice': _juice(canvas, const Color(0xFFE7C65B)); break;
      case 'milkshake': _shake(canvas, const Color(0xFFF1E5D7)); break;
      case 'protein_shake': _shake(canvas, const Color(0xFFD8B994)); break;
      case 'smoothie': _shake(canvas, const Color(0xFFC96B77)); break;
      case 'soft_drink': _can(canvas, const Color(0xFFC54C43)); break;
      case 'diet_soft_drink': _can(canvas, const Color(0xFF6B7E87)); break;
      case 'black_tea': _tea(canvas, const Color(0xFF74513C)); break;
      case 'green_tea': _tea(canvas, const Color(0xFF89A867)); break;
      case 'baklava': _pastry(canvas, const Color(0xFFD6A34A), layers: true); break;
      case 'basbousa': _cake(canvas, const Color(0xFFE3B95E)); break;
      case 'cookie': _cookie(canvas); break;
      case 'chebakia': _spiral(canvas); break;
      case 'chocolate': _chocolate(canvas, const Color(0xFF81513B)); break;
      case 'dark_chocolate': _chocolate(canvas, const Color(0xFF4D332B)); break;
      case 'jam': _jar(canvas); break;
      case 'gazelle_horns': _crescent(canvas); break;
      case 'croissant': _crescent(canvas, croissant: true); break;
      case 'atayef_moroccan': _pancakes(canvas); break;
      case 'ghriyba': _ghriyba(canvas); break;
      case 'ice_cream': _iceCream(canvas); break;
      default: break;
    }
    canvas.restore();
  }

  void _glass(Canvas c, Color liquid, {bool bubbles = false, bool coconut = false}) {
    _shadow(c);
    final glass = Path()..moveTo(36, 31)..lineTo(64, 31)..lineTo(60, 73)..quadraticBezierTo(50, 77, 40, 73)..close();
    c.drawPath(glass, _fill(const Color(0xFFDCE9E8).withValues(alpha: .72)));
    final inside = Path()..moveTo(39, 43)..lineTo(61, 43)..lineTo(58, 70)..quadraticBezierTo(50, 73, 42, 70)..close();
    c.drawPath(inside, _fill(liquid));
    if (bubbles) for (final p in const <Offset>[Offset(45, 50), Offset(55, 47), Offset(50, 60), Offset(57, 64)]) c.drawCircle(p, 1.7, _stroke(const Color(0xFF6EAFC8), 1));
    if (coconut) c.drawOval(const Rect.fromLTWH(55, 27, 16, 9), _fill(const Color(0xFF6D8C58)));
  }

  void _juice(Canvas c, Color liquid) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(38, 33, 24, 38), const Radius.circular(5)), _fill(const Color(0xFFDDE9E7)));
    c.drawRect(const Rect.fromLTWH(41, 44, 18, 24), _fill(liquid));
    c.drawLine(const Offset(57, 36), const Offset(66, 24), _stroke(const Color(0xFF6C8B88), 2));
  }

  void _shake(Canvas c, Color fill) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(38, 34, 24, 37), const Radius.circular(7)), _fill(fill));
    c.drawOval(const Rect.fromLTWH(37, 29, 26, 12), _fill(const Color(0xFFF4EFE7)));
    c.drawLine(const Offset(57, 33), const Offset(65, 21), _stroke(const Color(0xFF7C8E8B), 2));
  }

  void _can(Canvas c, Color fill) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(39, 29, 22, 45), const Radius.circular(5)), _fill(fill));
    c.drawLine(const Offset(43, 34), const Offset(57, 34), _stroke(const Color(0xFFE1E7E5), 1.5));
  }

  void _tea(Canvas c, Color liquid) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(34, 40, 32, 25), const Radius.circular(6)), _fill(const Color(0xFFF2EEE6)));
    c.drawOval(const Rect.fromLTWH(38, 40, 24, 9), _fill(liquid));
    c.drawArc(const Rect.fromLTWH(59, 45, 18, 15), -.8, 2.1, false, _stroke(const Color(0xFFF2EEE6), 4));
  }

  void _pastry(Canvas c, Color fill, {required bool layers}) {
    _plate(c);
    final r = RRect.fromRectAndRadius(const Rect.fromLTWH(31, 40, 39, 25), const Radius.circular(4));
    c.drawRRect(r, _fill(fill));
    if (layers) for (final y in const <double>[47, 54, 61]) c.drawLine(Offset(34, y), Offset(67, y), _stroke(const Color(0xFFF1D18A), 1));
  }

  void _cake(Canvas c, Color fill) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(32, 40, 37, 27), const Radius.circular(4)), _fill(fill));
    c.drawRect(const Rect.fromLTWH(32, 40, 37, 7), _fill(const Color(0xFFF4E5C4)));
  }

  void _cookie(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(50, 53), 19, _fill(const Color(0xFFC99458)));
    for (final p in const <Offset>[Offset(43, 47), Offset(55, 44), Offset(58, 56), Offset(46, 61)]) c.drawCircle(p, 2.2, _fill(const Color(0xFF6E4C36)));
  }

  void _spiral(Canvas c) {
    _plate(c);
    for (var i = 0; i < 4; i++) c.drawArc(Rect.fromCenter(center: const Offset(50, 53), width: 18 + i * 8, height: 18 + i * 8), .2 + i * .5, 3.8, false, _stroke(const Color(0xFFB9783F), 3));
  }

  void _chocolate(Canvas c, Color fill) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(33, 38, 35, 30), const Radius.circular(3)), _fill(fill));
    for (final x in const <double>[44, 56]) c.drawLine(Offset(x, 40), Offset(x, 66), _stroke(const Color(0xFFD0A17B).withValues(alpha: .35), 1));
    c.drawLine(const Offset(35, 53), const Offset(66, 53), _stroke(const Color(0xFFD0A17B).withValues(alpha: .35), 1));
  }

  void _jar(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(36, 35, 29, 37), const Radius.circular(6)), _fill(const Color(0xFFDDE9E7)));
    c.drawRect(const Rect.fromLTWH(39, 45, 23, 23), _fill(const Color(0xFFB94E58)));
    c.drawRect(const Rect.fromLTWH(39, 31, 23, 7), _fill(const Color(0xFF82918E)));
  }

  void _crescent(Canvas c, {bool croissant = false}) {
    _plate(c);
    final outer = Path()..addOval(const Rect.fromLTWH(28, 35, 45, 35));
    final inner = Path()..addOval(const Rect.fromLTWH(38, 32, 38, 31));
    final path = Path.combine(PathOperation.difference, outer, inner);
    c.drawPath(path, _fill(croissant ? const Color(0xFFD79A4D) : const Color(0xFFE3B66A)));
  }

  void _pancakes(Canvas c) {
    _plate(c);
    for (final y in const <double>[58, 52, 46]) c.drawOval(Rect.fromLTWH(32, y - 7, 38, 12), _fill(const Color(0xFFD9A45A)));
    c.drawCircle(const Offset(52, 43), 5, _fill(const Color(0xFFF2D07A)));
  }

  void _ghriyba(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(50, 53), 18, _fill(const Color(0xFFE2C797)));
    c.drawLine(const Offset(42, 45), const Offset(58, 61), _stroke(const Color(0xFFB38C62), 1.4));
    c.drawLine(const Offset(58, 45), const Offset(42, 61), _stroke(const Color(0xFFB38C62), 1.4));
  }

  void _iceCream(Canvas c) {
    _plate(c);
    final cone = Path()..moveTo(41, 53)..lineTo(59, 53)..lineTo(50, 75)..close();
    c.drawPath(cone, _fill(const Color(0xFFC99558)));
    c.drawCircle(const Offset(50, 45), 12, _fill(const Color(0xFFF0B5B5)));
    c.drawCircle(const Offset(43, 48), 9, _fill(const Color(0xFFF4DFB7)));
    c.drawCircle(const Offset(57, 49), 9, _fill(const Color(0xFFB8C989)));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch12 oldDelegate) => oldDelegate.foodId != foodId;
}
