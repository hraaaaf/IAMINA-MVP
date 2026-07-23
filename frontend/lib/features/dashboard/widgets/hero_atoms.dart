part of '../dashboard_screen.dart';

// ── Hero atom widgets ─────────────────────────────────────────────────────────

class _HeroBadge extends StatelessWidget {
  final String label;
  const _HeroBadge({required this.label});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: Colors.white.withValues(alpha: 0.16),
      borderRadius: BorderRadius.circular(99),
    ),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.auto_awesome, color: Colors.white, size: 10),
      const SizedBox(width: 6),
      Text(label, style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.12)),
    ]),
  );
}

class _HeroChip extends StatelessWidget {
  final String label;
  const _HeroChip({required this.label});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(99)),
    child: Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 11, fontWeight: FontWeight.w500)),
  );
}

class _HeroFilledBtn extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _HeroFilledBtn({required this.label, required this.onTap});
  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(99),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.18), blurRadius: 12, offset: const Offset(0, 4))],
      ),
      child: Text(label, style: const TextStyle(color: AminaTheme.teal700, fontSize: 12, fontWeight: FontWeight.w700)),
    ),
  );
}

class _HeroOutlineBtn extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _HeroOutlineBtn({required this.label, required this.onTap});
  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.14),
        border: Border.all(color: Colors.white.withValues(alpha: 0.28)),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 12, fontWeight: FontWeight.w600)),
    ),
  );
}

// ── Dots ornament painter ─────────────────────────────────────────────────────

class _DotsPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = Colors.white.withValues(alpha: 0.07);
    const sx = 28.0, sy = 28.0;
    for (double x = sx / 2; x < size.width; x += sx) {
      for (double y = sy / 2; y < size.height; y += sy) {
        canvas.drawCircle(Offset(x, y), 1.2, paint);
      }
    }
  }
  @override
  bool shouldRepaint(_DotsPainter _) => false;
}
