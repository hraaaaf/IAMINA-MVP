part of '../dashboard_screen.dart';

// ── ECG Painter animé ─────────────────────────────────────────────────────────

class _EcgPainter extends CustomPainter {
  final double progress; // 0→1 animation
  final Color color;

  _EcgPainter({required this.progress, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2.0
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;

    final w = size.width;
    final h = size.height / 2;

    // Points ECG normalisés
    final pts = [
      Offset(0.0, h),
      Offset(0.35, h),
      Offset(0.42, h * 0.4),
      Offset(0.50, h * 1.6),
      Offset(0.58, h * 0.1),
      Offset(0.65, h),
      Offset(1.0, h),
    ].map((p) => Offset(p.dx * w, p.dy)).toList();

    // Longueur totale approximative
    double totalLen = 0;
    for (int i = 1; i < pts.length; i++) {
      totalLen += (pts[i] - pts[i - 1]).distance;
    }
    final target = totalLen * progress;

    final path = Path();
    path.moveTo(pts[0].dx, pts[0].dy);
    double drawn = 0;
    for (int i = 1; i < pts.length; i++) {
      final seg = (pts[i] - pts[i - 1]).distance;
      if (drawn + seg <= target) {
        path.lineTo(pts[i].dx, pts[i].dy);
        drawn += seg;
      } else {
        final t = (target - drawn) / seg;
        final x = pts[i - 1].dx + (pts[i].dx - pts[i - 1].dx) * t;
        final y = pts[i - 1].dy + (pts[i].dy - pts[i - 1].dy) * t;
        path.lineTo(x, y);
        break;
      }
    }
    canvas.drawPath(path, paint);

    // Dot à la position courante
    final pathMetrics = path.computeMetrics().toList();
    if (pathMetrics.isNotEmpty) {
      final tang = pathMetrics.last.getTangentForOffset(
        pathMetrics.last.length,
      );
      if (tang != null) {
        canvas.drawCircle(
          tang.position,
          3.5,
          Paint()
            ..color = color
            ..style = PaintingStyle.fill,
        );
      }
    }
  }

  @override
  bool shouldRepaint(_EcgPainter old) => old.progress != progress;
}

class _AnimatedEcg extends StatefulWidget {
  final Color color;
  final double width;
  final double height;
  const _AnimatedEcg({required this.color, this.width = 200, this.height = 32});
  @override
  State<_AnimatedEcg> createState() => _AnimatedEcgState();
}

class _AnimatedEcgState extends State<_AnimatedEcg>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2200),
    )..repeat();
    _anim = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) => CustomPaint(
        size: Size(widget.width, widget.height),
        painter: _EcgPainter(progress: _anim.value, color: widget.color),
      ),
    );
  }
}
