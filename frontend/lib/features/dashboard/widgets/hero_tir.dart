part of '../dashboard_screen.dart';

// ── Hero mesures dans la cible (mi-journée) ───────────────────────────────────

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
    final percentage = ClinicalEngine.calcTIR(logs, low, high);
    final daysWithData = logs
        .map((log) {
          final date = log.loggedAt ?? log.createdAt;
          return DateTime(date.year, date.month, date.day);
        })
        .toSet()
        .length;

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
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HeroBadge(label: 'MESURES DANS LA CIBLE · $range JOURS'),
                const SizedBox(height: 16),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      '$percentage',
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
                const SizedBox(height: 10),
                Text(
                  '${logs.length} mesures sur $daysWithData jour${daysWithData > 1 ? 's' : ''} · proportion de mesures, pas durée CGM',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.78),
                    fontSize: 12,
                    height: 1.35,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Repère général ≥ 70 % · votre cible personnelle peut être différente.',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.9),
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
    );
  }
}
