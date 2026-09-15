import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch13Ids = <String>{
  'cake', 'bastilla_milk', 'khanfaroosh', 'kunafa', 'maamoul', 'mhalbiya',
  'mhancha', 'honey', 'molasses', 'umm_ali', 'qatayef', 'sago_dessert',
  'date_syrup', 'stevia', 'sugar', 'brown_sugar', 'bocadillo', 'chips',
  'fries', 'hot_dog', 'nuggets', 'panini', 'popcorn', 'fried_chicken',
};

bool hasCodeFoodPictogramBatch13(String foodId) =>
    codeFoodPictogramBatch13Ids.contains(foodId);

class FoodPictogramPainterBatch13 extends CustomPainter {
  final String foodId;
  const FoodPictogramPainterBatch13(this.foodId);

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
      case 'cake': _cake(canvas); break;
      case 'bastilla_milk': _layered(canvas, const Color(0xFFE7C884)); break;
      case 'khanfaroosh': _friedSweet(canvas, const Color(0xFFB97943)); break;
      case 'kunafa': _kunafa(canvas); break;
      case 'maamoul': _cookie(canvas, stamped: true); break;
      case 'mhalbiya': _pudding(canvas, const Color(0xFFF3E9D5)); break;
      case 'mhancha': _coil(canvas); break;
      case 'honey': _jar(canvas, const Color(0xFFDCA53B)); break;
      case 'molasses': _jar(canvas, const Color(0xFF6E4331)); break;
      case 'umm_ali': _pudding(canvas, const Color(0xFFD9B575), nuts: true); break;
      case 'qatayef': _crescent(canvas, const Color(0xFFD9A85C)); break;
      case 'sago_dessert': _pudding(canvas, const Color(0xFFC8875B), pearls: true); break;
      case 'date_syrup': _jar(canvas, const Color(0xFF8B5438)); break;
      case 'stevia': _leaf(canvas); break;
      case 'sugar': _sugar(canvas, const Color(0xFFF5F0E5)); break;
      case 'brown_sugar': _sugar(canvas, const Color(0xFFC79A68)); break;
      case 'bocadillo': _sandwich(canvas, long: true); break;
      case 'chips': _chips(canvas); break;
      case 'fries': _fries(canvas); break;
      case 'hot_dog': _hotDog(canvas); break;
      case 'nuggets': _nuggets(canvas); break;
      case 'panini': _sandwich(canvas, long: false); break;
      case 'popcorn': _popcorn(canvas); break;
      case 'fried_chicken': _friedChicken(canvas); break;
      default: break;
    }
    canvas.restore();
  }

  void _cake(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(32, 40, 38, 28), const Radius.circular(5)), _fill(const Color(0xFFD7A25E)));
    c.drawRect(const Rect.fromLTWH(32, 40, 38, 8), _fill(const Color(0xFFF0DAB2)));
    c.drawCircle(const Offset(52, 36), 3, _fill(const Color(0xFFC44A4E)));
  }

  void _layered(Canvas c, Color fill) {
    _plate(c);
    for (var i = 0; i < 3; i++) {
      c.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(32 + i * 2.0, 39 + i * 8.0, 38 - i * 4.0, 8), const Radius.circular(3)), _fill(i.isEven ? fill : const Color(0xFFF4E8CA)));
    }
  }

  void _friedSweet(Canvas c, Color fill) {
    _plate(c);
    c.drawCircle(const Offset(50, 53), 18, _fill(fill));
    c.drawCircle(const Offset(50, 53), 7, _fill(const Color(0xFFF7E6C2)));
  }

  void _kunafa(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(50, 53), 19, _fill(const Color(0xFFD9A144)));
    for (var i = 0; i < 7; i++) {
      final a = i * math.pi / 3.5;
      c.drawLine(Offset(50 + math.cos(a) * 4, 53 + math.sin(a) * 4), Offset(50 + math.cos(a) * 17, 53 + math.sin(a) * 17), _stroke(const Color(0xFFF0CC7D), 1.2));
    }
  }

  void _cookie(Canvas c, {required bool stamped}) {
    _plate(c);
    c.drawCircle(const Offset(50, 53), 18, _fill(const Color(0xFFD8B076)));
    if (stamped) {
      c.drawCircle(const Offset(50, 53), 10, _stroke(const Color(0xFFA77D51), 1.5));
      for (var i = 0; i < 6; i++) {
        final a = i * math.pi / 3;
        c.drawCircle(Offset(50 + math.cos(a) * 7, 53 + math.sin(a) * 7), 1.5, _fill(const Color(0xFFA77D51)));
      }
    }
  }

  void _pudding(Canvas c, Color fill, {bool nuts = false, bool pearls = false}) {
    _shadow(c);
    c.drawOval(const Rect.fromLTWH(21, 46, 58, 33), _fill(const Color(0xFFE4ECE9)));
    c.drawOval(const Rect.fromLTWH(26, 39, 48, 22), _fill(fill));
    if (nuts) for (final p in const <Offset>[Offset(42, 48), Offset(53, 45), Offset(62, 51)]) c.drawOval(Rect.fromCenter(center: p, width: 7, height: 4), _fill(const Color(0xFF8D6843)));
    if (pearls) for (final p in const <Offset>[Offset(39, 47), Offset(49, 44), Offset(59, 48), Offset(45, 54), Offset(56, 55)]) c.drawCircle(p, 2.2, _fill(const Color(0xFFE5C7A4)));
  }

  void _coil(Canvas c) {
    _plate(c);
    for (var i = 0; i < 4; i++) {
      c.drawArc(Rect.fromCenter(center: const Offset(50, 53), width: 15 + i * 9, height: 15 + i * 9), .3 + i * .4, 4.6, false, _stroke(const Color(0xFFC98C4E), 3));
    }
  }

  void _jar(Canvas c, Color fill) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(36, 34, 29, 38), const Radius.circular(6)), _fill(const Color(0xFFDDE9E7)));
    c.drawRect(const Rect.fromLTWH(39, 45, 23, 23), _fill(fill));
    c.drawRect(const Rect.fromLTWH(39, 30, 23, 7), _fill(const Color(0xFF879491)));
  }

  void _crescent(Canvas c, Color fill) {
    _plate(c);
    final outer = Path()..addOval(const Rect.fromLTWH(29, 36, 44, 34));
    final inner = Path()..addOval(const Rect.fromLTWH(39, 33, 36, 30));
    c.drawPath(Path.combine(PathOperation.difference, outer, inner), _fill(fill));
  }

  void _leaf(Canvas c) {
    _plate(c);
    c.drawLine(const Offset(50, 69), const Offset(50, 34), _stroke(const Color(0xFF547C51), 2));
    for (var i = 0; i < 5; i++) {
      final y = 61.0 - i * 6;
      final dx = i.isEven ? -8.0 : 8.0;
      c.drawOval(Rect.fromCenter(center: Offset(50 + dx, y), width: 14, height: 8), _fill(const Color(0xFF78A765)));
    }
  }

  void _sugar(Canvas c, Color fill) {
    _plate(c);
    for (final p in const <Offset>[Offset(40, 52), Offset(51, 45), Offset(62, 53), Offset(47, 62), Offset(58, 62)]) {
      c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center: p, width: 11, height: 9), const Radius.circular(2)), _fill(fill));
    }
  }

  void _sandwich(Canvas c, {required bool long}) {
    _plate(c);
    final w = long ? 48.0 : 40.0;
    c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center: const Offset(50, 48), width: w, height: 13), const Radius.circular(6)), _fill(const Color(0xFFD9A35F)));
    c.drawRect(Rect.fromCenter(center: const Offset(50, 55), width: w - 5, height: 6), _fill(const Color(0xFF7FA968)));
    c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center: const Offset(50, 63), width: w, height: 13), const Radius.circular(6)), _fill(const Color(0xFFC99155)));
  }

  void _chips(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(37, 32, 26, 41), const Radius.circular(5)), _fill(const Color(0xFFE9C55D)));
    for (final p in const <Offset>[Offset(45, 49), Offset(55, 46), Offset(51, 59)]) c.drawOval(Rect.fromCenter(center: p, width: 10, height: 6), _fill(const Color(0xFFF6E4A0)));
  }

  void _fries(Canvas c) {
    _plate(c);
    for (final x in const <double>[39, 45, 51, 57, 63]) c.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x, 32 + (x % 2) * 2, 5, 29), const Radius.circular(2)), _fill(const Color(0xFFE9C258)));
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(36, 50, 31, 23), const Radius.circular(4)), _fill(const Color(0xFFC94A3E)));
  }

  void _hotDog(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(28, 45, 45, 20), const Radius.circular(10)), _fill(const Color(0xFFD49A58)));
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(33, 49, 35, 12), const Radius.circular(6)), _fill(const Color(0xFFA94D3D)));
    c.drawArc(const Rect.fromLTWH(36, 49, 28, 10), 0, math.pi, false, _stroke(const Color(0xFFE4C754), 2));
  }

  void _nuggets(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(39, 50), Offset(53, 45), Offset(62, 57), Offset(46, 62)]) {
      c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center: p, width: 16, height: 12), const Radius.circular(6)), _fill(const Color(0xFFC98B45)));
    }
  }

  void _popcorn(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(38, 45, 25, 28), const Radius.circular(4)), _fill(const Color(0xFFC8473E)));
    for (final p in const <Offset>[Offset(40, 43), Offset(47, 38), Offset(54, 42), Offset(61, 38), Offset(57, 48), Offset(45, 49)]) c.drawCircle(p, 7, _fill(const Color(0xFFF5EACD)));
  }

  void _friedChicken(Canvas c) {
    _plate(c);
    c.drawOval(const Rect.fromLTWH(33, 38, 30, 29), _fill(const Color(0xFFB97342)));
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(58, 49, 18, 7), const Radius.circular(4)), _fill(const Color(0xFFE4D4B5)));
    c.drawCircle(const Offset(75, 52), 5, _fill(const Color(0xFFE4D4B5)));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch13 oldDelegate) => oldDelegate.foodId != foodId;
}
