import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch7Ids = <String>{
  'fish',
  'octopus',
  'tuna',
  'omelette',
  'fried_egg',
  'boiled_egg',
  'butter',
  'cream',
  'feta',
  'cheese',
  'processed_cheese',
  'fresh_cheese',
  'cream_cheese',
  'halloumi',
  'laban',
  'labneh',
  'camel_milk',
  'semi_skimmed_milk',
  'whole_milk',
  'skimmed_milk',
  'mozzarella',
  'qishta',
  'raib',
  'yogurt',
};

bool hasCodeFoodPictogramBatch7(String foodId) =>
    codeFoodPictogramBatch7Ids.contains(foodId);

class FoodPictogramPainterBatch7 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch7(this.foodId);

  static const _teal = Color(0xFF1F9E7A);
  static const _cream = Color(0xFFFFF7E8);
  static const _dark = Color(0xFF394743);

  Paint _fill(Color color) => Paint()
    ..style = PaintingStyle.fill
    ..color = color
    ..isAntiAlias = true;

  Paint _stroke(Color color, double width) => Paint()
    ..style = PaintingStyle.stroke
    ..strokeWidth = width
    ..strokeCap = StrokeCap.round
    ..strokeJoin = StrokeJoin.round
    ..color = color
    ..isAntiAlias = true;

  Paint _gradient(Rect rect, Color a, Color b) => Paint()
    ..shader = LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: <Color>[a, b],
    ).createShader(rect);

  void _shadow(Canvas c, Rect rect) {
    c.drawShadow(Path()..addOval(rect), Colors.black.withValues(alpha: .14), 4, false);
  }

  void _plate(Canvas c) {
    _shadow(c, const Rect.fromLTWH(16, 77, 68, 7));
    c.drawOval(const Rect.fromLTWH(15, 48, 70, 31), _fill(const Color(0xFFDDE8E4)));
    c.drawOval(const Rect.fromLTWH(20, 44, 60, 30), _fill(const Color(0xFFFAFCFB)));
  }

  void _bowl(Canvas c, Color inside) {
    _shadow(c, const Rect.fromLTWH(19, 77, 62, 7));
    c.drawOval(const Rect.fromLTWH(19, 45, 62, 34), _fill(const Color(0xFFE4ECE9)));
    c.drawOval(const Rect.fromLTWH(24, 37, 52, 25), _fill(inside));
    c.drawArc(const Rect.fromLTWH(23, 36, 54, 27), 0, math.pi, false, _stroke(_teal, 1.5));
  }

  @override
  void paint(Canvas canvas, Size size) {
    final side = math.min(size.width, size.height);
    canvas.save();
    canvas.translate((size.width - side) / 2, (size.height - side) / 2);
    canvas.scale(side / 100, side / 100);

    switch (foodId) {
      case 'fish':
        _fish(canvas, const Color(0xFFA5BBB5), tuna: false);
        break;
      case 'octopus':
        _octopus(canvas);
        break;
      case 'tuna':
        _fish(canvas, const Color(0xFF6F9695), tuna: true);
        break;
      case 'omelette':
        _omelette(canvas);
        break;
      case 'fried_egg':
        _friedEgg(canvas);
        break;
      case 'boiled_egg':
        _boiledEgg(canvas);
        break;
      case 'butter':
        _butter(canvas);
        break;
      case 'cream':
        _dairyBowl(canvas, const Color(0xFFF5EFE0), swirl: true);
        break;
      case 'feta':
        _cheeseBlock(canvas, const Color(0xFFF4EEDC), holes: false, cubes: true);
        break;
      case 'cheese':
        _cheeseWedge(canvas, const Color(0xFFF0C95F), holes: true);
        break;
      case 'processed_cheese':
        _cheeseSlice(canvas);
        break;
      case 'fresh_cheese':
        _dairyBowl(canvas, const Color(0xFFF7F3E7), swirl: false);
        break;
      case 'cream_cheese':
        _dairyBowl(canvas, const Color(0xFFF3EEDF), swirl: true, thick: true);
        break;
      case 'halloumi':
        _halloumi(canvas);
        break;
      case 'laban':
        _milkGlass(canvas, const Color(0xFFF2F0E5), accent: _teal);
        break;
      case 'labneh':
        _dairyBowl(canvas, const Color(0xFFF7F4EA), swirl: true, olive: true);
        break;
      case 'camel_milk':
        _milkGlass(canvas, const Color(0xFFF2E7D5), accent: const Color(0xFFC79B5D));
        break;
      case 'semi_skimmed_milk':
        _milkGlass(canvas, const Color(0xFFF5F6EE), accent: const Color(0xFF74A6C9));
        break;
      case 'whole_milk':
        _milkGlass(canvas, const Color(0xFFFFF9E9), accent: const Color(0xFFD7B553));
        break;
      case 'skimmed_milk':
        _milkGlass(canvas, const Color(0xFFF7FAF8), accent: const Color(0xFF8BB8D4));
        break;
      case 'mozzarella':
        _mozzarella(canvas);
        break;
      case 'qishta':
        _dairyBowl(canvas, const Color(0xFFF5E9CF), swirl: true, thick: true);
        break;
      case 'raib':
        _milkGlass(canvas, const Color(0xFFF3EEE3), accent: const Color(0xFF8AAE88));
        break;
      case 'yogurt':
        _yogurtCup(canvas);
        break;
      default:
        break;
    }
    canvas.restore();
  }

  void _fish(Canvas c, Color color, {required bool tuna}) {
    _plate(c);
    final body = Path()
      ..moveTo(27, 51)
      ..quadraticBezierTo(43, 31, 66, 42)
      ..lineTo(81, 32)
      ..lineTo(78, 51)
      ..lineTo(81, 69)
      ..lineTo(66, 59)
      ..quadraticBezierTo(43, 70, 27, 51)
      ..close();
    c.drawPath(body, _gradient(const Rect.fromLTWH(27, 32, 54, 37), const Color(0xFFDDE6E2), color));
    if (tuna) {
      c.drawArc(const Rect.fromLTWH(34, 35, 34, 28), 3.6, 2.3, false, _stroke(const Color(0xFF4D6C70), 3));
    }
    c.drawCircle(const Offset(35, 48), 1.6, _fill(_dark));
    c.drawLine(const Offset(50, 40), const Offset(47, 61), _stroke(const Color(0xFF6F8580), 1.2));
  }

  void _octopus(Canvas c) {
    _plate(c);
    c.drawOval(const Rect.fromLTWH(37, 28, 27, 31), _gradient(const Rect.fromLTWH(37, 28, 27, 31), const Color(0xFFD89A91), const Color(0xFF9E5C64)));
    c.drawCircle(const Offset(45, 42), 1.7, _fill(_dark));
    c.drawCircle(const Offset(56, 42), 1.7, _fill(_dark));
    for (var i = 0; i < 6; i++) {
      final x = 32.0 + i * 7.0;
      c.drawArc(Rect.fromLTWH(x, 53, 20, 22), .2, 2.5, false, _stroke(const Color(0xFFB66E74), 3));
    }
  }

  void _omelette(Canvas c) {
    _plate(c);
    final path = Path()
      ..moveTo(28, 58)
      ..quadraticBezierTo(31, 38, 53, 34)
      ..quadraticBezierTo(76, 39, 73, 60)
      ..quadraticBezierTo(53, 70, 28, 58)
      ..close();
    c.drawPath(path, _gradient(const Rect.fromLTWH(28, 34, 45, 36), const Color(0xFFF5D56B), const Color(0xFFD9A53A)));
    for (final p in const <Offset>[Offset(41, 49), Offset(55, 44), Offset(62, 55)]) {
      c.drawCircle(p, 2.4, _fill(const Color(0xFF84A35A)));
    }
  }

  void _friedEgg(Canvas c) {
    _plate(c);
    final white = Path()
      ..moveTo(29, 53)
      ..quadraticBezierTo(27, 38, 43, 38)
      ..quadraticBezierTo(53, 29, 64, 40)
      ..quadraticBezierTo(78, 43, 71, 57)
      ..quadraticBezierTo(66, 70, 51, 64)
      ..quadraticBezierTo(36, 70, 29, 53)
      ..close();
    c.drawPath(white, _fill(const Color(0xFFF8F6EC)));
    c.drawCircle(const Offset(51, 50), 10, _gradient(const Rect.fromLTWH(41, 40, 20, 20), const Color(0xFFFFD557), const Color(0xFFE9A52E)));
  }

  void _boiledEgg(Canvas c) {
    _plate(c);
    for (final x in const <double>[40, 60]) {
      c.drawOval(Rect.fromCenter(center: Offset(x, 51), width: 25, height: 34), _fill(const Color(0xFFF8F4E8)));
      c.drawCircle(Offset(x, 52), 7, _fill(const Color(0xFFF2B638)));
    }
  }

  void _butter(Canvas c) {
    _plate(c);
    final rect = const Rect.fromLTWH(31, 37, 39, 27);
    c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(5)), _gradient(rect, const Color(0xFFFFE58D), const Color(0xFFE7B94A)));
    c.drawLine(const Offset(37, 45), const Offset(64, 45), _stroke(const Color(0xFFFFF1B5), 2));
  }

  void _dairyBowl(Canvas c, Color base, {required bool swirl, bool thick = false, bool olive = false}) {
    _bowl(c, base);
    c.drawOval(const Rect.fromLTWH(32, 40, 36, 19), _fill(base));
    if (swirl) {
      c.drawArc(const Rect.fromLTWH(38, 43, 24, 11), .2, 2.8, false, _stroke(const Color(0xFFD8D3C6), thick ? 2.2 : 1.4));
    }
    if (olive) {
      c.drawCircle(const Offset(53, 47), 3, _fill(const Color(0xFFB8A847)));
      c.drawArc(const Rect.fromLTWH(41, 42, 20, 13), .4, 2.0, false, _stroke(const Color(0xFF6D8D52), 1.5));
    }
  }

  void _cheeseBlock(Canvas c, Color color, {required bool holes, required bool cubes}) {
    _plate(c);
    if (cubes) {
      for (final p in const <Offset>[Offset(39, 47), Offset(54, 42), Offset(63, 55), Offset(47, 59)]) {
        final rect = Rect.fromCenter(center: p, width: 16, height: 12);
        c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(2)), _gradient(rect, const Color(0xFFFFF9EC), color));
      }
      return;
    }
    final rect = const Rect.fromLTWH(30, 37, 40, 27);
    c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(4)), _fill(color));
    if (holes) {
      for (final p in const <Offset>[Offset(42, 47), Offset(57, 43), Offset(61, 55)]) {
        c.drawCircle(p, 2.5, _fill(const Color(0xFFD2AA43)));
      }
    }
  }

  void _cheeseWedge(Canvas c, Color color, {required bool holes}) {
    _plate(c);
    final wedge = Path()
      ..moveTo(29, 61)
      ..lineTo(69, 33)
      ..lineTo(72, 62)
      ..close();
    c.drawPath(wedge, _gradient(const Rect.fromLTWH(29, 33, 43, 29), const Color(0xFFFFE99A), color));
    if (holes) {
      for (final p in const <Offset>[Offset(52, 48), Offset(63, 43), Offset(60, 57)]) {
        c.drawCircle(p, 2.6, _fill(const Color(0xFFD2A73A)));
      }
    }
  }

  void _cheeseSlice(Canvas c) {
    _plate(c);
    c.save();
    c.translate(50, 50);
    c.rotate(-.14);
    c.translate(-50, -50);
    final rect = const Rect.fromLTWH(29, 38, 42, 27);
    c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(4)), _gradient(rect, const Color(0xFFFFE68A), const Color(0xFFE7B843)));
    c.restore();
  }

  void _halloumi(Canvas c) {
    _plate(c);
    for (var i = 0; i < 3; i++) {
      final rect = Rect.fromLTWH(31, 38 + i * 9.0, 39, 8);
      c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(3)), _fill(const Color(0xFFF1E4C5)));
      for (final x in const <double>[40, 50, 60]) {
        c.drawLine(Offset(x, rect.top + 1), Offset(x + 3, rect.bottom - 1), _stroke(const Color(0xFFB88755), 1.2));
      }
    }
  }

  void _milkGlass(Canvas c, Color milk, {required Color accent}) {
    _shadow(c, const Rect.fromLTWH(31, 77, 38, 6));
    final glass = Path()
      ..moveTo(34, 29)
      ..lineTo(66, 29)
      ..lineTo(62, 73)
      ..quadraticBezierTo(50, 78, 38, 73)
      ..close();
    c.drawPath(glass, _fill(const Color(0xFFDCE9E8).withValues(alpha: .72)));
    final liquid = Path()
      ..moveTo(38, 41)
      ..lineTo(62, 41)
      ..lineTo(59, 70)
      ..quadraticBezierTo(50, 73, 41, 70)
      ..close();
    c.drawPath(liquid, _fill(milk));
    c.drawLine(const Offset(38, 42), const Offset(62, 42), _stroke(accent, 2.2));
  }

  void _mozzarella(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(38, 52), Offset(52, 43), Offset(63, 56)]) {
      final rect = Rect.fromCenter(center: p, width: 19, height: 16);
      c.drawOval(rect, _gradient(rect, const Color(0xFFFFFFFF), const Color(0xFFE7E3D7)));
    }
  }

  void _yogurtCup(Canvas c) {
    _shadow(c, const Rect.fromLTWH(31, 77, 38, 6));
    final cup = Path()
      ..moveTo(33, 36)
      ..lineTo(67, 36)
      ..lineTo(62, 72)
      ..quadraticBezierTo(50, 77, 38, 72)
      ..close();
    c.drawPath(cup, _gradient(const Rect.fromLTWH(33, 36, 34, 40), const Color(0xFFF7FAF8), const Color(0xFFD8E8E4)));
    c.drawOval(const Rect.fromLTWH(31, 32, 38, 10), _fill(_teal));
    c.drawArc(const Rect.fromLTWH(40, 47, 20, 10), .2, 2.6, false, _stroke(const Color(0xFFB7C9C4), 1.5));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch7 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
