import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramIds = <String>{
  'egg',
  'whole_grain_bread',
  'chicken',
  'grilled_chicken',
  'beef',
  'sardines',
  'salmon',
  'milk',
  'plain_yogurt',
  'apple',
  'banana',
  'orange',
  'tomato',
  'potato',
  'lentils',
  'chickpeas',
  'olive_oil',
  'pizza',
  'burger',
  'moroccan_bread',
  'msemen',
  'baghrir',
  'couscous_7_vegetables',
  'harira',
};

bool hasCodeFoodPictogram(String foodId) =>
    codeFoodPictogramIds.contains(foodId);

class FoodPictogramPainter extends CustomPainter {
  final String foodId;

  const FoodPictogramPainter(this.foodId);

  static const Color _teal = Color(0xFF1F9E7A);
  static const Color _navy = Color(0xFF17304B);

  @override
  void paint(Canvas canvas, Size size) {
    final side = math.min(size.width, size.height);
    canvas.save();
    canvas.translate(
      (size.width - side) / 2,
      (size.height - side) / 2,
    );
    canvas.scale(side / 100, side / 100);

    switch (foodId) {
      case 'egg':
        _egg(canvas);
      case 'whole_grain_bread':
        _wholeGrainBread(canvas);
      case 'chicken':
        _chicken(canvas, grilled: false);
      case 'grilled_chicken':
        _chicken(canvas, grilled: true);
      case 'beef':
        _beef(canvas);
      case 'sardines':
        _sardines(canvas);
      case 'salmon':
        _salmon(canvas);
      case 'milk':
        _milk(canvas);
      case 'plain_yogurt':
        _yogurt(canvas);
      case 'apple':
        _apple(canvas);
      case 'banana':
        _banana(canvas);
      case 'orange':
        _orange(canvas);
      case 'tomato':
        _tomato(canvas);
      case 'potato':
        _potato(canvas);
      case 'lentils':
        _bowl(canvas, soup: const Color(0xFF7D5033), lentils: true);
      case 'chickpeas':
        _bowl(canvas, soup: const Color(0xFFD9B06A), chickpeas: true);
      case 'olive_oil':
        _oliveOil(canvas);
      case 'pizza':
        _pizza(canvas);
      case 'burger':
        _burger(canvas);
      case 'moroccan_bread':
        _moroccanBread(canvas);
      case 'msemen':
        _msemen(canvas);
      case 'baghrir':
        _baghrir(canvas);
      case 'couscous_7_vegetables':
        _couscous(canvas);
      case 'harira':
        _bowl(canvas, soup: const Color(0xFFA84430), harira: true);
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

  void _shadow(Canvas canvas, Rect rect, {double alpha = .18}) {
    final path = Path()..addOval(rect);
    canvas.drawShadow(
      path,
      Colors.black.withValues(alpha: alpha),
      4,
      false,
    );
  }

  Paint _radial(Rect bounds, Color light, Color dark) => Paint()
    ..shader = RadialGradient(
      center: const Alignment(-.35, -.45),
      radius: .95,
      colors: <Color>[light, dark],
      stops: const <double>[0, 1],
    ).createShader(bounds);

  Paint _linear(Rect bounds, List<Color> colors) => Paint()
    ..shader = LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: colors,
    ).createShader(bounds);

  void _egg(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(23, 72, 55, 12));
    final shell = Path()
      ..moveTo(40, 14)
      ..cubicTo(21, 33, 24, 69, 45, 77)
      ..cubicTo(65, 85, 78, 60, 68, 36)
      ..cubicTo(60, 18, 50, 8, 40, 14)
      ..close();
    canvas.drawPath(
      shell,
      _linear(
        const Rect.fromLTWH(22, 10, 58, 74),
        const <Color>[Color(0xFFFFF9E9), Color(0xFFE8D6AF)],
      ),
    );
    canvas.drawPath(shell, _stroke(const Color(0xFFC8B48E), 1.6));

    canvas.drawOval(
      const Rect.fromLTWH(52, 48, 36, 27),
      _fill(const Color(0xFFF8F7F0)),
    );
    canvas.drawOval(
      const Rect.fromLTWH(63, 54, 16, 16),
      _radial(
        const Rect.fromLTWH(63, 54, 16, 16),
        const Color(0xFFFFD75E),
        const Color(0xFFE79A14),
      ),
    );
  }

  void _wholeGrainBread(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(15, 73, 70, 11));
    final rrect = RRect.fromRectAndRadius(
      const Rect.fromLTWH(17, 26, 66, 48),
      const Radius.circular(18),
    );
    canvas.drawRRect(
      rrect,
      _linear(
        const Rect.fromLTWH(17, 26, 66, 48),
        const <Color>[Color(0xFFDCA867), Color(0xFF9E5D2B)],
      ),
    );
    canvas.drawRRect(rrect, _stroke(const Color(0xFF75431F), 1.8));
    for (final x in <double>[33, 49, 65]) {
      final path = Path()
        ..moveTo(x - 7, 35)
        ..quadraticBezierTo(x, 49, x + 9, 60);
      canvas.drawPath(path, _stroke(const Color(0xFFF2D59A), 3));
    }
    canvas.drawOval(
      const Rect.fromLTWH(25, 31, 25, 10),
      _fill(Colors.white.withValues(alpha: .13)),
    );
  }

  void _chicken(Canvas canvas, {required bool grilled}) {
    _shadow(canvas, const Rect.fromLTWH(17, 73, 68, 11));
    final body = RRect.fromRectAndRadius(
      const Rect.fromLTWH(20, 25, 48, 48),
      const Radius.circular(19),
    );
    canvas.drawRRect(
      body,
      _linear(
        const Rect.fromLTWH(20, 25, 48, 48),
        const <Color>[Color(0xFFF1AF68), Color(0xFFC66F37)],
      ),
    );
    canvas.drawRRect(body, _stroke(const Color(0xFF9B4F29), 1.6));
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(62, 50, 22, 12),
        const Radius.circular(5),
      ),
      _fill(const Color(0xFFF2E2C6)),
    );
    canvas.drawOval(
      const Rect.fromLTWH(79, 47, 10, 10),
      _fill(const Color(0xFFF5E7CD)),
    );
    canvas.drawOval(
      const Rect.fromLTWH(81, 57, 10, 10),
      _fill(const Color(0xFFF5E7CD)),
    );
    if (grilled) {
      for (final x in <double>[29, 39, 49, 59]) {
        canvas.drawLine(
          Offset(x, 33),
          Offset(x + 12, 62),
          _stroke(const Color(0xFF6B3923), 2.4),
        );
      }
    }
    canvas.drawOval(
      const Rect.fromLTWH(26, 29, 22, 9),
      _fill(Colors.white.withValues(alpha: .14)),
    );
  }

  void _beef(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(15, 72, 70, 12));
    final steak = Path()
      ..moveTo(19, 46)
      ..lineTo(30, 28)
      ..lineTo(56, 22)
      ..lineTo(78, 34)
      ..lineTo(84, 52)
      ..lineTo(69, 69)
      ..lineTo(43, 77)
      ..lineTo(21, 66)
      ..close();
    canvas.drawPath(
      steak,
      _linear(
        const Rect.fromLTWH(18, 22, 67, 55),
        const <Color>[Color(0xFFCB7768), Color(0xFF7D2E28)],
      ),
    );
    canvas.drawPath(steak, _stroke(const Color(0xFF68241F), 1.8));
    for (final x in <double>[38, 50, 62]) {
      canvas.drawLine(
        Offset(x, 33),
        Offset(x + 10, 61),
        _stroke(const Color(0xFF69372F), 2.2),
      );
    }
  }

  void _sardines(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(12, 73, 76, 10));
    _fish(canvas, 33, 38, const Color(0xFF4A91B3));
    _fish(canvas, 26, 57, const Color(0xFF3F82A0));
  }

  void _fish(Canvas canvas, double x, double y, Color color) {
    canvas.drawOval(Rect.fromLTWH(x - 16, y, 42, 15), _fill(color));
    final tail = Path()
      ..moveTo(x + 24, y + 7.5)
      ..lineTo(x + 39, y - 2)
      ..lineTo(x + 38, y + 17)
      ..close();
    canvas.drawPath(tail, _fill(color.withValues(alpha: .9)));
    canvas.drawCircle(
      Offset(x - 7, y + 6),
      1.5,
      _fill(const Color(0xFF0C1B25)),
    );
    canvas.drawLine(
      Offset(x - 1, y + 6),
      Offset(x + 19, y + 6),
      _stroke(Colors.white.withValues(alpha: .45), 1),
    );
  }

  void _salmon(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(14, 73, 72, 10));
    final fillet = Path()
      ..moveTo(14, 55)
      ..lineTo(28, 32)
      ..lineTo(63, 29)
      ..lineTo(85, 45)
      ..lineTo(70, 66)
      ..lineTo(31, 72)
      ..close();
    canvas.drawPath(
      fillet,
      _linear(
        const Rect.fromLTWH(14, 29, 71, 43),
        const <Color>[Color(0xFFFF9D78), Color(0xFFD95D42)],
      ),
    );
    for (final x in <double>[34, 44, 54, 64, 74]) {
      canvas.drawLine(
        Offset(x, 34),
        Offset(x - 7, 63),
        _stroke(const Color(0xFFFFD4C1), 1.7),
      );
    }
  }

  void _milk(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(28, 74, 44, 9));
    final glass = RRect.fromRectAndRadius(
      const Rect.fromLTWH(32, 18, 36, 60),
      const Radius.circular(7),
    );
    canvas.drawRRect(glass, _fill(const Color(0xFFEAF3F0)));
    canvas.drawRRect(glass, _stroke(const Color(0xFFB5C7C1), 1.4));
    canvas.drawRect(
      const Rect.fromLTWH(35, 31, 30, 42),
      _linear(
        const Rect.fromLTWH(35, 31, 30, 42),
        const <Color>[Color(0xFFFFFEF5), Color(0xFFEFEFDD)],
      ),
    );
    canvas.drawOval(
      const Rect.fromLTWH(35, 27, 30, 8),
      _fill(const Color(0xFFFBFBF1)),
    );
  }

  void _yogurt(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(20, 72, 60, 10));
    canvas.drawOval(
      const Rect.fromLTWH(19, 43, 62, 31),
      _fill(const Color(0xFFE7ECE9)),
    );
    canvas.drawOval(
      const Rect.fromLTWH(23, 36, 54, 22),
      _fill(const Color(0xFFFAFAF4)),
    );
    canvas.drawOval(
      const Rect.fromLTWH(31, 40, 23, 7),
      _fill(Colors.white.withValues(alpha: .7)),
    );
  }

  void _apple(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(23, 73, 54, 11));
    final bounds = const Rect.fromLTWH(25, 23, 52, 54);
    canvas.drawOval(
      bounds,
      _radial(bounds, const Color(0xFFFF5A52), const Color(0xFFB81325)),
    );
    canvas.drawLine(
      const Offset(52, 25),
      const Offset(57, 11),
      _stroke(const Color(0xFF6D4428), 3),
    );
    canvas.drawOval(
      const Rect.fromLTWH(56, 11, 20, 9),
      _fill(const Color(0xFF2D8B55)),
    );
    canvas.drawCircle(
      const Offset(37, 36),
      5,
      _fill(Colors.white.withValues(alpha: .5)),
    );
  }

  void _banana(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(18, 71, 64, 11));
    final outer = Paint()
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 20
      ..color = const Color(0xFFF0C02F);
    final inner = Paint()
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 12
      ..color = const Color(0xFFFFE15C);
    final rect = const Rect.fromLTWH(18, 15, 64, 60);
    canvas.drawArc(rect, .15, 2.25, false, outer);
    canvas.drawArc(rect, .18, 2.18, false, inner);
  }

  void _orange(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(23, 73, 54, 11));
    final bounds = const Rect.fromLTWH(25, 22, 52, 55);
    canvas.drawOval(
      bounds,
      _radial(bounds, const Color(0xFFFFB442), const Color(0xFFE27400)),
    );
    canvas.drawOval(
      const Rect.fromLTWH(50, 18, 18, 9),
      _fill(const Color(0xFF31905A)),
    );
    canvas.drawCircle(
      const Offset(37, 35),
      5,
      _fill(Colors.white.withValues(alpha: .5)),
    );
  }

  void _tomato(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(23, 73, 54, 11));
    final bounds = const Rect.fromLTWH(25, 25, 52, 52);
    canvas.drawOval(
      bounds,
      _radial(bounds, const Color(0xFFFF5B50), const Color(0xFFB81720)),
    );
    final crown = Path()
      ..moveTo(51, 22)
      ..lineTo(44, 34)
      ..lineTo(34, 29)
      ..lineTo(40, 40)
      ..lineTo(29, 40)
      ..lineTo(44, 46)
      ..lineTo(51, 58)
      ..lineTo(56, 45)
      ..lineTo(72, 48)
      ..lineTo(62, 38)
      ..lineTo(72, 31)
      ..lineTo(58, 34)
      ..close();
    canvas.drawPath(crown, _fill(const Color(0xFF2E8B4F)));
  }

  void _potato(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(21, 73, 58, 10));
    final bounds = const Rect.fromLTWH(23, 25, 55, 50);
    canvas.drawOval(
      bounds,
      _radial(bounds, const Color(0xFFD2A066), const Color(0xFF9A6237)),
    );
    for (final point in <Offset>[
      const Offset(38, 43),
      const Offset(55, 37),
      const Offset(65, 50),
      const Offset(46, 61),
      const Offset(62, 65),
    ]) {
      canvas.drawCircle(point, 1.6, _fill(const Color(0xFF754928)));
    }
  }

  void _bowl(
    Canvas canvas, {
    required Color soup,
    bool lentils = false,
    bool chickpeas = false,
    bool harira = false,
  }) {
    _shadow(canvas, const Rect.fromLTWH(18, 73, 64, 10));
    canvas.drawOval(
      const Rect.fromLTWH(20, 42, 60, 37),
      _fill(const Color(0xFFE7ECEA)),
    );
    canvas.drawOval(
      const Rect.fromLTWH(24, 34, 52, 24),
      _fill(soup),
    );
    canvas.drawArc(
      const Rect.fromLTWH(23, 33, 54, 26),
      0,
      math.pi,
      false,
      _stroke(_teal, 1.7),
    );
    final count = lentils ? 15 : chickpeas ? 10 : 8;
    for (var i = 0; i < count; i++) {
      final angle = i * 2.3;
      final radius = 5 + (i % 5) * 2.5;
      final x = 50 + math.cos(angle) * radius;
      final y = 47 + math.sin(angle) * radius * .36;
      final color = lentils
          ? const Color(0xFFA66D3D)
          : chickpeas
          ? const Color(0xFFE4BE78)
          : i.isEven
          ? const Color(0xFFDCB16E)
          : const Color(0xFF4D925A);
      canvas.drawOval(
        Rect.fromCenter(center: Offset(x, y), width: 3.2, height: 2.4),
        _fill(color),
      );
    }
    if (harira) {
      canvas.drawArc(
        const Rect.fromLTWH(34, 40, 32, 13),
        .4,
        1.8,
        false,
        _stroke(Colors.white.withValues(alpha: .22), 1),
      );
    }
  }

  void _oliveOil(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(29, 73, 42, 10));
    final bottle = RRect.fromRectAndRadius(
      const Rect.fromLTWH(34, 23, 32, 54),
      const Radius.circular(7),
    );
    canvas.drawRRect(bottle, _fill(const Color(0xFFD9E3C9)));
    canvas.drawRRect(bottle, _stroke(const Color(0xFF6D7A4B), 1.5));
    canvas.drawRect(
      const Rect.fromLTWH(38, 47, 24, 26),
      _linear(
        const Rect.fromLTWH(38, 47, 24, 26),
        const <Color>[Color(0xFFD9B34A), Color(0xFF9D7B22)],
      ),
    );
    canvas.drawRect(
      const Rect.fromLTWH(40, 14, 20, 12),
      _fill(const Color(0xFF355A3C)),
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(42, 9, 16, 7),
        const Radius.circular(2),
      ),
      _fill(const Color(0xFF28472F)),
    );
  }

  void _pizza(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(16, 73, 68, 10));
    final slice = Path()
      ..moveTo(28, 15)
      ..lineTo(84, 63)
      ..lineTo(27, 77)
      ..close();
    canvas.drawPath(slice, _fill(const Color(0xFFF1B84A)));
    canvas.drawLine(
      const Offset(28, 16),
      const Offset(27, 77),
      _stroke(const Color(0xFFC27C2D), 7),
    );
    for (final center in <Offset>[
      const Offset(47, 35),
      const Offset(61, 48),
      const Offset(43, 60),
      const Offset(69, 61),
    ]) {
      canvas.drawCircle(center, 5, _fill(const Color(0xFFB73034)));
    }
  }

  void _burger(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(18, 75, 64, 9));
    canvas.drawOval(
      const Rect.fromLTWH(22, 21, 56, 25),
      _linear(
        const Rect.fromLTWH(22, 21, 56, 25),
        const <Color>[Color(0xFFF1B65E), Color(0xFFCA7E32)],
      ),
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(25, 45, 50, 10),
        const Radius.circular(4),
      ),
      _fill(const Color(0xFF4B954F)),
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(24, 53, 52, 13),
        const Radius.circular(5),
      ),
      _fill(const Color(0xFF6B3829)),
    );
    final cheese = Path()
      ..moveTo(24, 65)
      ..lineTo(76, 65)
      ..lineTo(70, 73)
      ..lineTo(29, 73)
      ..close();
    canvas.drawPath(cheese, _fill(const Color(0xFFF2C33D)));
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(22, 72, 56, 11),
        const Radius.circular(5),
      ),
      _fill(const Color(0xFFCF8738)),
    );
  }

  void _moroccanBread(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(17, 74, 66, 10));
    canvas.drawOval(
      const Rect.fromLTWH(19, 22, 62, 57),
      _linear(
        const Rect.fromLTWH(19, 22, 62, 57),
        const <Color>[Color(0xFFE0B06E), Color(0xFFA7632D)],
      ),
    );
    canvas.drawOval(
      const Rect.fromLTWH(19, 22, 62, 57),
      _stroke(const Color(0xFF7C461F), 1.5),
    );
    for (final x in <double>[37, 50, 63]) {
      canvas.drawArc(
        Rect.fromLTWH(x - 8, 32, 16, 30),
        .9,
        1.4,
        false,
        _stroke(const Color(0xFFF1D29C), 2.5),
      );
    }
  }

  void _msemen(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(17, 74, 66, 10));
    final square = RRect.fromRectAndRadius(
      const Rect.fromLTWH(20, 25, 60, 53),
      const Radius.circular(7),
    );
    canvas.drawRRect(
      square,
      _linear(
        const Rect.fromLTWH(20, 25, 60, 53),
        const <Color>[Color(0xFFF2C06F), Color(0xFFC8863D)],
      ),
    );
    canvas.drawRRect(square, _stroke(const Color(0xFF9F6028), 1.5));
    for (final y in <double>[38, 48, 58, 68]) {
      canvas.drawLine(
        Offset(28, y),
        Offset(72, y - 3),
        _stroke(const Color(0xFFAD6B30), 1),
      );
    }
  }

  void _baghrir(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(17, 74, 66, 10));
    canvas.drawOval(
      const Rect.fromLTWH(18, 25, 64, 53),
      _linear(
        const Rect.fromLTWH(18, 25, 64, 53),
        const <Color>[Color(0xFFF3CD80), Color(0xFFC88A40)],
      ),
    );
    canvas.drawOval(
      const Rect.fromLTWH(18, 25, 64, 53),
      _stroke(const Color(0xFF9F642C), 1.4),
    );
    for (var i = 0; i < 32; i++) {
      final angle = i * 2.4;
      final radius = 8 + (i % 7) * 2.6;
      final x = 50 + math.cos(angle) * radius;
      final y = 51 + math.sin(angle) * radius * .7;
      canvas.drawCircle(
        Offset(x, y),
        1.2 + (i % 3) * .2,
        _fill(const Color(0xFF9D642F).withValues(alpha: .68)),
      );
    }
  }

  void _couscous(Canvas canvas) {
    _shadow(canvas, const Rect.fromLTWH(15, 75, 70, 9));
    canvas.drawOval(
      const Rect.fromLTWH(14, 37, 72, 46),
      _fill(const Color(0xFFF6F8F6)),
    );
    canvas.drawOval(
      const Rect.fromLTWH(22, 34, 56, 35),
      _fill(const Color(0xFFE1C67F)),
    );
    for (var i = 0; i < 25; i++) {
      final angle = i * 2.4;
      final radius = 5 + (i % 6) * 3;
      final x = 50 + math.cos(angle) * radius;
      final y = 52 + math.sin(angle) * radius * .45;
      canvas.drawCircle(
        Offset(x, y),
        .8,
        _fill(const Color(0xFFF6DFA8)),
      );
    }
    final vegetables = <(Rect, Color)>[
      (const Rect.fromLTWH(33, 35, 7, 20), const Color(0xFFE18B31)),
      (const Rect.fromLTWH(45, 32, 7, 23), const Color(0xFF5A8C4B)),
      (const Rect.fromLTWH(57, 36, 7, 20), const Color(0xFFEAB73F)),
      (const Rect.fromLTWH(39, 52, 8, 8), const Color(0xFFB54538)),
      (const Rect.fromLTWH(54, 51, 8, 9), const Color(0xFF65994A)),
    ];
    for (final entry in vegetables) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(entry.$1, const Radius.circular(2)),
        _fill(entry.$2),
      );
    }
    canvas.drawArc(
      const Rect.fromLTWH(14, 37, 72, 46),
      0,
      math.pi,
      false,
      _stroke(_teal, 1.4),
    );
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainter oldDelegate) =>
      oldDelegate.foodId != foodId;
}
