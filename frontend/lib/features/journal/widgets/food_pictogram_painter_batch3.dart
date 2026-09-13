import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch3Ids = <String>{
  'baguette',
  'batbout',
  'bulgur',
  'chebab',
  'couscous',
  'crepe',
  'cereal',
  'oats',
  'waffle',
  'granola',
  'harcha',
  'krachel',
  'corn',
  'muesli',
  'barley',
  'white_bread',
  'toast_bread',
  'khameer_bread',
  'pita_bread',
  'regag_bread',
  'pancake',
  'porridge',
  'pasta',
  'quinoa',
};

bool hasCodeFoodPictogramBatch3(String foodId) =>
    codeFoodPictogramBatch3Ids.contains(foodId);

class FoodPictogramPainterBatch3 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch3(this.foodId);

  static const _teal = Color(0xFF1F9E7A);
  static const _cream = Color(0xFFFFF7E5);

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

  Paint _gradient(Rect rect, Color light, Color dark) => Paint()
    ..shader = LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: <Color>[light, dark],
    ).createShader(rect);

  void _shadow(Canvas c, Rect rect) {
    c.drawShadow(
      Path()..addOval(rect),
      Colors.black.withValues(alpha: .15),
      4,
      false,
    );
  }

  void _plate(Canvas c) {
    _shadow(c, const Rect.fromLTWH(16, 76, 68, 7));
    c.drawOval(
      const Rect.fromLTWH(15, 48, 70, 31),
      _fill(const Color(0xFFDDE8E4)),
    );
    c.drawOval(
      const Rect.fromLTWH(20, 44, 60, 30),
      _fill(const Color(0xFFF9FBFA)),
    );
  }

  void _bowl(Canvas c, Color inside) {
    _shadow(c, const Rect.fromLTWH(19, 76, 62, 7));
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
      case 'baguette':
        _baguette(canvas);
        break;
      case 'batbout':
        _roundBread(canvas, flatter: true, sesame: false);
        break;
      case 'bulgur':
        _grainBowl(canvas, const Color(0xFFC18D4F), coarse: true);
        break;
      case 'chebab':
        _pancakeStack(canvas, thin: true);
        break;
      case 'couscous':
        _couscous(canvas);
        break;
      case 'crepe':
        _crepe(canvas);
        break;
      case 'cereal':
        _cereal(canvas);
        break;
      case 'oats':
        _grainBowl(canvas, const Color(0xFFD7BC83), coarse: true);
        break;
      case 'waffle':
        _waffle(canvas);
        break;
      case 'granola':
        _granola(canvas);
        break;
      case 'harcha':
        _harcha(canvas);
        break;
      case 'krachel':
        _krachel(canvas);
        break;
      case 'corn':
        _corn(canvas);
        break;
      case 'muesli':
        _muesli(canvas);
        break;
      case 'barley':
        _grainBowl(canvas, const Color(0xFFC99E62), coarse: false);
        break;
      case 'white_bread':
        _loaf(canvas, sliced: false);
        break;
      case 'toast_bread':
        _loaf(canvas, sliced: true);
        break;
      case 'khameer_bread':
        _roundBread(canvas, flatter: false, sesame: true);
        break;
      case 'pita_bread':
        _pita(canvas);
        break;
      case 'regag_bread':
        _regag(canvas);
        break;
      case 'pancake':
        _pancakeStack(canvas, thin: false);
        break;
      case 'porridge':
        _porridge(canvas);
        break;
      case 'pasta':
        _pasta(canvas);
        break;
      case 'quinoa':
        _quinoa(canvas);
        break;
      default:
        break;
    }
    canvas.restore();
  }

  void _baguette(Canvas c) {
    _shadow(c, const Rect.fromLTWH(15, 72, 70, 8));
    const rect = Rect.fromLTWH(15, 28, 70, 42);
    final shape = RRect.fromRectAndRadius(rect, const Radius.circular(19));
    c.save();
    c.translate(50, 50);
    c.rotate(-.14);
    c.translate(-50, -50);
    c.drawRRect(
      shape,
      _gradient(rect, const Color(0xFFF0C77D), const Color(0xFFB86E34)),
    );
    c.drawRRect(shape, _stroke(const Color(0xFF945126), 1.4));
    for (final x in <double>[31, 46, 61, 74]) {
      c.drawLine(
        Offset(x, 34),
        Offset(x - 7, 57),
        _stroke(_cream.withValues(alpha: .8), 2.6),
      );
    }
    c.restore();
  }

  void _roundBread(Canvas c, {required bool flatter, required bool sesame}) {
    _shadow(c, const Rect.fromLTWH(19, 73, 62, 8));
    final rect = flatter
        ? const Rect.fromLTWH(18, 37, 64, 34)
        : const Rect.fromLTWH(20, 27, 60, 45);
    final radius = flatter ? 18.0 : 24.0;
    final shape = RRect.fromRectAndRadius(rect, Radius.circular(radius));
    c.drawRRect(
      shape,
      _gradient(rect, const Color(0xFFEBC47B), const Color(0xFFB66D36)),
    );
    c.drawRRect(shape, _stroke(const Color(0xFF8C522E), 1.3));
    c.drawArc(rect.deflate(8), .25, 2.5, false, _stroke(_cream, 1.6));
    if (sesame) {
      for (final p in const <Offset>[
        Offset(37, 40),
        Offset(48, 34),
        Offset(60, 41),
        Offset(43, 53),
        Offset(58, 55),
        Offset(67, 48),
      ]) {
        c.drawOval(
          Rect.fromCenter(center: p, width: 3.5, height: 1.4),
          _fill(const Color(0xFFF4E0A7)),
        );
      }
    }
  }

  void _grainBowl(Canvas c, Color grain, {required bool coarse}) {
    _bowl(c, const Color(0xFFE0C79B));
    for (var i = 0; i < 22; i++) {
      final col = i % 7;
      final row = i ~/ 7;
      final x = 31.0 + col * 6.0 + (row.isOdd ? 2.0 : 0.0);
      final y = 42.0 + row * 5.0;
      c.drawOval(
        Rect.fromCenter(
          center: Offset(x, y),
          width: coarse ? 4.2 : 3.2,
          height: coarse ? 2.4 : 1.8,
        ),
        _fill(grain),
      );
    }
  }

  void _pancakeStack(Canvas c, {required bool thin}) {
    _plate(c);
    final count = thin ? 4 : 3;
    for (var i = 0; i < count; i++) {
      final y = 54.0 - i * (thin ? 5.0 : 6.5);
      final height = thin ? 11.0 : 13.0;
      final rect = Rect.fromLTWH(29, y, 42, height);
      c.drawOval(
        rect,
        _gradient(rect, const Color(0xFFF0C778), const Color(0xFFC47A39)),
      );
      c.drawArc(
        rect,
        0,
        math.pi,
        false,
        _stroke(const Color(0xFF985725), 1),
      );
    }
    if (!thin) {
      c.drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(46, 35, 10, 7),
          const Radius.circular(2),
        ),
        _fill(const Color(0xFFF3D56A)),
      );
    }
  }

  void _couscous(Canvas c) {
    _plate(c);
    c.drawOval(
      const Rect.fromLTWH(26, 43, 48, 27),
      _gradient(
        const Rect.fromLTWH(26, 43, 48, 27),
        const Color(0xFFF0D48D),
        const Color(0xFFD4A65A),
      ),
    );
    const points = <Offset>[
      Offset(36, 53),
      Offset(47, 46),
      Offset(58, 57),
      Offset(66, 49),
    ];
    const colors = <Color>[
      Color(0xFFE58A3E),
      Color(0xFF6F9A4D),
      Color(0xFFE2BE48),
      Color(0xFF9B663A),
    ];
    for (var i = 0; i < points.length; i++) {
      c.drawCircle(points[i], 4.5, _fill(colors[i]));
    }
  }

  void _crepe(Canvas c) {
    _plate(c);
    final path = Path()
      ..moveTo(27, 61)
      ..lineTo(69, 43)
      ..lineTo(61, 69)
      ..close();
    c.drawPath(
      path,
      _gradient(
        const Rect.fromLTWH(27, 43, 42, 26),
        const Color(0xFFF0C77A),
        const Color(0xFFC27A3A),
      ),
    );
    c.drawPath(path, _stroke(const Color(0xFF97572A), 1.2));
  }

  void _cereal(Canvas c) {
    _bowl(c, const Color(0xFFF4EFE4));
    for (final p in const <Offset>[
      Offset(33, 47),
      Offset(42, 42),
      Offset(51, 49),
      Offset(60, 42),
      Offset(68, 49),
      Offset(39, 54),
      Offset(56, 55),
    ]) {
      c.drawCircle(p, 4, _fill(const Color(0xFFD6A64A)));
      c.drawCircle(p, 1.5, _fill(const Color(0xFFF6E0A5)));
    }
  }

  void _waffle(Canvas c) {
    _plate(c);
    const rect = Rect.fromLTWH(29, 35, 42, 36);
    final shape = RRect.fromRectAndRadius(rect, const Radius.circular(8));
    c.drawRRect(
      shape,
      _gradient(rect, const Color(0xFFE9B95F), const Color(0xFFB86D2E)),
    );
    c.drawRRect(shape, _stroke(const Color(0xFF8F5224), 1.2));
    for (final x in <double>[38, 48, 58, 68]) {
      c.drawLine(
        Offset(x, 38),
        Offset(x - 5, 68),
        _stroke(_cream.withValues(alpha: .55), 1),
      );
    }
    for (final y in <double>[44, 53, 62]) {
      c.drawLine(
        Offset(31, y),
        Offset(68, y + 2),
        _stroke(_cream.withValues(alpha: .55), 1),
      );
    }
  }

  void _granola(Canvas c) {
    _bowl(c, const Color(0xFFF1E7D4));
    for (var i = 0; i < 18; i++) {
      final x = 31.0 + (i % 6) * 7.0;
      final y = 42.0 + (i ~/ 6) * 6.0;
      c.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromCenter(center: Offset(x, y), width: 5, height: 3.5),
          const Radius.circular(2),
        ),
        _fill(i.isEven ? const Color(0xFFC88942) : const Color(0xFF9F6C35)),
      );
    }
  }

  void _harcha(Canvas c) {
    _plate(c);
    const rect = Rect.fromLTWH(27, 29, 46, 46);
    c.drawCircle(
      const Offset(50, 52),
      23,
      _gradient(rect, const Color(0xFFE8BD62), const Color(0xFFB97534)),
    );
    c.drawCircle(
      const Offset(50, 52),
      23,
      _stroke(const Color(0xFF965429), 1.2),
    );
  }

  void _krachel(Canvas c) {
    _shadow(c, const Rect.fromLTWH(21, 74, 58, 8));
    const rect = Rect.fromLTWH(24, 28, 52, 45);
    final shape = RRect.fromRectAndRadius(rect, const Radius.circular(23));
    c.drawRRect(
      shape,
      _gradient(rect, const Color(0xFFEBC378), const Color(0xFFB86B31)),
    );
    c.drawRRect(shape, _stroke(const Color(0xFF8F4D25), 1.2));
    c.drawLine(
      const Offset(50, 31),
      const Offset(50, 69),
      _stroke(_cream.withValues(alpha: .75), 1.6),
    );
  }

  void _corn(Canvas c) {
    _shadow(c, const Rect.fromLTWH(29, 75, 42, 7));
    final cob = RRect.fromRectAndRadius(
      const Rect.fromLTWH(35, 22, 30, 54),
      const Radius.circular(15),
    );
    c.drawRRect(cob, _fill(const Color(0xFFF0C84A)));
    for (var row = 0; row < 7; row++) {
      for (var col = 0; col < 4; col++) {
        final offset = row.isOdd ? 2.0 : 0.0;
        c.drawCircle(
          Offset(40.0 + col * 6.5 + offset, 28.0 + row * 6.5),
          2.5,
          _fill(const Color(0xFFFFDB5B)),
        );
      }
    }
    final leftLeaf = Path()
      ..moveTo(36, 66)
      ..quadraticBezierTo(21, 58, 24, 40)
      ..quadraticBezierTo(34, 51, 41, 72)
      ..close();
    c.drawPath(leftLeaf, _fill(_teal));
    final rightLeaf = Path()
      ..moveTo(64, 68)
      ..quadraticBezierTo(79, 58, 76, 40)
      ..quadraticBezierTo(66, 51, 59, 72)
      ..close();
    c.drawPath(rightLeaf, _fill(const Color(0xFF58A86C)));
  }

  void _muesli(Canvas c) {
    _bowl(c, const Color(0xFFF4EFE4));
    for (final p in const <Offset>[
      Offset(34, 45),
      Offset(43, 51),
      Offset(52, 43),
      Offset(61, 51),
      Offset(68, 44),
    ]) {
      c.drawOval(
        Rect.fromCenter(center: p, width: 7, height: 3.5),
        _fill(const Color(0xFFD4B77D)),
      );
    }
    c.drawCircle(const Offset(39, 39), 3.2, _fill(const Color(0xFFB84943)));
    c.drawCircle(const Offset(58, 39), 3.2, _fill(const Color(0xFF8F5A2C)));
  }

  void _loaf(Canvas c, {required bool sliced}) {
    _shadow(c, const Rect.fromLTWH(18, 75, 64, 8));
    const rect = Rect.fromLTWH(21, 27, 58, 47);
    final shape = RRect.fromRectAndRadius(rect, const Radius.circular(18));
    c.drawRRect(
      shape,
      _gradient(rect, const Color(0xFFF0C886), const Color(0xFFB9743A)),
    );
    c.drawRRect(shape, _stroke(const Color(0xFF92572C), 1.3));
    if (sliced) {
      final slice = RRect.fromRectAndRadius(
        const Rect.fromLTWH(31, 31, 38, 39),
        const Radius.circular(14),
      );
      c.drawRRect(slice, _fill(const Color(0xFFFFF1CB)));
      c.drawRRect(slice, _stroke(const Color(0xFFC28A50), 1.1));
    }
  }

  void _pita(Canvas c) {
    _shadow(c, const Rect.fromLTWH(18, 74, 64, 8));
    const rect = Rect.fromLTWH(18, 31, 64, 42);
    c.drawOval(
      rect,
      _gradient(rect, const Color(0xFFE6B86F), const Color(0xFFB56B35)),
    );
    c.drawOval(rect, _stroke(const Color(0xFF8F532C), 1.2));
  }

  void _regag(Canvas c) {
    _plate(c);
    for (var i = 0; i < 4; i++) {
      final y = 57.0 - i * 5.0;
      final path = Path()
        ..moveTo(28, y + 5)
        ..quadraticBezierTo(48, y - 3, 72, y + 2)
        ..lineTo(68, y + 8)
        ..quadraticBezierTo(47, y + 3, 30, y + 10)
        ..close();
      c.drawPath(
        path,
        _fill(i.isEven ? const Color(0xFFE7B766) : const Color(0xFFD59A48)),
      );
      c.drawPath(path, _stroke(const Color(0xFFA56530), .8));
    }
  }

  void _porridge(Canvas c) {
    _bowl(c, const Color(0xFFE5D5B6));
    c.drawArc(
      const Rect.fromLTWH(31, 41, 38, 15),
      .2,
      2.6,
      false,
      _stroke(const Color(0xFFC5A879), 1.5),
    );
  }

  void _pasta(Canvas c) {
    _plate(c);
    for (var i = 0; i < 8; i++) {
      final y = 44.0 + i * 3.2;
      final path = Path()
        ..moveTo(30, y)
        ..cubicTo(38, y - 5, 45, y + 5, 52, y)
        ..cubicTo(59, y - 5, 65, y + 4, 71, y - 1);
      c.drawPath(path, _stroke(const Color(0xFFE0A943), 2.3));
    }
  }

  void _quinoa(Canvas c) {
    _bowl(c, const Color(0xFFF0E2BC));
    for (var i = 0; i < 26; i++) {
      final row = i ~/ 8;
      final x = 30.0 + (i % 8) * 5.5 + (row.isOdd ? 1.5 : 0.0);
      final y = 41.0 + row * 5.0;
      c.drawCircle(
        Offset(x, y),
        1.5,
        _fill(
          i % 3 == 0 ? const Color(0xFFB88A54) : const Color(0xFFE5C98C),
        ),
      );
    }
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch3 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
