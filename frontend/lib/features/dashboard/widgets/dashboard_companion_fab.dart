import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/amina_visual_language.dart';

/// Premium 58dp IAMINA chat entry. No patient facts, animation loop, external
/// image, leaf logo, or ChatBrain. Focusable/tappable with localized semantics.
class DashboardCompanionFab extends StatelessWidget {
  const DashboardCompanionFab({super.key});

  @override
  Widget build(BuildContext context) {
    final label = switch (Localizations.localeOf(context).languageCode) {
      'ar' => 'تحدث مع IAmina',
      'en' => 'Talk with IAMINA',
      _ => 'Parler avec IAMINA',
    };

    return Semantics(
      button: true,
      label: label,
      child: Tooltip(
        message: label,
        preferBelow: false,
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            key: const ValueKey('dashboard-companion-chat-action'),
            onTap: () => context.push('/companion/chat'),
            customBorder: const CircleBorder(),
            child: Container(
              width: 58,
              height: 58,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const RadialGradient(
                  center: Alignment(-.45, -.65),
                  radius: 1.22,
                  colors: [
                    Color(0xFF149578),
                    AminaVisualLanguage.actionGreen,
                    AminaVisualLanguage.forestDeep,
                  ],
                  stops: [0, .4, 1],
                ),
                border: Border.all(
                  color: const Color(0xFF5BAF9B),
                  width: 1,
                ),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x35034536),
                    blurRadius: 12,
                    spreadRadius: -2,
                    offset: Offset(0, 5),
                  ),
                ],
              ),
              child: const CustomPaint(
                size: Size(32, 32),
                painter: _ChatGlyphPainter(),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// White dialogue silhouette with three dots, drawn as scalable vector strokes.
class _ChatGlyphPainter extends CustomPainter {
  const _ChatGlyphPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final scale = size.width / 32;
    canvas.save();
    canvas.scale(scale);
    final outline = Paint()
      ..color = const Color(0xFFFFFEF7)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.7
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final path = Path()
      ..moveTo(15.7, 3)
      ..cubicTo(23.3, 3, 29, 8.5, 29, 15.6)
      ..cubicTo(29, 22.8, 23.4, 28, 15.7, 28)
      ..quadraticBezierTo(12.1, 28, 9.5, 26.7)
      ..lineTo(3.3, 29)
      ..lineTo(5.4, 23.0)
      ..cubicTo(3.6, 20.9, 3, 18.5, 3, 15.6)
      ..cubicTo(3, 8.5, 8.7, 3, 15.7, 3)
      ..close();
    canvas.drawPath(path, outline);
    final dot = Paint()..color = const Color(0xFFFFFEF7);
    for (final x in [10.5, 16.0, 21.5]) {
      canvas.drawCircle(Offset(x, 15.7), 1.7, dot);
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _ChatGlyphPainter oldDelegate) => false;
}
