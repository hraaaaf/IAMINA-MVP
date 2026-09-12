import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch2Ids = <String>{
  'rfissa',
  'chicken_preserved_lemon_tagine',
  'kefta_tagine',
  'zaalouk',
  'taktouka',
  'amlou',
  'mint_tea',
  'moroccan_sweet_tea',
  'arabic_flatbread',
  'tannour_bread',
  'machboos_chicken',
  'kabsa_chicken',
  'mandi_chicken',
  'harees',
  'jareesh',
  'thareed',
  'balaleet',
  'luqaimat',
  'dates',
  'ajwa_dates',
  'arabic_coffee',
  'karak_tea',
  'shawarma_chicken',
  'hummus',
};

bool hasCodeFoodPictogramBatch2(String foodId) =>
    codeFoodPictogramBatch2Ids.contains(foodId);

class FoodPictogramPainterBatch2 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch2(this.foodId);

  static const Color _teal = Color(0xFF1F9E7A);
  static const Color _cream = Color(0xFFFFF8E8);
  static const Color _ink = Color(0xFF26343A);

  @override
  void paint(Canvas canvas, Size size) {
    final side = math.min(size.width, size.height);
    canvas.save();
    canvas.translate((size.width - side) / 2, (size.height - side) / 2);
    canvas.scale(side / 100, side / 100);

    switch (foodId) {
      case 'rfissa':
        _rfissa(canvas);
        break;
      case 'chicken_preserved_lemon_tagine':
        _tagine(canvas, chicken: true);
        break;
      case 'kefta_tagine':
        _tagine(canvas, chicken: false);
        break;
      case 'zaalouk':
        _zaalouk(canvas);
        break;
      case 'taktouka':
        _taktouka(canvas);
        break;
      case 'amlou':
        _amlou(canvas);
        break;
      case 'mint_tea':
        _tea(canvas, sweet: false);
        break;
      case 'moroccan_sweet_tea':
        _tea(canvas, sweet: true);
        break;
      case 'arabic_flatbread':
        _flatbread(canvas, tannour: false);
        break;
      case 'tannour_bread':
        _flatbread(canvas, tannour: true);
        break;
      case 'machboos_chicken':
        _riceDish(canvas, spice: const Color(0xFFB56C32), garnish: _teal);
        break;
      case 'kabsa_chicken':
        _riceDish(
          canvas,
          spice: const Color(0xFFBE4F34),
          garnish: const Color(0xFF8B6036),
        );
        break;
      case 'mandi_chicken':
        _riceDish(
          canvas,
          spice: const Color(0xFFD08A45),
          garnish: const Color(0xFFF0CF65),
        );
        break;
      case 'harees':
        _porridge(canvas, color: const Color(0xFFE5D1A4), grain: false);
        break;
      case 'jareesh':
        _porridge(canvas, color: const Color(0xFFD6B783), grain: true);
        break;
      case 'thareed':
        _thareed(canvas);
        break;
      case 'balaleet':
        _balaleet(canvas);
        break;
      case 'luqaimat':
        _luqaimat(canvas);
        break;
      case 'dates':
        _dates(canvas, ajwa: false);
        break;
      case 'ajwa_dates':
        _dates(canvas, ajwa: true);
        break;
      case 'arabic_coffee':
        _arabicCoffee(canvas);
        break;
      case 'karak_tea':
        _karak(canvas);
        break;
      case 'shawarma_chicken':
        _shawarma(canvas);
        break;
      case 'hummus':
        _hummus(canvas);
        break;
      default:
        break;
    }

    canvas.restore();
  }

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

  Paint _linear(Rect bounds, List<Color> colors) => Paint()
    ..shader = LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: colors,
    ).createShader(bounds);

  Paint _radial(Rect bounds, Color light, Color dark) => Paint()
    ..shader = RadialGradient(
      center: const Alignment(-.35, -.45),
      radius: .95,
      colors: <Color>[light, dark],
    ).createShader(bounds);

  void _shadow(Canvas canvas, Rect rect, {double alpha = .16}) {
    canvas.drawShadow(
      Path()..addOval(rect),
      Colors.black.withValues(alpha: alpha),
      4,
      false,
    );
  }

  void _plate(Canvas canvas, {Color color = const Color(0xFFF5F8F7)}) {
    _shadow(canvas, const Rect.fromLTWH(14, 74, 72, 9));
    canvas.drawOval(
      const Rect.fromLTWH(14, 42, 72, 40),
      _fill(const Color(0xFFDDE5E2)),
    );
    canvas.drawOval(const Rect.fromLTWH(19, 38, 62, 38), _fill(color));
    canvas.drawArc(
      const Rect.fromLTWH(19, 38, 62, 38),
      .05,
      math.pi * .95,
      false,
      _stroke(_teal.withValues(alpha: .45), 1.4),
    );
  }

  void _bowlBase(Canvas canvas, Color inside) {
    _shadow(canvas, const Rect.fromLTWH(18, 75, 64, 9));
    canvas.drawOval(
      const Rect.fromLTWH(18, 43, 64, 37),
      _fill(const Color(0xFFE6ECEA)),
    );
    canvas.drawOval(const Rect.fromLTWH(23, 35, 54, 26), _fill(inside));
    canvas.drawArc(
      const Rect.fromLTWH(22, 34, 56, 28),
      0,
      math.pi,
      false,
      _stroke(_teal, 1.6),
    );
  }

  void _rfissa(Canvas c) {
    _plate(c, color: const Color(0xFFFFFBF0));
    for (var i = 0; i < 12; i++) {
      final y = 48 + (i % 6) * 3.2;
      final x = 26 + (i ~/ 6) * 5 + (i % 3) * 8;
      c.drawLine(
        Offset(x, y),
        Offset(x + 18, y - 6),
        _stroke(const Color(0xFFD6A55C), 2.8),
      );
    }
    c.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(49, 39, 23, 22),
        const Radius.circular(8),
      ),
      _linear(
        const Rect.fromLTWH(49, 39, 23, 22),
        const <Color>[Color(0xFFE5A05B), Color(0xFFB96835)],
      ),
    );
    for (final p in const <Offset>[
      Offset(35, 55),
      Offset(43, 61),
      Offset(55, 68),
      Offset(64, 58),
    ]) {
      c.drawCircle(p, 2.4, _fill(const Color(0xFFB88745)));
    }
  }

  void _tagine(Canvas c, {required bool chicken}) {
    _shadow(c, const Rect.fromLTWH(16, 75, 68, 9));
    c.drawOval(
      const Rect.fromLTWH(17, 58, 66, 22),
      _linear(
        const Rect.fromLTWH(17, 58, 66, 22),
        const <Color>[Color(0xFFDBA86B), Color(0xFFA96638)],
      ),
    );
    final lid = Path()
      ..moveTo(28, 58)
      ..quadraticBezierTo(50, 18, 72, 58)
      ..close();
    c.drawPath(
      lid,
      _linear(
        const Rect.fromLTWH(28, 20, 44, 39),
        const <Color>[Color(0xFFF3C684), Color(0xFFC47B40)],
      ),
    );
    c.drawPath(lid, _stroke(const Color(0xFF8D542F), 1.5));
    c.drawCircle(const Offset(50, 23), 3.5, _fill(_teal));
    if (chicken) {
      c.drawCircle(const Offset(33, 65), 5, _fill(const Color(0xFFE9C45D)));
      c.drawCircle(const Offset(67, 65), 5, _fill(const Color(0xFF799A45)));
    } else {
      for (final x in <double>[37, 50, 63]) {
        c.drawCircle(Offset(x, 65), 5, _fill(const Color(0xFF8E4435)));
      }
    }
  }

  void _zaalouk(Canvas c) {
    _bowlBase(c, const Color(0xFF86483F));
    for (final p in const <Offset>[
      Offset(35, 47),
      Offset(44, 43),
      Offset(52, 51),
      Offset(62, 44),
      Offset(67, 52),
    ]) {
      c.drawOval(
        Rect.fromCenter(center: p, width: 8, height: 4),
        _fill(const Color(0xFF553A59)),
      );
    }
    c.drawPath(
      Path()
        ..moveTo(34, 41)
        ..quadraticBezierTo(50, 33, 67, 41),
      _stroke(const Color(0xFF6E9B54), 2.4),
    );
  }

  void _taktouka(Canvas c) {
    _bowlBase(c, const Color(0xFFC44837));
    for (final e in const <(Offset, Color)>[
      (Offset(36, 47), Color(0xFF3C9654)),
      (Offset(48, 43), Color(0xFFE6A53C)),
      (Offset(59, 51), Color(0xFF3C9654)),
      (Offset(67, 43), Color(0xFFE6A53C)),
    ]) {
      c.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromCenter(center: e.$1, width: 10, height: 5),
          const Radius.circular(2.5),
        ),
        _fill(e.$2),
      );
    }
  }

  void _amlou(Canvas c) {
    _bowlBase(c, const Color(0xFFA86838));
    c.drawArc(
      const Rect.fromLTWH(31, 40, 38, 17),
      .2,
      2.5,
      false,
      _stroke(const Color(0xFFD79A53), 2.2),
    );
    for (final p in const <Offset>[
      Offset(34, 31),
      Offset(46, 27),
      Offset(58, 30),
      Offset(68, 27),
    ]) {
      final almond = RRect.fromRectAndRadius(
        Rect.fromCenter(center: p, width: 9, height: 4),
        const Radius.circular(3),
      );
      c.drawRRect(almond, _fill(const Color(0xFFC68A4B)));
    }
  }

  void _tea(Canvas c, {required bool sweet}) {
    _shadow(c, const Rect.fromLTWH(29, 75, 42, 8));
    final glass = Path()
      ..moveTo(34, 27)
      ..lineTo(66, 27)
      ..lineTo(62, 75)
      ..lineTo(38, 75)
      ..close();
    c.drawPath(glass, _fill(const Color(0xFFEAF4F2).withValues(alpha: .82)));
    c.drawPath(glass, _stroke(const Color(0xFF93B7AF), 1.4));
    c.drawPath(
      Path()
        ..moveTo(37, 42)
        ..lineTo(63, 42)
        ..lineTo(61, 71)
        ..lineTo(39, 71)
        ..close(),
      _linear(
        const Rect.fromLTWH(37, 42, 26, 29),
        const <Color>[Color(0xFFD9A54A), Color(0xFF9C5D27)],
      ),
    );
    c.drawPath(
      Path()
        ..moveTo(45, 40)
        ..quadraticBezierTo(39, 29, 46, 24)
        ..quadraticBezierTo(51, 32, 48, 40),
      _stroke(const Color(0xFF2C8B58), 2.3),
    );
    c.drawOval(const Rect.fromLTWH(42, 25, 11, 6), _fill(const Color(0xFF3A9A65)));
    if (sweet) {
      c.drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(69, 58, 13, 13),
          const Radius.circular(3),
        ),
        _fill(const Color(0xFFFFFCF0)),
      );
      c.drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(72, 48, 11, 11),
          const Radius.circular(3),
        ),
        _fill(const Color(0xFFF5F0DE)),
      );
    }
  }

  void _flatbread(Canvas c, {required bool tannour}) {
    _shadow(c, const Rect.fromLTWH(15, 73, 70, 10));
    final bounds = tannour
        ? const Rect.fromLTWH(21, 18, 58, 60)
        : const Rect.fromLTWH(15, 28, 70, 48);
    final bread = tannour
        ? RRect.fromRectAndRadius(bounds, const Radius.circular(22))
        : RRect.fromRectAndRadius(bounds, const Radius.circular(16));
    c.drawRRect(
      bread,
      _linear(
        bounds,
        const <Color>[Color(0xFFE8B66B), Color(0xFFB87339)],
      ),
    );
    c.drawRRect(bread, _stroke(const Color(0xFF92562D), 1.4));
    for (final p in <Offset>[
      const Offset(34, 40),
      const Offset(48, 34),
      const Offset(62, 44),
      const Offset(42, 57),
      const Offset(60, 61),
    ]) {
      c.drawCircle(p, tannour ? 1.8 : 1.2, _fill(const Color(0xFF8F522A)));
    }
    if (!tannour) {
      c.drawArc(bounds.deflate(8), .25, 2.5, false, _stroke(_cream, 2));
    }
  }

  void _riceDish(Canvas c, {required Color spice, required Color garnish}) {
    _plate(c);
    c.drawOval(
      const Rect.fromLTWH(25, 42, 50, 28),
      _linear(
        const Rect.fromLTWH(25, 42, 50, 28),
        const <Color>[Color(0xFFF4D990), Color(0xFFD8AE59)],
      ),
    );
    for (var i = 0; i < 14; i++) {
      final a = i * .9;
      final r = 5 + (i % 5) * 2.5;
      c.drawLine(
        Offset(50 + math.cos(a) * r, 55 + math.sin(a) * r * .45),
        Offset(53 + math.cos(a) * r, 53 + math.sin(a) * r * .45),
        _stroke(const Color(0xFFF8E7B5), 1.1),
      );
    }
    c.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(47, 34, 28, 22),
        const Radius.circular(9),
      ),
      _linear(
        const Rect.fromLTWH(47, 34, 28, 22),
        <Color>[spice.withValues(alpha: .78), spice],
      ),
    );
    c.drawCircle(const Offset(35, 49), 2.6, _fill(garnish));
    c.drawCircle(const Offset(69, 61), 2.3, _fill(garnish));
  }

  void _porridge(Canvas c, {required Color color, required bool grain}) {
    _bowlBase(c, color);
    c.drawArc(
      const Rect.fromLTWH(30, 41, 40, 14),
      .15,
      2.7,
      false,
      _stroke(Colors.white.withValues(alpha: .38), 1.5),
    );
    if (grain) {
      for (var i = 0; i < 12; i++) {
        final x = 34 + (i % 6) * 6.2;
        final y = 44 + (i ~/ 6) * 6.5 + (i % 2) * 1.5;
        c.drawOval(
          Rect.fromCenter(center: Offset(x, y), width: 3.4, height: 1.8),
          _fill(const Color(0xFF9D7649).withValues(alpha: .72)),
        );
      }
    } else {
      c.drawCircle(const Offset(64, 45), 2.6, _fill(const Color(0xFFD7A84F)));
    }
  }

  void _thareed(Canvas c) {
    _bowlBase(c, const Color(0xFFB96B3E));
    for (final p in const <Offset>[
      Offset(34, 49),
      Offset(48, 44),
      Offset(61, 51),
    ]) {
      c.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromCenter(center: p, width: 10, height: 6),
          const Radius.circular(2),
        ),
        _fill(const Color(0xFFDDA65C)),
      );
    }
    c.drawPath(
      Path()
        ..moveTo(28, 35)
        ..lineTo(48, 33)
        ..lineTo(39, 47)
        ..close(),
      _fill(const Color(0xFFE7C47F)),
    );
  }

  void _balaleet(Canvas c) {
    _plate(c);
    for (var i = 0; i < 9; i++) {
      final y = 45 + i * 2.6;
      c.drawPath(
        Path()
          ..moveTo(26, y)
          ..cubicTo(38, y - 7, 59, y + 7, 75, y - 1),
        _stroke(const Color(0xFFDCA93D), 1.7),
      );
    }
    c.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(45, 35, 33, 19),
        const Radius.circular(8),
      ),
      _fill(const Color(0xFFFFF6D7)),
    );
    c.drawOval(const Rect.fromLTWH(58, 40, 12, 10), _fill(const Color(0xFFF0B52D)));
  }

  void _luqaimat(Canvas c) {
    _plate(c, color: const Color(0xFFFFFBF2));
    for (final p in const <Offset>[
      Offset(35, 58),
      Offset(46, 47),
      Offset(58, 58),
      Offset(67, 46),
      Offset(52, 66),
    ]) {
      final b = Rect.fromCenter(center: p, width: 15, height: 14);
      c.drawOval(b, _radial(b, const Color(0xFFF1B85A), const Color(0xFFA95A25)));
    }
    c.drawPath(
      Path()
        ..moveTo(31, 39)
        ..cubicTo(46, 32, 61, 45, 73, 36),
      _stroke(const Color(0xFFD99832).withValues(alpha: .85), 2.3),
    );
  }

  void _dates(Canvas c, {required bool ajwa}) {
    _shadow(c, const Rect.fromLTWH(18, 74, 64, 9));
    final light = ajwa ? const Color(0xFF684033) : const Color(0xFFB77645);
    final dark = ajwa ? const Color(0xFF2D2425) : const Color(0xFF6D3A25);
    for (final p in const <Offset>[
      Offset(31, 54),
      Offset(43, 39),
      Offset(55, 56),
      Offset(67, 42),
      Offset(70, 61),
      Offset(42, 66),
    ]) {
      final b = Rect.fromCenter(center: p, width: 16, height: 25);
      c.drawOval(b, _radial(b, light, dark));
      c.drawLine(
        Offset(p.dx - 4, p.dy),
        Offset(p.dx + 4, p.dy),
        _stroke(Colors.white.withValues(alpha: .17), 1),
      );
    }
    c.drawPath(
      Path()
        ..moveTo(38, 28)
        ..quadraticBezierTo(52, 18, 68, 28),
      _stroke(const Color(0xFF56824D), 2.6),
    );
  }

  void _arabicCoffee(Canvas c) {
    _shadow(c, const Rect.fromLTWH(18, 75, 68, 8));
    final pot = Path()
      ..moveTo(29, 34)
      ..lineTo(57, 34)
      ..quadraticBezierTo(65, 52, 56, 70)
      ..lineTo(30, 70)
      ..quadraticBezierTo(23, 52, 29, 34)
      ..close();
    c.drawPath(
      pot,
      _linear(
        const Rect.fromLTWH(24, 32, 43, 40),
        const <Color>[Color(0xFFE0C98C), Color(0xFF9A7940)],
      ),
    );
    c.drawPath(pot, _stroke(const Color(0xFF72552C), 1.4));
    c.drawLine(const Offset(42, 34), const Offset(43, 19), _stroke(_ink, 2));
    c.drawCircle(const Offset(43, 17), 3, _fill(_teal));
    c.drawPath(
      Path()
        ..moveTo(58, 39)
        ..quadraticBezierTo(84, 33, 78, 50),
      _stroke(const Color(0xFF9A7940), 4),
    );
    c.drawArc(
      const Rect.fromLTWH(65, 56, 22, 18),
      0,
      math.pi,
      false,
      _stroke(const Color(0xFF9A7940), 4),
    );
  }

  void _karak(Canvas c) {
    _shadow(c, const Rect.fromLTWH(28, 75, 44, 8));
    final glass = RRect.fromRectAndRadius(
      const Rect.fromLTWH(32, 24, 36, 52),
      const Radius.circular(7),
    );
    c.drawRRect(glass, _fill(const Color(0xFFEAF2F0).withValues(alpha: .86)));
    c.drawRRect(glass, _stroke(const Color(0xFF94B2AA), 1.4));
    c.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(36, 34, 28, 38),
        const Radius.circular(4),
      ),
      _linear(
        const Rect.fromLTWH(36, 34, 28, 38),
        const <Color>[Color(0xFFD59A60), Color(0xFF8B542F)],
      ),
    );
    c.drawPath(
      Path()
        ..moveTo(43, 27)
        ..quadraticBezierTo(48, 20, 54, 27)
        ..quadraticBezierTo(59, 20, 63, 27),
      _stroke(Colors.white.withValues(alpha: .55), 1.3),
    );
  }

  void _shawarma(Canvas c) {
    _shadow(c, const Rect.fromLTWH(20, 75, 60, 8));
    final wrap = Path()
      ..moveTo(27, 24)
      ..lineTo(69, 31)
      ..lineTo(74, 70)
      ..lineTo(37, 80)
      ..close();
    c.drawPath(
      wrap,
      _linear(
        const Rect.fromLTWH(27, 24, 47, 56),
        const <Color>[Color(0xFFEBCB8A), Color(0xFFBE8245)],
      ),
    );
    c.drawPath(wrap, _stroke(const Color(0xFF956233), 1.5));
    c.drawPath(
      Path()
        ..moveTo(31, 29)
        ..lineTo(66, 35)
        ..lineTo(58, 49)
        ..lineTo(35, 45)
        ..close(),
      _fill(const Color(0xFFC56C3D)),
    );
    c.drawLine(const Offset(42, 39), const Offset(54, 35), _stroke(_teal, 2.2));
    c.drawLine(
      const Offset(55, 44),
      const Offset(66, 39),
      _stroke(const Color(0xFFF1D15A), 2.2),
    );
  }

  void _hummus(Canvas c) {
    _bowlBase(c, const Color(0xFFE5C884));
    c.drawArc(
      const Rect.fromLTWH(31, 39, 38, 17),
      .2,
      2.45,
      false,
      _stroke(const Color(0xFFF4E0AE), 2.2),
    );
    c.drawCircle(const Offset(50, 47), 5, _fill(const Color(0xFFBD8F3F)));
    c.drawCircle(const Offset(50, 47), 2.2, _fill(_teal));
    c.drawPath(
      Path()
        ..moveTo(65, 34)
        ..quadraticBezierTo(72, 26, 78, 35),
      _stroke(const Color(0xFF3D9258), 2.1),
    );
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch2 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
