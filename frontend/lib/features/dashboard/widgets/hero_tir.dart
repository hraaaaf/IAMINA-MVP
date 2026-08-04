part of '../dashboard_screen.dart';

// ── Hero TIR (mi-journée) ─────────────────────────────────────────────────────

class _HeroTIR extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low, high;
  final int range;
  const _HeroTIR({
    required this.logs,
    required this.low,
    required this.high,
    required this.range,
  });

  @override
  Widget build(BuildContext context) {
    final tir = ClinicalEngine.calcTIR(logs, low, high);
    return ClipRRect(
      borderRadius: BorderRadius.circular(AminaTheme.radius3XL),
      child: Stack(
        children: [
          Container(
            width: double.infinity,
            decoration: AminaTheme.heroCardDecoration(),
          ),
          Positioned.fill(child: CustomPaint(painter: _DotsPainter())),
          Padding(
            padding: const EdgeInsets.all(24),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const _HeroBadge(label: 'TEMPS EN CIBLE · AUJOURD\'HUI'),
                      const SizedBox(height: 16),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.baseline,
                        textBaseline: TextBaseline.alphabetic,
                        children: [
                          Text(
                            '$tir',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 72,
                              fontWeight: FontWeight.w800,
                              height: 0.85,
                              letterSpacing: -3,
                            ),
                          ),
                          const Text(
                            '%',
                            style: TextStyle(
                              color: Colors.white70,
                              fontSize: 22,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        tir >= 70
                            ? '✓ Objectif ADA atteint'
                            : 'Objectif : ≥ 70%',
                        style: TextStyle(
                          color: tir >= 70
                              ? const Color(0xFF6EF0C4)
                              : Colors.amber.shade200,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 18),
                      _HeroOutlineBtn(
                        label: 'Voir le journal',
                        onTap: () => GoRouter.of(context).go('/journal'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
