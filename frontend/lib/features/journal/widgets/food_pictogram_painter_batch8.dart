import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch8Ids = <String>{
  'greek_yogurt',
  'fava_beans',
  'white_beans',
  'red_beans',
  'green_peas',
  'split_peas',
  'soybeans',
  'garlic',
  'artichoke',
  'eggplant',
  'beetroot',
  'broccoli',
  'carrot',
  'mushroom',
  'cabbage',
  'cauliflower',
  'preserved_lemon',
  'cucumber',
  'coriander',
  'pumpkin',
  'zucchini',
  'celery',
  'okra',
  'green_beans',
};

bool hasCodeFoodPictogramBatch8(String foodId) =>
    codeFoodPictogramBatch8Ids.contains(foodId);

class FoodPictogramPainterBatch8 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch8(this.foodId);

  static const _teal = Color(0xFF1F9E7A);
  static const _dark = Color(0xFF394743);
  static const _leaf = Color(0xFF6F9E66);
  static const _leafDark = Color(0xFF4F7D59);

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
    c.drawShadow(
      Path()..addOval(rect),
      Colors.black.withValues(alpha: .14),
      4,
      false,
    );
  }

  void _plate(Canvas c) {
    _shadow(c, const Rect.fromLTWH(16, 77, 68, 7));
    c.drawOval(
      const Rect.fromLTWH(15, 48, 70, 31),
      _fill(const Color(0xFFDDE8E4)),
    );
    c.drawOval(
      const Rect.fromLTWH(20, 44, 60, 30),
      _fill(const Color(0xFFFAFCFB)),
    );
  }

  void _bowl(Canvas c, Color inside) {
    _shadow(c, const Rect.fromLTWH(19, 77, 62, 7));
    c.drawOval(
      const Rect.fromLTWH(19, 45, 62, 34),
      _fill(const Color(0xFFE4ECE9)),
    );
    c.drawOval(const Rect.fromLTWH(24, 37, 52, 25), _fill(inside));
    c.drawArc(
      const Rect.fromLTWH(23, 36, 54, 27),
      0,
      math.pi,
      false,
      _stroke(_teal, 1.5),
    );
  }

  @override
  void paint(Canvas canvas, Size size) {
    final side = math.min(size.width, size.height);
    canvas.save();
    canvas.translate((size.width - side) / 2, (size.height - side) / 2);
    canvas.scale(side / 100, side / 100);

    switch (foodId) {
      case 'greek_yogurt':
        _greekYogurt(canvas);
        break;
      case 'fava_beans':
        _beans(canvas, const Color(0xFF8AAE67), long: true);
        break;
      case 'white_beans':
        _beans(canvas, const Color(0xFFF2E7C8));
        break;
      case 'red_beans':
        _beans(canvas, const Color(0xFF9D4F48));
        break;
      case 'green_peas':
        _peas(canvas, const Color(0xFF7FAE55));
        break;
      case 'split_peas':
        _splitPeas(canvas);
        break;
      case 'soybeans':
        _beans(canvas, const Color(0xFFD8C976));
        break;
      case 'garlic':
        _garlic(canvas);
        break;
      case 'artichoke':
        _artichoke(canvas);
        break;
      case 'eggplant':
        _eggplant(canvas);
        break;
      case 'beetroot':
        _root(canvas, const Color(0xFF9C3F66), beet: true);
        break;
      case 'broccoli':
        _broccoli(canvas, cauliflower: false);
        break;
      case 'carrot':
        _carrot(canvas);
        break;
      case 'mushroom':
        _mushroom(canvas);
        break;
      case 'cabbage':
        _cabbage(canvas);
        break;
      case 'cauliflower':
        _broccoli(canvas, cauliflower: true);
        break;
      case 'preserved_lemon':
        _lemon(canvas);
        break;
      case 'cucumber':
        _cucumber(canvas, zucchini: false);
        break;
      case 'coriander':
        _herb(canvas, dense: true);
        break;
      case 'pumpkin':
        _pumpkin(canvas);
        break;
      case 'zucchini':
        _cucumber(canvas, zucchini: true);
        break;
      case 'celery':
        _celery(canvas);
        break;
      case 'okra':
        _okra(canvas);
        break;
      case 'green_beans':
        _greenBeans(canvas);
        break;
      default:
        break;
    }

    canvas.restore();
  }

  void _greekYogurt(Canvas c) {
    _bowl(c, const Color(0xFFF8F5EA));
    c.drawOval(
      const Rect.fromLTWH(32, 40, 36, 18),
      _fill(const Color(0xFFF9F7EF)),
    );
    c.drawArc(
      const Rect.fromLTWH(38, 42, 24, 12),
      .15,
      2.8,
      false,
      _stroke(const Color(0xFFD8D3C6), 2.2),
    );
    c.drawCircle(const Offset(57, 47), 2.4, _fill(_teal));
  }

  void _beans(Canvas c, Color color, {bool long = false}) {
    _bowl(c, const Color(0xFFE8D7B5));
    const points = <Offset>[
      Offset(36, 47),
      Offset(45, 43),
      Offset(55, 48),
      Offset(64, 43),
      Offset(43, 54),
      Offset(58, 55),
    ];
    for (final p in points) {
      final rect = Rect.fromCenter(
        center: p,
        width: long ? 12 : 10,
        height: long ? 6 : 8,
      );
      c.drawOval(rect, _gradient(rect, color.withValues(alpha: .75), color));
      c.drawArc(rect.deflate(2), .3, 2.1, false, _stroke(_dark.withValues(alpha: .35), .9));
    }
  }

  void _peas(Canvas c, Color color) {
    _plate(c);
    final pod = Path()
      ..moveTo(27, 54)
      ..quadraticBezierTo(49, 32, 75, 45)
      ..quadraticBezierTo(60, 65, 30, 63)
      ..close();
    c.drawPath(pod, _gradient(const Rect.fromLTWH(27, 35, 48, 30), const Color(0xFFA9C975), color));
    for (final x in const <double>[38, 48, 58, 67]) {
      c.drawCircle(Offset(x, 50), 4, _fill(const Color(0xFFD8E9A8)));
    }
  }

  void _splitPeas(Canvas c) {
    _bowl(c, const Color(0xFFD6C96E));
    for (var row = 0; row < 2; row++) {
      for (var col = 0; col < 5; col++) {
        c.drawCircle(
          Offset(35 + col * 7.5, 44 + row * 8.0),
          3.2,
          _fill(row.isEven ? const Color(0xFFE5D77F) : const Color(0xFFC6B85F)),
        );
      }
    }
  }

  void _garlic(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(44, 53), Offset(52, 48), Offset(60, 54)]) {
      c.drawOval(
        Rect.fromCenter(center: p, width: 15, height: 22),
        _gradient(
          Rect.fromCenter(center: p, width: 15, height: 22),
          const Color(0xFFFFF9E9),
          const Color(0xFFE7D9BC),
        ),
      );
    }
    c.drawLine(const Offset(52, 38), const Offset(53, 29), _stroke(_leafDark, 2));
  }

  void _artichoke(Canvas c) {
    _plate(c);
    for (var row = 0; row < 4; row++) {
      final y = 61.0 - row * 8;
      final count = 5 - row;
      for (var i = 0; i < count; i++) {
        final x = 50 - (count - 1) * 6 / 2 + i * 6;
        final leaf = Path()
          ..moveTo(x, y + 6)
          ..quadraticBezierTo(x - 6, y, x, y - 8)
          ..quadraticBezierTo(x + 6, y, x, y + 6)
          ..close();
        c.drawPath(leaf, _fill(row.isEven ? _leaf : _leafDark));
      }
    }
    c.drawLine(const Offset(50, 63), const Offset(50, 72), _stroke(_leafDark, 4));
  }

  void _eggplant(Canvas c) {
    _plate(c);
    c.save();
    c.translate(50, 52);
    c.rotate(-.35);
    c.translate(-50, -52);
    final body = const Rect.fromLTWH(35, 34, 31, 42);
    c.drawOval(body, _gradient(body, const Color(0xFF8D6AA9), const Color(0xFF563D78)));
    final crown = Path()
      ..moveTo(42, 37)
      ..lineTo(50, 28)
      ..lineTo(56, 37)
      ..lineTo(64, 32)
      ..lineTo(60, 43)
      ..close();
    c.drawPath(crown, _fill(_leafDark));
    c.restore();
  }

  void _root(Canvas c, Color color, {required bool beet}) {
    _plate(c);
    final bulb = Rect.fromCenter(center: const Offset(50, 53), width: 31, height: 32);
    c.drawOval(bulb, _gradient(bulb, color.withValues(alpha: .75), color));
    c.drawLine(const Offset(50, 67), const Offset(48, 74), _stroke(color, 2));
    if (beet) {
      c.drawArc(const Rect.fromLTWH(35, 25, 24, 24), 3.2, 1.6, false, _stroke(_leafDark, 4));
      c.drawArc(const Rect.fromLTWH(47, 24, 25, 24), 4.2, 1.4, false, _stroke(_leaf, 4));
    }
  }

  void _broccoli(Canvas c, {required bool cauliflower}) {
    _plate(c);
    c.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(46, 50, 9, 24), const Radius.circular(4)),
      _fill(const Color(0xFF7FA768)),
    );
    final colors = cauliflower
        ? const <Color>[Color(0xFFF0EAD4), Color(0xFFE6DFC4)]
        : const <Color>[Color(0xFF6FA35B), Color(0xFF4E814C)];
    for (final p in const <Offset>[Offset(38, 45), Offset(49, 38), Offset(61, 44), Offset(50, 49)]) {
      c.drawCircle(p, 10, _fill(colors[(p.dx.round() + p.dy.round()) % 2]));
    }
    if (cauliflower) {
      c.drawArc(const Rect.fromLTWH(31, 48, 38, 24), .1, 2.8, false, _stroke(_leaf, 3));
    }
  }

  void _carrot(Canvas c) {
    _plate(c);
    final carrot = Path()
      ..moveTo(38, 39)
      ..quadraticBezierTo(54, 38, 61, 44)
      ..lineTo(48, 73)
      ..close();
    c.drawPath(carrot, _gradient(const Rect.fromLTWH(38, 38, 23, 35), const Color(0xFFF6A23A), const Color(0xFFE36E2B)));
    for (final dx in const <double>[43, 50, 57]) {
      c.drawLine(Offset(dx, 39), Offset(dx - 7, 28), _stroke(_leafDark, 3));
    }
  }

  void _mushroom(Canvas c) {
    _plate(c);
    c.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(45, 49, 12, 23), const Radius.circular(5)),
      _fill(const Color(0xFFE8D9C0)),
    );
    final cap = const Rect.fromLTWH(31, 32, 40, 27);
    c.drawArc(cap, math.pi, math.pi, true, _gradient(cap, const Color(0xFFD9B792), const Color(0xFF9F765D)));
    c.drawCircle(const Offset(42, 44), 2, _fill(const Color(0xFFF4EBDD)));
    c.drawCircle(const Offset(57, 40), 2, _fill(const Color(0xFFF4EBDD)));
  }

  void _cabbage(Canvas c) {
    _plate(c);
    final base = const Offset(50, 51);
    c.drawCircle(base, 22, _gradient(const Rect.fromLTWH(28, 29, 44, 44), const Color(0xFFB7D594), const Color(0xFF719F67)));
    for (final angle in const <double>[-1.7, -.8, 0, .8, 1.7]) {
      c.drawArc(const Rect.fromLTWH(34, 36, 32, 30), angle, 1.4, false, _stroke(const Color(0xFFE0EDC9), 1.5));
    }
  }

  void _lemon(Canvas c) {
    _plate(c);
    final lemon = const Rect.fromLTWH(33, 35, 36, 32);
    c.drawOval(lemon, _gradient(lemon, const Color(0xFFFFE868), const Color(0xFFD9B62E)));
    c.drawCircle(const Offset(51, 51), 11, _stroke(const Color(0xFFF8F2B9), 2));
    for (var i = 0; i < 6; i++) {
      final a = i * math.pi / 3;
      c.drawLine(const Offset(51, 51), Offset(51 + math.cos(a) * 10, 51 + math.sin(a) * 10), _stroke(const Color(0xFFF8F2B9), 1));
    }
    c.drawOval(const Rect.fromLTWH(59, 29, 14, 7), _fill(_leaf));
  }

  void _cucumber(Canvas c, {required bool zucchini}) {
    _plate(c);
    c.save();
    c.translate(50, 52);
    c.rotate(-.22);
    c.translate(-50, -52);
    final body = const Rect.fromLTWH(27, 42, 48, 19);
    c.drawRRect(
      RRect.fromRectAndRadius(body, const Radius.circular(10)),
      _gradient(
        body,
        zucchini ? const Color(0xFF78A45E) : const Color(0xFF9EC77A),
        zucchini ? const Color(0xFF3F7E49) : const Color(0xFF5F9B58),
      ),
    );
    for (final x in const <double>[39, 52, 65]) {
      c.drawCircle(Offset(x, 51), 1.2, _fill(const Color(0xFFD9E8B8).withValues(alpha: .65)));
    }
    c.restore();
  }

  void _herb(Canvas c, {required bool dense}) {
    _plate(c);
    c.drawLine(const Offset(50, 70), const Offset(50, 36), _stroke(_leafDark, 2));
    for (var i = 0; i < (dense ? 7 : 5); i++) {
      final y = 61.0 - i * 5;
      final dx = i.isEven ? -8.0 : 8.0;
      c.drawOval(Rect.fromCenter(center: Offset(50 + dx, y), width: 14, height: 8), _fill(i.isEven ? _leaf : _leafDark));
    }
  }

  void _pumpkin(Canvas c) {
    _plate(c);
    final rect = const Rect.fromLTWH(27, 36, 47, 36);
    c.drawOval(rect, _gradient(rect, const Color(0xFFF3A33C), const Color(0xFFD66D2A)));
    for (final x in const <double>[38, 50, 62]) {
      c.drawArc(Rect.fromCenter(center: Offset(x, 54), width: 18, height: 34), 1.5, 3.2, false, _stroke(const Color(0xFFC76228), 1.4));
    }
    c.drawLine(const Offset(51, 37), const Offset(55, 28), _stroke(_leafDark, 4));
  }

  void _celery(Canvas c) {
    _plate(c);
    for (final x in const <double>[42, 48, 54, 60]) {
      c.drawLine(Offset(x, 70), Offset(x - 4, 37), _stroke(const Color(0xFF9EC57D), 4));
      c.drawOval(Rect.fromCenter(center: Offset(x - 7, 35), width: 14, height: 9), _fill(_leaf));
    }
  }

  void _okra(Canvas c) {
    _plate(c);
    c.save();
    c.translate(50, 52);
    c.rotate(-.25);
    c.translate(-50, -52);
    final pod = Path()
      ..moveTo(31, 56)
      ..lineTo(67, 40)
      ..quadraticBezierTo(76, 43, 70, 51)
      ..lineTo(36, 66)
      ..close();
    c.drawPath(pod, _gradient(const Rect.fromLTWH(31, 40, 45, 26), const Color(0xFF8BB46C), const Color(0xFF557E48)));
    c.drawLine(const Offset(70, 44), const Offset(78, 39), _stroke(_leafDark, 2));
    c.restore();
  }

  void _greenBeans(Canvas c) {
    _plate(c);
    for (var i = 0; i < 4; i++) {
      final y = 43.0 + i * 7;
      c.drawArc(
        Rect.fromLTWH(29 + i * 2, y, 45, 15),
        3.4,
        2.3,
        false,
        _stroke(i.isEven ? const Color(0xFF6EA45D) : const Color(0xFF4F844F), 3.2),
      );
    }
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch8 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
