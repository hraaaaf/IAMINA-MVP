import 'package:flutter/material.dart';

class EcgPainter extends CustomPainter {
  final double progress;
  final Color color;
  final double strokeWidth;

  EcgPainter({
    required this.progress,
    required this.color,
    this.strokeWidth = 2.0,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final path = Path();
    final width = size.width;
    final height = size.height;
    final midY = height / 2;

    // Define the ECG pattern relative to width
    // P-wave, QRS complex, T-wave
    const List<Offset> pattern = [
      Offset(0.0, 0.0), // Start
      Offset(0.1, 0.0), // Baseline
      Offset(0.15, -5.0), // P wave
      Offset(0.2, 0.0), // Baseline
      Offset(0.22, 2.0), // Q
      Offset(0.25, -20.0), // R
      Offset(0.28, 5.0), // S
      Offset(0.3, 0.0), // Baseline
      Offset(0.4, -8.0), // T wave
      Offset(0.5, 0.0), // End of one cycle
    ];

    double cycleWidth = width * 0.5; // Two cycles per width

    for (int i = 0; i < 3; i++) {
      // Draw 3 cycles to handle scrolling
      double xOffset = (i * cycleWidth) - (progress * cycleWidth);

      for (int j = 0; j < pattern.length; j++) {
        double px = xOffset + (pattern[j].dx * cycleWidth);
        double py = midY + pattern[j].dy;

        if (j == 0 && i == 0) {
          path.moveTo(px, py);
        } else if (j == 0) {
          path.lineTo(px, py);
        } else {
          path.lineTo(px, py);
        }
      }
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant EcgPainter oldDelegate) {
    return oldDelegate.progress != progress || oldDelegate.color != color;
  }
}

class AnimatedEcg extends StatefulWidget {
  final Color color;
  final double height;
  final Duration duration;

  const AnimatedEcg({
    super.key,
    this.color = Colors.white24,
    this.height = 40,
    this.duration = const Duration(seconds: 3),
  });

  @override
  State<AnimatedEcg> createState() => _AnimatedEcgState();
}

class _AnimatedEcgState extends State<AnimatedEcg>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: widget.duration)
      ..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          size: Size(double.infinity, widget.height),
          painter: EcgPainter(progress: _controller.value, color: widget.color),
        );
      },
    );
  }
}
