import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch6Ids = <String>{
  'shawarma_beef',
  'shuwa',
  'tabbouleh',
  'lamb',
  'chicken_breast',
  'minced_beef',
  'lamb_chops',
  'turkey',
  'liver',
  'kefta',
  'merguez',
  'roast_chicken',
  'sausage',
  'beef_steak',
  'veal',
  'sea_bass',
  'squid',
  'crab',
  'shrimp',
  'sea_bream',
  'prawns',
  'mackerel',
  'hake',
  'mussels',
};

bool hasCodeFoodPictogramBatch6(String foodId) =>
    codeFoodPictogramBatch6Ids.contains(foodId);

class FoodPictogramPainterBatch6 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch6(this.foodId);

  static const _teal = Color(0xFF1F9E7A);
  static const _brown = Color(0xFF8A5034);
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
    c.drawOval(const Rect.fromLTWH(15, 48, 70, 31), _fill(const Color(0xFFDCE8E4)));
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
      case 'shawarma_beef':
        _shawarma(canvas);
        break;
      case 'shuwa':
        _roast(canvas, const Color(0xFF8B4F32), bone: true);
        break;
      case 'tabbouleh':
        _tabbouleh(canvas);
        break;
      case 'lamb':
        _meatCut(canvas, const Color(0xFFB86F55), bone: true);
        break;
      case 'chicken_breast':
        _poultryCut(canvas, const Color(0xFFD99A62));
        break;
      case 'minced_beef':
        _minced(canvas);
        break;
      case 'lamb_chops':
        _chops(canvas);
        break;
      case 'turkey':
        _poultryCut(canvas, const Color(0xFFC77B4E), leg: true);
        break;
      case 'liver':
        _liver(canvas);
        break;
      case 'kefta':
        _kefta(canvas);
        break;
      case 'merguez':
        _sausages(canvas, const Color(0xFFB84435), curved: true);
        break;
      case 'roast_chicken':
        _roastChicken(canvas);
        break;
      case 'sausage':
        _sausages(canvas, const Color(0xFFC9784D), curved: false);
        break;
      case 'beef_steak':
        _steak(canvas);
        break;
      case 'veal':
        _meatCut(canvas, const Color(0xFFC88873), bone: false);
        break;
      case 'sea_bass':
        _fish(canvas, const Color(0xFF9FB4AE), stripe: true);
        break;
      case 'squid':
        _squid(canvas);
        break;
      case 'crab':
        _crab(canvas);
        break;
      case 'shrimp':
        _shrimp(canvas, large: false);
        break;
      case 'sea_bream':
        _fish(canvas, const Color(0xFFD0B875), stripe: false);
        break;
      case 'prawns':
        _shrimp(canvas, large: true);
        break;
      case 'mackerel':
        _fish(canvas, const Color(0xFF7A9E9A), stripe: true, darkBack: true);
        break;
      case 'hake':
        _fish(canvas, const Color(0xFFB7C1BE), stripe: false, slim: true);
        break;
      case 'mussels':
        _mussels(canvas);
        break;
      default:
        break;
    }
    canvas.restore();
  }

  void _shawarma(Canvas c) {
    _plate(c);
    final wrap = Path()
      ..moveTo(31, 64)
      ..lineTo(40, 30)
      ..quadraticBezierTo(55, 24, 69, 38)
      ..lineTo(61, 70)
      ..close();
    c.drawPath(wrap, _gradient(const Rect.fromLTWH(31, 28, 38, 42), const Color(0xFFEBC77F), const Color(0xFFB9773D)));
    c.drawPath(wrap, _stroke(_brown, 1.2));
    for (final y in const <double>[39, 46, 53]) {
      c.drawLine(Offset(43, y), Offset(61, y + 4), _stroke(const Color(0xFF7A4632), 3));
    }
    c.drawLine(const Offset(45, 34), const Offset(60, 38), _stroke(_teal, 2));
  }

  void _roast(Canvas c, Color color, {required bool bone}) {
    _plate(c);
    final rect = const Rect.fromLTWH(30, 36, 42, 28);
    c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(12)), _gradient(rect, const Color(0xFFD0915B), color));
    c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(12)), _stroke(const Color(0xFF74402D), 1.2));
    if (bone) {
      c.drawLine(const Offset(66, 44), const Offset(77, 35), _stroke(const Color(0xFFEAD7B0), 4));
      c.drawCircle(const Offset(79, 34), 3, _fill(const Color(0xFFF0DFBE)));
    }
  }

  void _tabbouleh(Canvas c) {
    _bowl(c, const Color(0xFF7DAA62));
    for (final p in const <Offset>[Offset(33, 47), Offset(42, 42), Offset(50, 50), Offset(59, 43), Offset(67, 49), Offset(44, 55)]) {
      c.drawCircle(p, 3.2, _fill(const Color(0xFF5B914F)));
    }
    for (final p in const <Offset>[Offset(39, 48), Offset(56, 46), Offset(62, 53)]) {
      c.drawCircle(p, 2.6, _fill(const Color(0xFFD65C48)));
    }
    c.drawCircle(const Offset(50, 43), 2.4, _fill(const Color(0xFFF2D36B)));
  }

  void _meatCut(Canvas c, Color color, {required bool bone}) {
    _plate(c);
    final path = Path()
      ..moveTo(29, 52)
      ..quadraticBezierTo(35, 35, 51, 34)
      ..quadraticBezierTo(71, 35, 73, 51)
      ..quadraticBezierTo(68, 67, 49, 66)
      ..quadraticBezierTo(33, 65, 29, 52)
      ..close();
    c.drawPath(path, _gradient(const Rect.fromLTWH(29, 34, 44, 33), const Color(0xFFE2A187), color));
    c.drawPath(path, _stroke(const Color(0xFF894B3B), 1.1));
    if (bone) {
      c.drawCircle(const Offset(55, 49), 7, _fill(const Color(0xFFF1DEC0)));
      c.drawCircle(const Offset(55, 49), 3.5, _fill(const Color(0xFFD7B28B)));
    }
  }

  void _poultryCut(Canvas c, Color color, {bool leg = false}) {
    _plate(c);
    if (leg) {
      final rect = const Rect.fromLTWH(30, 35, 35, 28);
      c.drawOval(rect, _gradient(rect, const Color(0xFFE3AA72), color));
      c.drawLine(const Offset(61, 50), const Offset(77, 62), _stroke(const Color(0xFFF0DDBA), 4));
      c.drawCircle(const Offset(78, 63), 3, _fill(const Color(0xFFF0DDBA)));
    } else {
      final path = Path()
        ..moveTo(31, 61)
        ..quadraticBezierTo(35, 35, 55, 32)
        ..quadraticBezierTo(72, 41, 67, 62)
        ..quadraticBezierTo(49, 70, 31, 61)
        ..close();
      c.drawPath(path, _gradient(const Rect.fromLTWH(31, 32, 40, 38), const Color(0xFFF0C69A), color));
    }
  }

  void _minced(Canvas c) {
    _plate(c);
    for (var i = 0; i < 18; i++) {
      final x = 32.0 + (i % 6) * 6.5;
      final y = 42.0 + (i ~/ 6) * 8.0;
      c.drawCircle(Offset(x, y), 4.2, _fill(i.isEven ? const Color(0xFFA85D4B) : const Color(0xFFC97862)));
    }
  }

  void _chops(Canvas c) {
    _plate(c);
    for (final dx in const <double>[0, 18]) {
      final rect = Rect.fromLTWH(28 + dx, 40, 25, 23);
      c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(9)), _gradient(rect, const Color(0xFFD69272), const Color(0xFF995442)));
      c.drawLine(Offset(48 + dx, 43), Offset(63 + dx, 30), _stroke(const Color(0xFFE9D4AF), 3.8));
    }
  }

  void _liver(Canvas c) {
    _plate(c);
    final path = Path()
      ..moveTo(27, 55)
      ..quadraticBezierTo(34, 35, 54, 37)
      ..quadraticBezierTo(74, 37, 74, 52)
      ..quadraticBezierTo(64, 67, 43, 65)
      ..quadraticBezierTo(31, 64, 27, 55)
      ..close();
    c.drawPath(path, _gradient(const Rect.fromLTWH(27, 36, 47, 31), const Color(0xFF9D554E), const Color(0xFF653536)));
  }

  void _kefta(Canvas c) {
    _plate(c);
    for (final y in const <double>[43, 54]) {
      c.drawLine(Offset(30, y), Offset(69, y + 7), _stroke(const Color(0xFF8B4E35), 7));
      c.drawLine(Offset(31, y - 1), Offset(68, y + 6), _stroke(const Color(0xFFC37A4E), 3));
    }
  }

  void _sausages(Canvas c, Color color, {required bool curved}) {
    _plate(c);
    for (var i = 0; i < 3; i++) {
      final y = 39.0 + i * 10.0;
      if (curved) {
        c.drawArc(Rect.fromLTWH(29, y - 5, 43, 14), .15, 2.75, false, _stroke(color, 6));
      } else {
        c.drawLine(Offset(31, y), Offset(69, y + 5), _stroke(color, 7));
      }
    }
  }

  void _roastChicken(Canvas c) {
    _plate(c);
    final body = const Rect.fromLTWH(31, 33, 40, 34);
    c.drawOval(body, _gradient(body, const Color(0xFFE6A65D), const Color(0xFF9C552D)));
    c.drawArc(const Rect.fromLTWH(36, 37, 29, 20), .3, 2.4, false, _stroke(const Color(0xFFF3CB88), 2));
    c.drawLine(const Offset(35, 56), const Offset(26, 67), _stroke(const Color(0xFFC47A40), 6));
    c.drawLine(const Offset(67, 55), const Offset(76, 67), _stroke(const Color(0xFFC47A40), 6));
  }

  void _steak(Canvas c) {
    _plate(c);
    final path = Path()
      ..moveTo(27, 54)
      ..quadraticBezierTo(31, 34, 52, 34)
      ..quadraticBezierTo(76, 39, 72, 58)
      ..quadraticBezierTo(59, 68, 39, 65)
      ..quadraticBezierTo(28, 64, 27, 54)
      ..close();
    c.drawPath(path, _gradient(const Rect.fromLTWH(27, 34, 46, 34), const Color(0xFFB5684D), const Color(0xFF774032)));
    c.drawPath(path, _stroke(const Color(0xFF60342B), 1.3));
    for (final x in const <double>[39, 49, 59]) {
      c.drawLine(Offset(x, 41), Offset(x + 7, 59), _stroke(const Color(0xFFD59A70), 1.5));
    }
  }

  void _fish(Canvas c, Color color, {required bool stripe, bool darkBack = false, bool slim = false}) {
    _plate(c);
    final h = slim ? 20.0 : 26.0;
    final bodyRect = Rect.fromLTWH(29, 38, 43, h);
    final path = Path()
      ..moveTo(29, 51)
      ..quadraticBezierTo(44, 32 + (slim ? 6 : 0), 66, 43)
      ..lineTo(80, 34)
      ..lineTo(77, 51)
      ..lineTo(80, 68)
      ..lineTo(66, 59)
      ..quadraticBezierTo(44, 70 - (slim ? 6 : 0), 29, 51)
      ..close();
    c.drawPath(path, _gradient(bodyRect, const Color(0xFFD9E3DE), color));
    if (darkBack) {
      c.drawArc(bodyRect, 3.4, 2.5, false, _stroke(const Color(0xFF4B6C69), 3));
    }
    if (stripe) {
      for (final x in const <double>[44, 51, 58]) {
        c.drawLine(Offset(x, 42), Offset(x - 3, 58), _stroke(const Color(0xFF647D78), 1.2));
      }
    }
    c.drawCircle(const Offset(35, 48), 1.5, _fill(_dark));
  }

  void _squid(Canvas c) {
    _plate(c);
    final body = Path()
      ..moveTo(39, 58)
      ..quadraticBezierTo(32, 38, 50, 27)
      ..quadraticBezierTo(68, 38, 61, 58)
      ..close();
    c.drawPath(body, _gradient(const Rect.fromLTWH(35, 27, 30, 33), const Color(0xFFF2D1C7), const Color(0xFFC98B83)));
    for (var i = 0; i < 5; i++) {
      c.drawArc(Rect.fromLTWH(34 + i * 5.5, 55, 18, 20), .4, 2.2, false, _stroke(const Color(0xFFC98B83), 2.4));
    }
  }

  void _crab(Canvas c) {
    _plate(c);
    c.drawOval(const Rect.fromLTWH(34, 39, 32, 24), _fill(const Color(0xFFD96545)));
    c.drawCircle(const Offset(42, 40), 2.3, _fill(_dark));
    c.drawCircle(const Offset(58, 40), 2.3, _fill(_dark));
    for (final y in const <double>[45, 53, 60]) {
      c.drawLine(Offset(34, y), Offset(22, y - 5), _stroke(const Color(0xFFD96545), 3));
      c.drawLine(Offset(66, y), Offset(78, y - 5), _stroke(const Color(0xFFD96545), 3));
    }
    c.drawArc(const Rect.fromLTWH(17, 31, 17, 18), -.6, 3.5, false, _stroke(const Color(0xFFD96545), 4));
    c.drawArc(const Rect.fromLTWH(66, 31, 17, 18), .2, 3.5, false, _stroke(const Color(0xFFD96545), 4));
  }

  void _shrimp(Canvas c, {required bool large}) {
    _plate(c);
    final rect = large ? const Rect.fromLTWH(27, 31, 50, 42) : const Rect.fromLTWH(31, 35, 42, 34);
    c.drawArc(rect, .2, 4.7, false, _stroke(const Color(0xFFE37762), large ? 7 : 6));
    c.drawCircle(Offset(large ? 69 : 65, large ? 42 : 44), 1.6, _fill(_dark));
    for (var i = 0; i < 4; i++) {
      final x = 41.0 + i * 7.0;
      c.drawLine(Offset(x, 52), Offset(x - 4, 61), _stroke(const Color(0xFFC95F52), 1.3));
    }
  }

  void _mussels(Canvas c) {
    _plate(c);
    const shells = <Offset>[Offset(37, 48), Offset(50, 42), Offset(62, 51), Offset(49, 59)];
    for (final p in shells) {
      final rect = Rect.fromCenter(center: p, width: 18, height: 11);
      c.drawOval(rect, _gradient(rect, const Color(0xFF53666C), const Color(0xFF202E33)));
      c.drawArc(rect, .1, 2.8, false, _stroke(const Color(0xFF82979A), 1));
      c.drawOval(Rect.fromCenter(center: Offset(p.dx + 2, p.dy), width: 8, height: 4), _fill(const Color(0xFFE3A04B)));
    }
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch6 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
