import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch10Ids = <String>{
  'guava',
  'pomegranate',
  'kiwi',
  'mandarin',
  'mango',
  'melon',
  'blueberry',
  'nectarine',
  'coconut',
  'orange_cinnamon',
  'grapefruit',
  'papaya',
  'watermelon',
  'pear',
  'plum',
  'prunes',
  'peach',
  'grapes',
  'raisins',
  'fruit_salad',
  'almonds',
  'peanut_butter',
  'peanuts',
  'chia_seeds',
};

bool hasCodeFoodPictogramBatch10(String foodId) =>
    codeFoodPictogramBatch10Ids.contains(foodId);

class FoodPictogramPainterBatch10 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch10(this.foodId);

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
    c.drawShadow(
      Path()..addOval(const Rect.fromLTWH(20, 76, 60, 7)),
      Colors.black.withValues(alpha: .14),
      4,
      false,
    );
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
      case 'guava':
        _roundFruit(canvas, const Color(0xFF9BC46C), seed: const Color(0xFFE98A7B));
        break;
      case 'pomegranate':
        _pomegranate(canvas);
        break;
      case 'kiwi':
        _kiwi(canvas);
        break;
      case 'mandarin':
        _roundFruit(canvas, const Color(0xFFE8912D));
        break;
      case 'mango':
        _mango(canvas);
        break;
      case 'melon':
        _melon(canvas);
        break;
      case 'blueberry':
        _berries(canvas, const Color(0xFF596AA7));
        break;
      case 'nectarine':
        _roundFruit(canvas, const Color(0xFFE66E4E));
        break;
      case 'coconut':
        _coconut(canvas);
        break;
      case 'orange_cinnamon':
        _orangeCinnamon(canvas);
        break;
      case 'grapefruit':
        _citrusHalf(canvas, const Color(0xFFE66F70));
        break;
      case 'papaya':
        _papaya(canvas);
        break;
      case 'watermelon':
        _watermelon(canvas);
        break;
      case 'pear':
        _pear(canvas);
        break;
      case 'plum':
        _roundFruit(canvas, const Color(0xFF7B507F));
        break;
      case 'prunes':
        _dried(canvas, const Color(0xFF654A58));
        break;
      case 'peach':
        _roundFruit(canvas, const Color(0xFFF0A067));
        break;
      case 'grapes':
        _grapes(canvas, dried: false);
        break;
      case 'raisins':
        _grapes(canvas, dried: true);
        break;
      case 'fruit_salad':
        _fruitSalad(canvas);
        break;
      case 'almonds':
        _nuts(canvas, const Color(0xFFC89058), almond: true);
        break;
      case 'peanut_butter':
        _spread(canvas);
        break;
      case 'peanuts':
        _peanuts(canvas);
        break;
      case 'chia_seeds':
        _seeds(canvas);
        break;
      default:
        break;
    }

    canvas.restore();
  }

  void _leaf(Canvas c, Offset p) {
    c.drawOval(Rect.fromCenter(center: p, width: 14, height: 7), _fill(const Color(0xFF5D8B57)));
  }

  void _roundFruit(Canvas c, Color color, {Color? seed}) {
    _plate(c);
    c.drawCircle(const Offset(50, 52), 19, _fill(color));
    c.drawCircle(const Offset(44, 46), 5, _fill(Colors.white.withValues(alpha: .15)));
    c.drawLine(const Offset(50, 35), const Offset(53, 28), _stroke(const Color(0xFF557653), 2));
    _leaf(c, const Offset(59, 31));
    if (seed != null) {
      c.drawCircle(const Offset(50, 52), 9, _fill(seed));
      for (final p in const <Offset>[Offset(47, 49), Offset(53, 49), Offset(50, 55), Offset(45, 55), Offset(55, 55)]) {
        c.drawCircle(p, 1.2, _fill(const Color(0xFFF6E5BC)));
      }
    }
  }

  void _pomegranate(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(50, 54), 19, _fill(const Color(0xFFB63D47)));
    final crown = Path()
      ..moveTo(43, 37)
      ..lineTo(46, 27)
      ..lineTo(51, 34)
      ..lineTo(56, 27)
      ..lineTo(58, 38)
      ..close();
    c.drawPath(crown, _fill(const Color(0xFF8B3038)));
  }

  void _kiwi(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(50, 53), 20, _fill(const Color(0xFF7A5B3E)));
    c.drawCircle(const Offset(50, 53), 15, _fill(const Color(0xFF9BC75F)));
    c.drawCircle(const Offset(50, 53), 4, _fill(const Color(0xFFF1E7C4)));
    for (var i = 0; i < 12; i++) {
      final a = i * math.pi / 6;
      c.drawCircle(Offset(50 + math.cos(a) * 10, 53 + math.sin(a) * 10), 1, _fill(const Color(0xFF2E332E)));
    }
  }

  void _mango(Canvas c) {
    _plate(c);
    c.save();
    c.translate(50, 52);
    c.rotate(-.3);
    c.translate(-50, -52);
    c.drawOval(const Rect.fromLTWH(33, 33, 35, 42), _fill(const Color(0xFFEFA447)));
    c.restore();
    _leaf(c, const Offset(63, 33));
  }

  void _melon(Canvas c) {
    _plate(c);
    c.drawOval(const Rect.fromLTWH(30, 37, 40, 34), _fill(const Color(0xFFD8C970)));
    for (final x in const <double>[39, 50, 61]) {
      c.drawArc(Rect.fromCenter(center: Offset(x, 54), width: 15, height: 31), 1.5, 3.2, false, _stroke(const Color(0xFFB3A14F), 1.2));
    }
  }

  void _berries(Canvas c, Color color) {
    _plate(c);
    for (final p in const <Offset>[Offset(40, 48), Offset(51, 43), Offset(61, 49), Offset(44, 58), Offset(56, 59)]) {
      c.drawCircle(p, 8, _fill(color));
      c.drawCircle(Offset(p.dx - 2, p.dy - 2), 2, _fill(Colors.white.withValues(alpha: .13)));
    }
  }

  void _coconut(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(45, 53), 18, _fill(const Color(0xFF75543D)));
    c.drawCircle(const Offset(45, 53), 13, _fill(const Color(0xFFF4EEE2)));
    c.drawCircle(const Offset(63, 58), 10, _fill(const Color(0xFF75543D)));
  }

  void _orangeCinnamon(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(43, 53), 16, _fill(const Color(0xFFE7952D)));
    c.drawCircle(const Offset(43, 53), 11, _stroke(const Color(0xFFFFD88A), 1.5));
    c.drawLine(const Offset(59, 39), const Offset(70, 66), _stroke(const Color(0xFF9B673D), 4));
  }

  void _citrusHalf(Canvas c, Color pulp) {
    _plate(c);
    c.drawCircle(const Offset(50, 53), 19, _fill(const Color(0xFFF4D077)));
    c.drawCircle(const Offset(50, 53), 14, _fill(pulp));
    for (var i = 0; i < 8; i++) {
      final a = i * math.pi / 4;
      c.drawLine(const Offset(50, 53), Offset(50 + math.cos(a) * 13, 53 + math.sin(a) * 13), _stroke(const Color(0xFFFBE7C7), .8));
    }
  }

  void _papaya(Canvas c) {
    _plate(c);
    c.drawOval(const Rect.fromLTWH(31, 34, 38, 39), _fill(const Color(0xFFE98C45)));
    c.drawOval(const Rect.fromLTWH(42, 43, 16, 22), _fill(const Color(0xFFF3C55C)));
    for (final p in const <Offset>[Offset(47, 49), Offset(53, 49), Offset(47, 57), Offset(53, 57)]) {
      c.drawCircle(p, 1.8, _fill(const Color(0xFF3C352D)));
    }
  }

  void _watermelon(Canvas c) {
    _plate(c);
    final wedge = Path()
      ..moveTo(28, 64)
      ..lineTo(72, 64)
      ..lineTo(50, 34)
      ..close();
    c.drawPath(wedge, _fill(const Color(0xFFDF5659)));
    c.drawLine(const Offset(28, 64), const Offset(72, 64), _stroke(const Color(0xFF66A45C), 5));
    for (final p in const <Offset>[Offset(43, 53), Offset(51, 47), Offset(58, 55)]) {
      c.drawOval(Rect.fromCenter(center: p, width: 2, height: 5), _fill(const Color(0xFF3A3A34)));
    }
  }

  void _pear(Canvas c) {
    _plate(c);
    final path = Path()
      ..moveTo(50, 31)
      ..quadraticBezierTo(42, 43, 37, 52)
      ..quadraticBezierTo(33, 69, 50, 72)
      ..quadraticBezierTo(67, 69, 63, 52)
      ..quadraticBezierTo(58, 43, 50, 31)
      ..close();
    c.drawPath(path, _fill(const Color(0xFFB6C86A)));
    c.drawLine(const Offset(50, 32), const Offset(53, 25), _stroke(const Color(0xFF6B6749), 2));
  }

  void _dried(Canvas c, Color color) {
    _plate(c);
    for (final p in const <Offset>[Offset(39, 51), Offset(51, 44), Offset(62, 53), Offset(47, 61), Offset(59, 62)]) {
      c.drawOval(Rect.fromCenter(center: p, width: 13, height: 10), _fill(color));
    }
  }

  void _grapes(Canvas c, {required bool dried}) {
    _plate(c);
    final color = dried ? const Color(0xFF795244) : const Color(0xFF7961A1);
    for (final p in const <Offset>[Offset(45, 41), Offset(55, 41), Offset(40, 50), Offset(50, 50), Offset(60, 50), Offset(45, 59), Offset(55, 59), Offset(50, 67)]) {
      c.drawCircle(p, dried ? 4 : 6, _fill(color));
    }
    c.drawLine(const Offset(50, 36), const Offset(55, 27), _stroke(const Color(0xFF5E8055), 2));
  }

  void _fruitSalad(Canvas c) {
    _shadow(c);
    c.drawOval(const Rect.fromLTWH(20, 45, 60, 34), _fill(const Color(0xFFE4ECE9)));
    c.drawOval(const Rect.fromLTWH(25, 38, 50, 23), _fill(const Color(0xFFF2D77B)));
    for (final p in const <Offset>[Offset(37, 46), Offset(47, 51), Offset(57, 45), Offset(65, 52)]) {
      c.drawCircle(p, 4, _fill(p.dx.round().isEven ? const Color(0xFFD95E58) : const Color(0xFF7FAE62)));
    }
  }

  void _nuts(Canvas c, Color color, {required bool almond}) {
    _plate(c);
    for (final p in const <Offset>[Offset(39, 50), Offset(50, 43), Offset(61, 51), Offset(46, 61), Offset(58, 61)]) {
      c.drawOval(Rect.fromCenter(center: p, width: almond ? 10 : 12, height: almond ? 18 : 14), _fill(color));
    }
  }

  void _spread(Canvas c) {
    _plate(c);
    c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(35, 35, 31, 38), const Radius.circular(8)), _fill(const Color(0xFFD4B388)));
    c.drawRect(const Rect.fromLTWH(38, 42, 25, 24), _fill(const Color(0xFFB97842)));
    c.drawLine(const Offset(38, 40), const Offset(63, 40), _stroke(const Color(0xFF8A6245), 2));
  }

  void _peanuts(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(41, 52), Offset(57, 47), Offset(54, 61)]) {
      final r = Rect.fromCenter(center: p, width: 14, height: 27);
      c.drawRRect(RRect.fromRectAndRadius(r, const Radius.circular(8)), _fill(const Color(0xFFC99A60)));
      c.drawArc(r.deflate(3), .4, 2.2, false, _stroke(const Color(0xFF9A714B), 1));
    }
  }

  void _seeds(Canvas c) {
    _plate(c);
    for (var row = 0; row < 4; row++) {
      for (var col = 0; col < 6; col++) {
        final p = Offset(35 + col * 6.0, 42 + row * 7.0);
        c.drawOval(Rect.fromCenter(center: p, width: 3.2, height: 5), _fill((row + col).isEven ? const Color(0xFF4E4A46) : const Color(0xFF8C8278)));
      }
    }
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch10 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
