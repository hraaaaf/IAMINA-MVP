import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class PremiumSlider extends StatelessWidget {
  final double value;
  final double min;
  final double max;
  final ValueChanged<double> onChanged;

  const PremiumSlider({
    super.key,
    required this.value,
    this.min = 30,
    this.max = 400,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SliderTheme(
          data: SliderThemeData(
            trackHeight: 12,
            activeTrackColor: Colors.transparent,
            inactiveTrackColor: Colors.transparent,
            thumbColor: Colors.white,
            overlayColor: AminaTheme.primaryTeal.withValues(alpha: 0.1),
            thumbShape: const PremiumThumbShape(),
            trackShape: const GradientTrackShape(),
          ),
          child: Slider(value: value, min: min, max: max, onChanged: onChanged),
        ),
        const SizedBox(height: 12),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildScaleText('30'),
              _buildScaleText('70'),
              _buildScaleText('130'),
              _buildScaleText('180'),
              _buildScaleText('400'),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildScaleText(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 10,
        fontWeight: FontWeight.w900,
        color: AminaTheme.textMuted,
        letterSpacing: 0.5,
      ),
    );
  }
}

class PremiumThumbShape extends SliderComponentShape {
  const PremiumThumbShape();

  @override
  Size getPreferredSize(bool isEnabled, bool isDiscrete) => const Size(36, 36);

  @override
  void paint(
    PaintingContext context,
    Offset center, {
    required Animation<double> activationAnimation,
    required Animation<double> enableAnimation,
    required bool isDiscrete,
    required TextPainter labelPainter,
    required RenderBox parentBox,
    required SliderThemeData sliderTheme,
    required TextDirection textDirection,
    required double value,
    required double textScaleFactor,
    required Size sizeWithOverflow,
  }) {
    final Canvas canvas = context.canvas;

    // Shadow
    final Path path = Path()
      ..addOval(Rect.fromCircle(center: center, radius: 18));
    canvas.drawShadow(path, Colors.black.withValues(alpha: 0.2), 8, true);

    // Outer Circle (White)
    final Paint paint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, 18, paint);

    // Border
    final Paint borderPaint = Paint()
      ..color = AminaTheme.surfaceWhite
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4;
    canvas.drawCircle(center, 18, borderPaint);
  }
}

class GradientTrackShape extends SliderTrackShape with BaseSliderTrackShape {
  const GradientTrackShape();

  @override
  void paint(
    PaintingContext context,
    Offset offset, {
    required RenderBox parentBox,
    required SliderThemeData sliderTheme,
    required Animation<double> enableAnimation,
    required TextDirection textDirection,
    required Offset thumbCenter,
    Offset? secondaryOffset,
    bool isDiscrete = false,
    bool isEnabled = false,
    double additionalActiveTrackHeight = 2,
  }) {
    final Rect trackRect = getPreferredRect(
      parentBox: parentBox,
      offset: offset,
      sliderTheme: sliderTheme,
      isEnabled: isEnabled,
      isDiscrete: isDiscrete,
    );

    final Paint gradientPaint = Paint()
      ..shader = const LinearGradient(
        colors: [
          Color(0xFFEF4444), // 0-15% (30-85.5) -> Approx 30-70 is Red/Amber
          Color(0xFFEF4444),
          Color(0xFFF59E0B),
          Color(0xFFF59E0B),
          Color(0xFF10B981),
          Color(0xFF10B981),
          Color(0xFFF59E0B),
          Color(0xFFF59E0B),
          Color(0xFFEF4444),
          Color(0xFFEF4444),
        ],
        stops: [0.0, 0.15, 0.15, 0.22, 0.22, 0.40, 0.40, 0.70, 0.70, 1.0],
      ).createShader(trackRect);

    final RRect rrect = RRect.fromRectAndRadius(
      trackRect,
      const Radius.circular(10),
    );
    context.canvas.drawRRect(rrect, gradientPaint);
  }
}
