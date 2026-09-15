import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch11Ids = <String>{
  'flax_seeds',
  'sunflower_seeds',
  'hazelnuts',
  'walnuts',
  'cashews',
  'pistachios',
  'almond_butter',
  'sesame',
  'chermoula',
  'harissa',
  'argan_oil',
  'sunflower_oil',
  'ketchup',
  'mayonnaise',
  'olives',
  'barbecue_sauce',
  'hot_sauce',
  'soy_sauce',
  'garlic_sauce',
  'tahini',
  'ayran',
  'energy_drink',
  'coffee',
  'water',
};

bool hasCodeFoodPictogramBatch11(String foodId) =>
    codeFoodPictogramBatch11Ids.contains(foodId);

class FoodPictogramPainterBatch11 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch11(this.foodId);

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

  void _shadow(Canvas c) {
    c.drawShadow(Path()..addOval(const Rect.fromLTWH(20, 76, 60, 7)), Colors.black.withValues(alpha: .14), 4, false);
  }

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
      case 'flax_seeds':
        _seeds(canvas, const Color(0xFF9B6B42));
        break;
      case 'sunflower_seeds':
        _seeds(canvas, const Color(0xFF4F4B42));
        break;
      case 'hazelnuts':
        _nuts(canvas, const Color(0xFF9A693E), round: true);
        break;
      case 'walnuts':
        _walnuts(canvas);
        break;
      case 'cashews':
        _cashews(canvas);
        break;
      case 'pistachios':
        _pistachios(canvas);
        break;
      case 'almond_butter':
        _spread(canvas, const Color(0xFFB98455));
        break;
      case 'sesame':
        _seeds(canvas, const Color(0xFFE5D3A4));
        break;
      case 'chermoula':
        _sauceBowl(canvas, const Color(0xFF5A9A5D));
        break;
      case 'harissa':
        _sauceBowl(canvas, const Color(0xFFC74335));
        break;
      case 'argan_oil':
        _oil(canvas, const Color(0xFFC48A38));
        break;
      case 'sunflower_oil':
        _oil(canvas, const Color(0xFFE1B94A));
        break;
      case 'ketchup':
        _bottle(canvas, const Color(0xFFC93E34));
        break;
      case 'mayonnaise':
        _bottle(canvas, const Color(0xFFF2E5B7));
        break;
      case 'olives':
        _olives(canvas);
        break;
      case 'barbecue_sauce':
        _bottle(canvas, const Color(0xFF7E3D31));
        break;
      case 'hot_sauce':
        _bottle(canvas, const Color(0xFFE24E35));
        break;
      case 'soy_sauce':
        _bottle(canvas, const Color(0xFF4C352D));
        break;
      case 'garlic_sauce':
        _sauceBowl(canvas, const Color(0xFFF0EAD9));
        break;
      case 'tahini':
        _sauceBowl(canvas, const Color(0xFFDCC99E));
        break;
      case 'ayran':
        _glass(canvas, const Color(0xFFF4F2E7), const Color(0xFF79A4B6));
        break;
      case 'energy_drink':
        _can(canvas);
        break;
      case 'coffee':
        _coffee(canvas);
        break;
      case 'water':
        _glass(canvas, const Color(0xFFD8EEF5), const Color(0xFF5BA5C8));
        break;
      default:
        break;
    }

    canvas.restore();
  }

  void _seeds(Canvas c, Color color) {
    _plate(c);
    for (var row = 0; row < 4; row++) {
      for (var col = 0; col < 6; col++) {
        c.drawOval(Rect.fromCenter(center: Offset(35 + col * 6.0, 42 + row * 7.0), width: 3.5, height: 6), _fill(color));
      }
    }
  }

  void _nuts(Canvas c, Color color, {required bool round}) {
    _plate(c);
    for (final p in const <Offset>[Offset(39, 50), Offset(51, 43), Offset(62, 51), Offset(46, 61), Offset(58, 61)]) {
      c.drawOval(Rect.fromCenter(center: p, width: round ? 13 : 10, height: round ? 13 : 18), _fill(color));
    }
  }

  void _walnuts(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(42, 50), Offset(57, 51), Offset(49, 62)]) {
      c.drawCircle(p, 9, _fill(const Color(0xFFB78D5E)));
      c.drawArc(Rect.fromCenter(center: p, width: 13, height: 13), .2, 2.8, false, _stroke(const Color(0xFF8F6748), 1.3));
    }
  }

  void _cashews(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(40, 49), Offset(55, 45), Offset(61, 59), Offset(45, 62)]) {
      c.drawArc(Rect.fromCenter(center: p, width: 16, height: 18), .5, 4.2, false, _stroke(const Color(0xFFDAB77E), 5));
    }
  }

  void _pistachios(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(40, 50), Offset(52, 44), Offset(63, 53), Offset(48, 62)]) {
      c.drawOval(Rect.fromCenter(center: p, width: 13, height: 20), _fill(const Color(0xFFD9C49A)));
      c.drawOval(Rect.fromCenter(center: p, width: 7, height: 14), _fill(const Color(0xFF92A75F)));
    }
  }

  void _spread(Canvas c, Color color) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(35, 35, 31, 38), const Radius.circular(8)), _fill(const Color(0xFFD9C29A)));
    c.drawRect(const Rect.fromLTWH(38, 43, 25, 23), _fill(color));
  }

  void _sauceBowl(Canvas c, Color sauce) {
    _shadow(c);
    c.drawOval(const Rect.fromLTWH(20, 45, 60, 34), _fill(const Color(0xFFE4ECE9)));
    c.drawOval(const Rect.fromLTWH(25, 38, 50, 23), _fill(sauce));
    c.drawArc(const Rect.fromLTWH(24, 37, 52, 25), 0, math.pi, false, _stroke(const Color(0xFF1F9E7A), 1.5));
  }

  void _oil(Canvas c, Color oil) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(39, 31, 22, 42), const Radius.circular(6)), _fill(const Color(0xFFDCE9E8).withValues(alpha: .7)));
    c.drawRect(const Rect.fromLTWH(42, 45, 16, 24), _fill(oil.withValues(alpha: .8)));
    c.drawRect(const Rect.fromLTWH(45, 25, 10, 8), _fill(const Color(0xFF6B7E79)));
  }

  void _bottle(Canvas c, Color sauce) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(40, 33, 20, 40), const Radius.circular(7)), _fill(sauce));
    c.drawRect(const Rect.fromLTWH(44, 27, 12, 8), _fill(const Color(0xFFE1E8E5)));
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(43, 47, 14, 11), const Radius.circular(3)), _fill(const Color(0xFFF4F6F5).withValues(alpha: .75)));
  }

  void _olives(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(40, 50), Offset(51, 44), Offset(61, 52), Offset(47, 61), Offset(59, 62)]) {
      c.drawOval(Rect.fromCenter(center: p, width: 11, height: 16), _fill(p.dx.round().isEven ? const Color(0xFF6E783B) : const Color(0xFF303C2C)));
      c.drawCircle(Offset(p.dx, p.dy - 3), 1.5, _fill(const Color(0xFFC0B46A)));
    }
  }

  void _glass(Canvas c, Color liquid, Color accent) {
    _shadow(c);
    final glass = Path()
      ..moveTo(36, 31)
      ..lineTo(64, 31)
      ..lineTo(60, 73)
      ..quadraticBezierTo(50, 77, 40, 73)
      ..close();
    c.drawPath(glass, _fill(const Color(0xFFDCE9E8).withValues(alpha: .72)));
    final inside = Path()
      ..moveTo(39, 43)
      ..lineTo(61, 43)
      ..lineTo(58, 70)
      ..quadraticBezierTo(50, 73, 42, 70)
      ..close();
    c.drawPath(inside, _fill(liquid));
    c.drawLine(const Offset(39, 43), const Offset(61, 43), _stroke(accent, 1.5));
  }

  void _can(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(39, 29, 22, 45), const Radius.circular(5)), _fill(const Color(0xFF4E6C73)));
    final bolt = Path()
      ..moveTo(52, 36)
      ..lineTo(45, 51)
      ..lineTo(51, 51)
      ..lineTo(47, 66)
      ..lineTo(58, 47)
      ..lineTo(52, 47)
      ..close();
    c.drawPath(bolt, _fill(const Color(0xFFE0C257)));
  }

  void _coffee(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(35, 40, 31, 25), const Radius.circular(6)), _fill(const Color(0xFFF3EFE6)));
    c.drawOval(const Rect.fromLTWH(38, 40, 25, 9), _fill(const Color(0xFF6B4632)));
    c.drawArc(const Rect.fromLTWH(59, 44, 18, 16), -.8, 2.1, false, _stroke(const Color(0xFFF3EFE6), 4));
    c.drawArc(const Rect.fromLTWH(40, 26, 8, 18), 2.9, 1.6, false, _stroke(const Color(0xFFA9B3AF), 1.4));
    c.drawArc(const Rect.fromLTWH(51, 24, 8, 19), 2.9, 1.6, false, _stroke(const Color(0xFFA9B3AF), 1.4));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch11 oldDelegate) => oldDelegate.foodId != foodId;
}
