import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch5Ids = <String>{
  'fish_biryani',
  'chicken_biryani',
  'lamb_biryani',
  'falafel',
  'fattoush',
  'foul_medames',
  'kabsa_lamb',
  'khabeesa',
  'machboos_fish',
  'majboos_shrimp',
  'machboos_lamb',
  'madrooba',
  'manakish_cheese',
  'manakish_zaatar',
  'mandi_lamb',
  'margoog',
  'moutabal',
  'mutabbaq',
  'muhammar_rice',
  'saleeg',
  'saloona',
  'samboosa_cheese',
  'samboosa_meat',
  'shakshuka',
};

bool hasCodeFoodPictogramBatch5(String foodId) =>
    codeFoodPictogramBatch5Ids.contains(foodId);

class FoodPictogramPainterBatch5 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch5(this.foodId);

  static const _teal = Color(0xFF1F9E7A);
  static const _cream = Color(0xFFFFF7E5);
  static const _brown = Color(0xFF8B5533);

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
      Colors.black.withValues(alpha: .14),
      4,
      false,
    );
  }

  void _plate(Canvas c) {
    _shadow(c, const Rect.fromLTWH(16, 77, 68, 7));
    c.drawOval(const Rect.fromLTWH(15, 48, 70, 31), _fill(const Color(0xFFDDE8E4)));
    c.drawOval(const Rect.fromLTWH(20, 44, 60, 30), _fill(const Color(0xFFF9FBFA)));
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
      case 'fish_biryani':
        _ricePlatter(canvas, protein: _Protein.fish, spice: true);
        break;
      case 'chicken_biryani':
        _ricePlatter(canvas, protein: _Protein.chicken, spice: true);
        break;
      case 'lamb_biryani':
        _ricePlatter(canvas, protein: _Protein.lamb, spice: true);
        break;
      case 'falafel':
        _falafel(canvas);
        break;
      case 'fattoush':
        _salad(canvas);
        break;
      case 'foul_medames':
        _beans(canvas);
        break;
      case 'kabsa_lamb':
        _ricePlatter(canvas, protein: _Protein.lamb, spice: false);
        break;
      case 'khabeesa':
        _porridge(canvas, const Color(0xFFC58A52), glossy: true);
        break;
      case 'machboos_fish':
        _ricePlatter(canvas, protein: _Protein.fish, spice: false);
        break;
      case 'majboos_shrimp':
        _ricePlatter(canvas, protein: _Protein.shrimp, spice: false);
        break;
      case 'machboos_lamb':
        _ricePlatter(canvas, protein: _Protein.lamb, spice: false);
        break;
      case 'madrooba':
        _porridge(canvas, const Color(0xFFD2AE76), glossy: false);
        break;
      case 'manakish_cheese':
        _manakish(canvas, cheese: true);
        break;
      case 'manakish_zaatar':
        _manakish(canvas, cheese: false);
        break;
      case 'mandi_lamb':
        _ricePlatter(canvas, protein: _Protein.lamb, spice: true, roasted: true);
        break;
      case 'margoog':
        _stew(canvas, const Color(0xFFB7653D), vegetables: true);
        break;
      case 'moutabal':
        _dip(canvas, const Color(0xFFD7C7A1), eggplant: true);
        break;
      case 'mutabbaq':
        _mutabbaq(canvas);
        break;
      case 'muhammar_rice':
        _riceOnly(canvas, const Color(0xFFC27645));
        break;
      case 'saleeg':
        _riceOnly(canvas, const Color(0xFFF1E7D1), creamy: true);
        break;
      case 'saloona':
        _stew(canvas, const Color(0xFFC9673E), vegetables: true);
        break;
      case 'samboosa_cheese':
        _samboosa(canvas, const Color(0xFFF3D989));
        break;
      case 'samboosa_meat':
        _samboosa(canvas, const Color(0xFFC27D55));
        break;
      case 'shakshuka':
        _shakshuka(canvas);
        break;
      default:
        break;
    }
    canvas.restore();
  }

  void _ricePlatter(
    Canvas c, {
    required _Protein protein,
    required bool spice,
    bool roasted = false,
  }) {
    _plate(c);
    c.drawOval(
      const Rect.fromLTWH(27, 43, 46, 27),
      _gradient(
        const Rect.fromLTWH(27, 43, 46, 27),
        spice ? const Color(0xFFE8BD63) : const Color(0xFFF0D58D),
        spice ? const Color(0xFFC9853F) : const Color(0xFFD6A75C),
      ),
    );
    for (var i = 0; i < 12; i++) {
      final x = 31.0 + (i % 6) * 6.8;
      final y = 51.0 + (i ~/ 6) * 7.0;
      c.drawOval(Rect.fromCenter(center: Offset(x, y), width: 4.4, height: 1.5), _fill(_cream));
    }
    switch (protein) {
      case _Protein.chicken:
        final rect = const Rect.fromLTWH(42, 35, 24, 16);
        c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(7)), _gradient(rect, const Color(0xFFD49352), const Color(0xFF8B4D2D)));
        break;
      case _Protein.lamb:
        final rect = const Rect.fromLTWH(39, 36, 28, 17);
        c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(6)), _gradient(rect, roasted ? const Color(0xFFB75C33) : const Color(0xFFC47A49), const Color(0xFF754129)));
        break;
      case _Protein.fish:
        final fish = Path()
          ..moveTo(36, 45)
          ..quadraticBezierTo(50, 31, 64, 45)
          ..quadraticBezierTo(50, 57, 36, 45)
          ..close();
        c.drawPath(fish, _gradient(const Rect.fromLTWH(36, 32, 28, 25), const Color(0xFFF1C58A), const Color(0xFFB36A43)));
        c.drawCircle(const Offset(58, 43), 1.3, _fill(const Color(0xFF3F4643)));
        break;
      case _Protein.shrimp:
        c.drawArc(const Rect.fromLTWH(40, 34, 28, 22), .3, 4.5, false, _stroke(const Color(0xFFE8775F), 5));
        c.drawCircle(const Offset(61, 41), 1.3, _fill(const Color(0xFF4F3B37)));
        break;
    }
  }

  void _falafel(Canvas c) {
    _plate(c);
    for (final p in const <Offset>[Offset(36, 51), Offset(50, 44), Offset(63, 53), Offset(49, 60)]) {
      c.drawCircle(p, 8, _gradient(Rect.fromCircle(center: p, radius: 8), const Color(0xFFB48A43), const Color(0xFF6F5A2F)));
      c.drawCircle(p, 8, _stroke(const Color(0xFF5F4A28), 1));
    }
  }

  void _salad(Canvas c) {
    _bowl(c, const Color(0xFFE9E7CF));
    const spots = <Offset>[
      Offset(34, 46),
      Offset(44, 42),
      Offset(54, 49),
      Offset(64, 42),
      Offset(68, 52),
      Offset(42, 54),
    ];
    const colors = <Color>[
      Color(0xFF69A05A),
      Color(0xFFD4664E),
      Color(0xFF69A05A),
      Color(0xFFE2B74B),
      Color(0xFFD4664E),
      Color(0xFF69A05A),
    ];
    for (var i = 0; i < spots.length; i++) {
      c.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromCenter(center: spots[i], width: 8, height: 6),
          const Radius.circular(2),
        ),
        _fill(colors[i]),
      );
    }
    c.drawLine(const Offset(34, 55), const Offset(63, 43), _stroke(const Color(0xFFE4C58A), 2));
  }

  void _beans(Canvas c) {
    _bowl(c, const Color(0xFFB5764D));
    for (final p in const <Offset>[Offset(34, 46), Offset(43, 42), Offset(52, 48), Offset(61, 43), Offset(67, 51), Offset(43, 54)]) {
      c.drawOval(Rect.fromCenter(center: p, width: 7, height: 4.5), _fill(const Color(0xFF7F4C32)));
    }
    c.drawArc(const Rect.fromLTWH(39, 42, 22, 14), .2, 2.7, false, _stroke(const Color(0xFF6B914D), 1.8));
  }

  void _porridge(Canvas c, Color base, {required bool glossy}) {
    _bowl(c, base);
    c.drawOval(const Rect.fromLTWH(34, 41, 32, 17), _gradient(const Rect.fromLTWH(34, 41, 32, 17), glossy ? const Color(0xFFE0BC82) : const Color(0xFFE1C79E), base));
    if (glossy) {
      c.drawArc(const Rect.fromLTWH(39, 43, 20, 8), .2, 2.2, false, _stroke(_cream.withValues(alpha: .7), 1.4));
    }
  }

  void _manakish(Canvas c, {required bool cheese}) {
    _plate(c);
    const rect = Rect.fromLTWH(27, 31, 46, 41);
    c.drawOval(rect, _gradient(rect, const Color(0xFFE9B964), const Color(0xFFB66B32)));
    c.drawOval(rect, _stroke(_brown, 1.2));
    if (cheese) {
      c.drawOval(const Rect.fromLTWH(34, 38, 32, 26), _fill(const Color(0xFFF1DBA0)));
    } else {
      for (final p in const <Offset>[Offset(38, 43), Offset(49, 40), Offset(60, 46), Offset(44, 55), Offset(57, 57)]) {
        c.drawCircle(p, 3.2, _fill(const Color(0xFF657A3D)));
      }
    }
  }

  void _stew(Canvas c, Color broth, {required bool vegetables}) {
    _bowl(c, broth);
    if (vegetables) {
      const spots = <Offset>[Offset(35, 47), Offset(45, 42), Offset(55, 49), Offset(64, 43), Offset(47, 55)];
      const colors = <Color>[Color(0xFFDF8A3D), Color(0xFF6E9B50), Color(0xFFE2C052), Color(0xFF9B5C3C), Color(0xFF7EAE62)];
      for (var i = 0; i < spots.length; i++) {
        c.drawCircle(spots[i], 3.5, _fill(colors[i]));
      }
    }
  }

  void _dip(Canvas c, Color dip, {required bool eggplant}) {
    _bowl(c, dip);
    c.drawArc(const Rect.fromLTWH(37, 43, 26, 13), .2, 2.5, false, _stroke(eggplant ? const Color(0xFF6A7748) : _teal, 2));
    c.drawCircle(const Offset(50, 48), 2.5, _fill(const Color(0xFFE1B54E)));
  }

  void _mutabbaq(Canvas c) {
    _plate(c);
    final path = Path()
      ..moveTo(30, 61)
      ..lineTo(44, 37)
      ..lineTo(70, 47)
      ..lineTo(57, 69)
      ..close();
    c.drawPath(path, _gradient(const Rect.fromLTWH(30, 37, 40, 32), const Color(0xFFEBC06E), const Color(0xFFAF642F)));
    c.drawPath(path, _stroke(_brown, 1.2));
    c.drawLine(const Offset(42, 51), const Offset(60, 58), _stroke(_cream.withValues(alpha: .65), 1.4));
  }

  void _riceOnly(Canvas c, Color rice, {bool creamy = false}) {
    _bowl(c, rice.withValues(alpha: .35));
    c.drawOval(const Rect.fromLTWH(31, 40, 38, 20), _fill(rice));
    for (var i = 0; i < 12; i++) {
      final x = 34.0 + (i % 6) * 6.0;
      final y = 45.0 + (i ~/ 6) * 7.0;
      c.drawOval(Rect.fromCenter(center: Offset(x, y), width: creamy ? 3.5 : 4.5, height: 1.4), _fill(creamy ? const Color(0xFFFFF9EA) : const Color(0xFFF0D1A2)));
    }
  }

  void _samboosa(Canvas c, Color filling) {
    _plate(c);
    final tri = Path()
      ..moveTo(31, 67)
      ..lineTo(50, 34)
      ..lineTo(69, 67)
      ..close();
    c.drawPath(tri, _gradient(const Rect.fromLTWH(31, 34, 38, 33), const Color(0xFFF0C16B), const Color(0xFFB76831)));
    c.drawPath(tri, _stroke(_brown, 1.2));
    c.drawCircle(const Offset(50, 56), 5.5, _fill(filling));
  }

  void _shakshuka(Canvas c) {
    _plate(c);
    c.drawOval(const Rect.fromLTWH(28, 39, 44, 28), _fill(const Color(0xFFC95C3E)));
    for (final p in const <Offset>[Offset(42, 49), Offset(58, 51)]) {
      c.drawCircle(p, 7, _fill(const Color(0xFFF7F2DE)));
      c.drawCircle(p, 3.3, _fill(const Color(0xFFE4B22F)));
    }
    c.drawCircle(const Offset(50, 44), 2.4, _fill(const Color(0xFF66904A)));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch5 oldDelegate) =>
      oldDelegate.foodId != foodId;
}

enum _Protein { chicken, lamb, fish, shrimp }
