import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch4Ids = <String>{
  'rice',
  'basmati_rice',
  'brown_rice',
  'semolina',
  'vermicelli',
  'bissara',
  'briouat_cheese',
  'briouat_meat',
  'couscous_tfaya',
  'hssoua',
  'khlii',
  'maakouda',
  'mrouzia',
  'mechoui',
  'pastilla_chicken',
  'pastilla_seafood',
  'seffa',
  'sellou',
  'sfenj',
  'tajine',
  'lamb_prune_tagine',
  'tanjia',
  'zammita',
  'aseeda',
};

bool hasCodeFoodPictogramBatch4(String foodId) =>
    codeFoodPictogramBatch4Ids.contains(foodId);

class FoodPictogramPainterBatch4 extends CustomPainter {
  final String foodId;

  const FoodPictogramPainterBatch4(this.foodId);

  static const _teal = Color(0xFF1F9E7A);
  static const _cream = Color(0xFFFFF7E5);
  static const _brown = Color(0xFF8D5633);

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
      case 'rice':
        _rice(canvas, const Color(0xFFF3E5B8), longGrain: false);
        break;
      case 'basmati_rice':
        _rice(canvas, const Color(0xFFF4E6B8), longGrain: true);
        break;
      case 'brown_rice':
        _rice(canvas, const Color(0xFFB98C5B), longGrain: false);
        break;
      case 'semolina':
        _grainBowl(canvas, const Color(0xFFE4C56F), fine: true);
        break;
      case 'vermicelli':
        _noodles(canvas, sweet: false);
        break;
      case 'bissara':
        _soup(canvas, const Color(0xFF9DB46B), garnish: true);
        break;
      case 'briouat_cheese':
        _briouat(canvas, const Color(0xFFF4D98E));
        break;
      case 'briouat_meat':
        _briouat(canvas, const Color(0xFFC98555));
        break;
      case 'couscous_tfaya':
        _couscousTfaya(canvas);
        break;
      case 'hssoua':
        _soup(canvas, const Color(0xFFD4B66A), garnish: false);
        break;
      case 'khlii':
        _meatPlate(canvas, shredded: true);
        break;
      case 'maakouda':
        _patties(canvas);
        break;
      case 'mrouzia':
        _meatPlate(canvas, sweet: true);
        break;
      case 'mechoui':
        _meatPlate(canvas, roasted: true);
        break;
      case 'pastilla_chicken':
        _pastilla(canvas, seafood: false);
        break;
      case 'pastilla_seafood':
        _pastilla(canvas, seafood: true);
        break;
      case 'seffa':
        _noodles(canvas, sweet: true);
        break;
      case 'sellou':
        _grainBowl(canvas, const Color(0xFFA56D3E), fine: false);
        break;
      case 'sfenj':
        _sfenj(canvas);
        break;
      case 'tajine':
        _tagine(canvas, const Color(0xFFD47D3E), prunes: false);
        break;
      case 'lamb_prune_tagine':
        _tagine(canvas, const Color(0xFF9B5E3F), prunes: true);
        break;
      case 'tanjia':
        _tanjia(canvas);
        break;
      case 'zammita':
        _grainBowl(canvas, const Color(0xFF8D6A44), fine: true);
        break;
      case 'aseeda':
        _aseeda(canvas);
        break;
      default:
        break;
    }
    canvas.restore();
  }

  void _rice(Canvas c, Color grain, {required bool longGrain}) {
    _bowl(c, const Color(0xFFF7F0DB));
    for (var i = 0; i < 22; i++) {
      final x = 31.0 + (i % 7) * 6.0 + ((i ~/ 7).isOdd ? 2.0 : 0.0);
      final y = 43.0 + (i ~/ 7) * 5.0;
      c.drawOval(
        Rect.fromCenter(center: Offset(x, y), width: longGrain ? 5.0 : 3.6, height: longGrain ? 1.5 : 2.0),
        _fill(grain),
      );
    }
  }

  void _grainBowl(Canvas c, Color grain, {required bool fine}) {
    _bowl(c, grain.withValues(alpha: .35));
    for (var i = 0; i < 28; i++) {
      final x = 30.0 + (i % 8) * 5.6;
      final y = 42.0 + (i ~/ 8) * 4.2;
      c.drawCircle(Offset(x, y), fine ? 1.25 : 1.8, _fill(grain));
    }
  }

  void _noodles(Canvas c, {required bool sweet}) {
    _plate(c);
    for (var i = 0; i < 7; i++) {
      final y = 45.0 + i * 3.2;
      final path = Path()
        ..moveTo(29, y)
        ..cubicTo(39, y - 6, 58, y + 7, 70, y - 1);
      c.drawPath(path, _stroke(sweet ? const Color(0xFFD7A75E) : const Color(0xFFE4B55C), 2.4));
    }
    if (sweet) {
      c.drawCircle(const Offset(48, 45), 3, _fill(const Color(0xFF7C4C33)));
      c.drawCircle(const Offset(61, 51), 2.5, _fill(const Color(0xFF7C4C33)));
    }
  }

  void _soup(Canvas c, Color soup, {required bool garnish}) {
    _bowl(c, soup);
    if (garnish) {
      c.drawArc(const Rect.fromLTWH(36, 42, 28, 12), .2, 2.5, false, _stroke(const Color(0xFF4E7B4F), 2));
      c.drawCircle(const Offset(55, 47), 2.2, _fill(const Color(0xFFE6B24E)));
    }
  }

  void _briouat(Canvas c, Color filling) {
    _plate(c);
    final tri = Path()
      ..moveTo(31, 67)
      ..lineTo(50, 35)
      ..lineTo(69, 67)
      ..close();
    c.drawPath(tri, _gradient(const Rect.fromLTWH(31, 35, 38, 32), const Color(0xFFF2C36B), const Color(0xFFB96B31)));
    c.drawPath(tri, _stroke(_brown, 1.3));
    c.drawCircle(const Offset(50, 56), 5.5, _fill(filling));
  }

  void _couscousTfaya(Canvas c) {
    _plate(c);
    c.drawOval(const Rect.fromLTWH(27, 43, 46, 27), _fill(const Color(0xFFE4C978)));
    c.drawArc(const Rect.fromLTWH(31, 39, 38, 25), .1, 2.7, false, _stroke(const Color(0xFF9B5B34), 3));
    for (final p in const <Offset>[Offset(39, 49), Offset(51, 44), Offset(61, 53)]) {
      c.drawCircle(p, 3.2, _fill(const Color(0xFF6C4432)));
    }
  }

  void _meatPlate(Canvas c, {bool shredded = false, bool sweet = false, bool roasted = false}) {
    _plate(c);
    final meat = roasted ? const Color(0xFF8D4B2D) : const Color(0xFF9C5D3A);
    for (var i = 0; i < (shredded ? 5 : 3); i++) {
      final x = 34.0 + i * (shredded ? 7.0 : 12.0);
      final rect = Rect.fromLTWH(x, 45 + (i.isOdd ? 3.0 : 0.0), shredded ? 13 : 18, shredded ? 6 : 14);
      c.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(5)), _gradient(rect, const Color(0xFFC27A4C), meat));
    }
    if (sweet) {
      for (final p in const <Offset>[Offset(39, 44), Offset(55, 50), Offset(65, 43)]) {
        c.drawCircle(p, 3.5, _fill(const Color(0xFF5E3941)));
      }
    }
  }

  void _patties(Canvas c) {
    _plate(c);
    for (var i = 0; i < 3; i++) {
      final rect = Rect.fromLTWH(31 + i * 11.0, 42 + i * 4.0, 28, 16);
      c.drawOval(rect, _gradient(rect, const Color(0xFFE2B657), const Color(0xFFA8622F)));
    }
  }

  void _pastilla(Canvas c, {required bool seafood}) {
    _plate(c);
    const rect = Rect.fromLTWH(28, 34, 44, 37);
    c.drawOval(rect, _gradient(rect, const Color(0xFFF1C873), const Color(0xFFB96C32)));
    c.drawOval(rect, _stroke(_brown, 1.2));
    if (seafood) {
      c.drawArc(const Rect.fromLTWH(41, 43, 18, 14), .2, 4.8, false, _stroke(const Color(0xFFE87656), 2.5));
    } else {
      c.drawCircle(const Offset(50, 51), 4, _fill(_cream));
      c.drawLine(const Offset(42, 51), const Offset(58, 51), _stroke(_cream, 1.6));
    }
  }

  void _sfenj(Canvas c) {
    _plate(c);
    const rect = Rect.fromLTWH(28, 32, 44, 42);
    c.drawOval(rect, _gradient(rect, const Color(0xFFE8B458), const Color(0xFFA95E2E)));
    c.drawOval(const Rect.fromLTWH(42, 44, 16, 15), _fill(const Color(0xFFF9FBFA)));
  }

  void _tagine(Canvas c, Color stew, {required bool prunes}) {
    _shadow(c, const Rect.fromLTWH(19, 76, 62, 7));
    c.drawOval(const Rect.fromLTWH(19, 52, 62, 27), _fill(const Color(0xFFC96C3D)));
    c.drawOval(const Rect.fromLTWH(24, 47, 52, 21), _fill(stew));
    final lid = Path()
      ..moveTo(31, 50)
      ..lineTo(50, 20)
      ..lineTo(69, 50)
      ..close();
    c.drawPath(lid, _gradient(const Rect.fromLTWH(31, 20, 38, 30), const Color(0xFFE49A58), const Color(0xFFB75D35)));
    c.drawCircle(const Offset(50, 18), 4, _fill(_teal));
    if (prunes) {
      for (final p in const <Offset>[Offset(39, 56), Offset(51, 53), Offset(62, 57)]) {
        c.drawCircle(p, 3.5, _fill(const Color(0xFF5A3542)));
      }
    }
  }

  void _tanjia(Canvas c) {
    _shadow(c, const Rect.fromLTWH(31, 76, 38, 7));
    final body = RRect.fromRectAndRadius(const Rect.fromLTWH(32, 29, 36, 49), const Radius.circular(13));
    c.drawRRect(body, _gradient(const Rect.fromLTWH(32, 29, 36, 49), const Color(0xFFD99658), const Color(0xFF9F5736)));
    c.drawRRect(body, _stroke(_brown, 1.3));
    c.drawRect(const Rect.fromLTWH(43, 22, 14, 10), _fill(const Color(0xFFB86D42)));
    c.drawLine(const Offset(39, 46), const Offset(61, 46), _stroke(_cream.withValues(alpha: .55), 1.2));
  }

  void _aseeda(Canvas c) {
    _bowl(c, const Color(0xFFD6AD6C));
    c.drawOval(const Rect.fromLTWH(34, 40, 32, 20), _gradient(const Rect.fromLTWH(34, 40, 32, 20), const Color(0xFFE3C58C), const Color(0xFFB57A45)));
    c.drawCircle(const Offset(50, 48), 4, _fill(const Color(0xFF8C5633)));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch4 oldDelegate) =>
      oldDelegate.foodId != foodId;
}
