import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch9Ids = <String>{
  'lettuce',
  'vegetables',
  'mint',
  'turnip',
  'onion',
  'sweet_potato',
  'parsley',
  'bell_pepper',
  'salad',
  'spinach',
  'apricot',
  'dried_apricots',
  'pineapple',
  'avocado',
  'cherry',
  'lemon',
  'clementine',
  'khalas_dates',
  'medjool_dates',
  'sukkari_dates',
  'fig',
  'dried_figs',
  'strawberry',
  'raspberry',
};

bool hasCodeFoodPictogramBatch9(String foodId) =>
    codeFoodPictogramBatch9Ids.contains(foodId);

class FoodPictogramPainterBatch9 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch9(this.foodId);

  static const _teal = Color(0xFF1F9E7A);
  static const _leaf = Color(0xFF6E9F63);
  static const _leafDark = Color(0xFF4E7D56);

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

  @override
  void paint(Canvas canvas, Size size) {
    final side = math.min(size.width, size.height);
    canvas.save();
    canvas.translate((size.width - side) / 2, (size.height - side) / 2);
    canvas.scale(side / 100, side / 100);

    switch (foodId) {
      case 'lettuce':
        _leafHead(canvas, const Color(0xFF93BF72));
        break;
      case 'vegetables':
        _vegetables(canvas);
        break;
      case 'mint':
        _herb(canvas, rounded: true);
        break;
      case 'turnip':
        _root(canvas, const Color(0xFFF0E7DC), const Color(0xFFB78BB0));
        break;
      case 'onion':
        _onion(canvas);
        break;
      case 'sweet_potato':
        _tuber(canvas);
        break;
      case 'parsley':
        _herb(canvas, rounded: false);
        break;
      case 'bell_pepper':
        _pepper(canvas);
        break;
      case 'salad':
        _salad(canvas);
        break;
      case 'spinach':
        _spinach(canvas);
        break;
      case 'apricot':
        _stoneFruit(canvas, const Color(0xFFF4A14A), split: false);
        break;
      case 'dried_apricots':
        _driedFruit(canvas, const Color(0xFFD88438));
        break;
      case 'pineapple':
        _pineapple(canvas);
        break;
      case 'avocado':
        _avocado(canvas);
        break;
      case 'cherry':
        _cherry(canvas);
        break;
      case 'lemon':
        _citrus(canvas, const Color(0xFFF1D34B));
        break;
      case 'clementine':
        _citrus(canvas, const Color(0xFFE98D2D));
        break;
      case 'khalas_dates':
        _dates(canvas, const Color(0xFF9C6139));
        break;
      case 'medjool_dates':
        _dates(canvas, const Color(0xFF6E432D));
        break;
      case 'sukkari_dates':
        _dates(canvas, const Color(0xFFC69046));
        break;
      case 'fig':
        _fig(canvas, dried: false);
        break;
      case 'dried_figs':
        _fig(canvas, dried: true);
        break;
      case 'strawberry':
        _strawberry(canvas);
        break;
      case 'raspberry':
        _raspberry(canvas);
        break;
      default:
        break;
    }

    canvas.restore();
  }

  void _leafHead(Canvas c, Color base) {
    _plate(c);
    c.drawCircle(const Offset(50, 52), 22, _gradient(const Rect.fromLTWH(28, 30, 44, 44), const Color(0xFFC7DFA8), base));
    for (final a in const <double>[-2.4, -1.4, -.4, .6, 1.6]) {
      c.drawArc(const Rect.fromLTWH(33, 35, 34, 33), a, 1.2, false, _stroke(const Color(0xFFE6F0D6), 1.5));
    }
  }

  void _vegetables(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(38, 54), 10, _fill(const Color(0xFFE68C36)));
    c.drawOval(const Rect.fromLTWH(47, 39, 12, 28), _fill(const Color(0xFF79A95D)));
    c.drawCircle(const Offset(65, 52), 9, _fill(const Color(0xFFB85B4A)));
    c.drawLine(const Offset(38, 44), const Offset(35, 36), _stroke(_leafDark, 2));
    c.drawLine(const Offset(53, 40), const Offset(57, 32), _stroke(_leafDark, 2));
  }

  void _herb(Canvas c, {required bool rounded}) {
    _plate(c);
    c.drawLine(const Offset(50, 70), const Offset(50, 34), _stroke(_leafDark, 2));
    for (var i = 0; i < 6; i++) {
      final y = 61.0 - i * 5.0;
      final dx = i.isEven ? -8.0 : 8.0;
      final rect = Rect.fromCenter(center: Offset(50 + dx, y), width: rounded ? 14 : 11, height: rounded ? 9 : 13);
      c.drawOval(rect, _fill(i.isEven ? _leaf : _leafDark));
    }
  }

  void _root(Canvas c, Color body, Color crown) {
    _plate(c);
    final bulb = Rect.fromCenter(center: const Offset(50, 54), width: 30, height: 31);
    c.drawOval(bulb, _gradient(bulb, const Color(0xFFFFFBF2), body));
    c.drawOval(const Rect.fromLTWH(39, 34, 22, 12), _fill(crown));
    c.drawLine(const Offset(50, 68), const Offset(48, 75), _stroke(body, 2));
    c.drawLine(const Offset(46, 34), const Offset(39, 25), _stroke(_leafDark, 3));
    c.drawLine(const Offset(54, 34), const Offset(61, 25), _stroke(_leaf, 3));
  }

  void _onion(Canvas c) {
    _plate(c);
    final body = Path()
      ..moveTo(50, 32)
      ..quadraticBezierTo(29, 45, 37, 64)
      ..quadraticBezierTo(50, 76, 63, 64)
      ..quadraticBezierTo(71, 45, 50, 32)
      ..close();
    c.drawPath(body, _gradient(const Rect.fromLTWH(35, 32, 30, 42), const Color(0xFFF1DFC5), const Color(0xFFD8B58F)));
    c.drawLine(const Offset(50, 32), const Offset(50, 24), _stroke(const Color(0xFFB9996D), 2));
  }

  void _tuber(Canvas c) {
    _plate(c);
    c.save();
    c.translate(50, 52);
    c.rotate(-.18);
    c.translate(-50, -52);
    final rect = const Rect.fromLTWH(31, 39, 40, 28);
    c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(14)), _gradient(rect, const Color(0xFFD99059), const Color(0xFFA95E47)));
    c.drawCircle(const Offset(43, 50), 1.5, _fill(const Color(0xFF81513F)));
    c.drawCircle(const Offset(59, 58), 1.5, _fill(const Color(0xFF81513F)));
    c.restore();
  }

  void _pepper(Canvas c) {
    _plate(c);
    final rect = const Rect.fromLTWH(34, 36, 34, 36);
    c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(14)), _gradient(rect, const Color(0xFFE86D58), const Color(0xFFB73D35)));
    c.drawLine(const Offset(51, 37), const Offset(53, 28), _stroke(_leafDark, 4));
    c.drawArc(const Rect.fromLTWH(39, 40, 24, 25), .3, 2.5, false, _stroke(const Color(0xFFF08C74), 1.5));
  }

  void _salad(Canvas c) {
    _shadow(c, const Rect.fromLTWH(18, 77, 64, 7));
    c.drawOval(const Rect.fromLTWH(19, 45, 62, 34), _fill(const Color(0xFFE4ECE9)));
    c.drawOval(const Rect.fromLTWH(24, 37, 52, 25), _fill(const Color(0xFF86B96B)));
    for (final p in const <Offset>[Offset(37, 47), Offset(48, 44), Offset(59, 50), Offset(66, 43)]) {
      c.drawCircle(p, 4, _fill(p.dx.round().isEven ? const Color(0xFFD95B4D) : const Color(0xFFF0D168)));
    }
    c.drawArc(const Rect.fromLTWH(23, 36, 54, 27), 0, math.pi, false, _stroke(_teal, 1.5));
  }

  void _spinach(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(38, 53), Offset(50, 44), Offset(61, 53), Offset(49, 59)]) {
      final leaf = Path()
        ..moveTo(p.dx, p.dy + 10)
        ..quadraticBezierTo(p.dx - 10, p.dy, p.dx, p.dy - 11)
        ..quadraticBezierTo(p.dx + 10, p.dy, p.dx, p.dy + 10)
        ..close();
      c.drawPath(leaf, _fill(p.dx.round().isEven ? _leaf : _leafDark));
    }
  }

  void _stoneFruit(Canvas c, Color color, {required bool split}) {
    _plate(c);
    final rect = const Rect.fromLTWH(34, 36, 34, 34);
    c.drawOval(rect, _gradient(rect, const Color(0xFFFFC06E), color));
    c.drawArc(rect.deflate(5), -.8, 1.7, false, _stroke(const Color(0xFFE68236), 1.4));
    if (split) c.drawCircle(const Offset(51, 53), 6, _fill(const Color(0xFF9A653E)));
    c.drawOval(const Rect.fromLTWH(56, 29, 14, 7), _fill(_leaf));
  }

  void _driedFruit(Canvas c, Color color) {
    _plate(c);
    for (final p in const <Offset>[Offset(39, 52), Offset(52, 45), Offset(63, 55), Offset(49, 61)]) {
      final r = Rect.fromCenter(center: p, width: 17, height: 12);
      c.drawOval(r, _gradient(r, color.withValues(alpha: .75), color));
      c.drawArc(r.deflate(3), .2, 2.2, false, _stroke(const Color(0xFFB66B35), 1));
    }
  }

  void _pineapple(Canvas c) {
    _plate(c);
    final body = const Rect.fromLTWH(37, 38, 28, 34);
    c.drawOval(body, _gradient(body, const Color(0xFFEBCB58), const Color(0xFFC89436)));
    for (var i = 0; i < 4; i++) {
      c.drawLine(Offset(39 + i * 7.0, 42), Offset(34 + i * 7.0, 66), _stroke(const Color(0xFFB27F31), 1));
      c.drawLine(Offset(62 - i * 7.0, 42), Offset(67 - i * 7.0, 66), _stroke(const Color(0xFFB27F31), 1));
    }
    for (final dx in const <double>[-8, 0, 8]) {
      c.drawLine(Offset(51, 39), Offset(51 + dx, 26), _stroke(_leafDark, 3));
    }
  }

  void _avocado(Canvas c) {
    _plate(c);
    final fruit = Path()
      ..moveTo(50, 29)
      ..quadraticBezierTo(31, 47, 36, 64)
      ..quadraticBezierTo(50, 76, 64, 64)
      ..quadraticBezierTo(69, 47, 50, 29)
      ..close();
    c.drawPath(fruit, _fill(const Color(0xFF5F8C49)));
    final inner = Path()
      ..moveTo(50, 36)
      ..quadraticBezierTo(38, 49, 41, 61)
      ..quadraticBezierTo(50, 69, 59, 61)
      ..quadraticBezierTo(62, 49, 50, 36)
      ..close();
    c.drawPath(inner, _fill(const Color(0xFFC7D86B)));
    c.drawCircle(const Offset(50, 57), 7, _fill(const Color(0xFF9B6339)));
  }

  void _cherry(Canvas c) {
    _plate(c);
    c.drawCircle(const Offset(42, 58), 9, _fill(const Color(0xFFB93843)));
    c.drawCircle(const Offset(59, 57), 9, _fill(const Color(0xFFD24D51)));
    c.drawArc(const Rect.fromLTWH(41, 29, 23, 28), 2.8, 1.9, false, _stroke(_leafDark, 2));
    c.drawArc(const Rect.fromLTWH(35, 30, 22, 29), 3.3, 1.6, false, _stroke(_leafDark, 2));
  }

  void _citrus(Canvas c, Color color) {
    _plate(c);
    final fruit = const Rect.fromLTWH(34, 35, 34, 34);
    c.drawOval(fruit, _gradient(fruit, color.withValues(alpha: .8), color));
    c.drawCircle(const Offset(51, 52), 11, _stroke(const Color(0xFFFFEAA0), 1.5));
    for (var i = 0; i < 6; i++) {
      final a = i * math.pi / 3;
      c.drawLine(const Offset(51, 52), Offset(51 + math.cos(a) * 10, 52 + math.sin(a) * 10), _stroke(const Color(0xFFFFEAA0), .9));
    }
    c.drawOval(const Rect.fromLTWH(58, 29, 13, 7), _fill(_leaf));
  }

  void _dates(Canvas c, Color color) {
    _plate(c);
    for (final p in const <Offset>[Offset(39, 52), Offset(49, 44), Offset(60, 51), Offset(48, 61), Offset(62, 61)]) {
      final rect = Rect.fromCenter(center: p, width: 13, height: 19);
      c.drawOval(rect, _gradient(rect, color.withValues(alpha: .72), color));
      c.drawLine(Offset(p.dx - 2, p.dy - 5), Offset(p.dx + 2, p.dy + 5), _stroke(const Color(0xFFE0B789).withValues(alpha: .45), .9));
    }
  }

  void _fig(Canvas c, {required bool dried}) {
    _plate(c);
    final body = Path()
      ..moveTo(50, 31)
      ..quadraticBezierTo(31, 46, 37, 64)
      ..quadraticBezierTo(50, 76, 63, 64)
      ..quadraticBezierTo(69, 46, 50, 31)
      ..close();
    c.drawPath(body, _gradient(const Rect.fromLTWH(35, 31, 30, 42), dried ? const Color(0xFF8B625D) : const Color(0xFF8B5A87), dried ? const Color(0xFF6A4743) : const Color(0xFF5A3C69)));
    c.drawOval(const Rect.fromLTWH(42, 45, 17, 20), _fill(const Color(0xFFD69A8C)));
    for (final p in const <Offset>[Offset(46, 51), Offset(52, 54), Offset(49, 60), Offset(55, 59)]) {
      c.drawCircle(p, 1.1, _fill(const Color(0xFFF2D5A8)));
    }
  }

  void _strawberry(Canvas c) {
    _plate(c);
    final body = Path()
      ..moveTo(35, 42)
      ..quadraticBezierTo(50, 31, 66, 42)
      ..quadraticBezierTo(63, 65, 50, 72)
      ..quadraticBezierTo(37, 65, 35, 42)
      ..close();
    c.drawPath(body, _gradient(const Rect.fromLTWH(35, 36, 31, 36), const Color(0xFFE96A5A), const Color(0xFFB93642)));
    for (final p in const <Offset>[Offset(43, 48), Offset(52, 45), Offset(59, 51), Offset(47, 59), Offset(56, 61)]) {
      c.drawCircle(p, 1.2, _fill(const Color(0xFFFFD678)));
    }
    c.drawArc(const Rect.fromLTWH(39, 30, 24, 17), .2, 2.7, false, _stroke(_leafDark, 3));
  }

  void _raspberry(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(43, 45), Offset(51, 42), Offset(59, 46), Offset(39, 53), Offset(47, 52), Offset(55, 53), Offset(63, 54), Offset(44, 61), Offset(53, 62), Offset(60, 61)]) {
      c.drawCircle(p, 5, _fill(const Color(0xFFC83F62)));
    }
    c.drawArc(const Rect.fromLTWH(40, 29, 22, 15), .4, 2.4, false, _stroke(_leafDark, 3));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch9 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
