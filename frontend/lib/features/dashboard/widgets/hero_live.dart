part of '../dashboard_screen.dart';

// ── Hero Live (après repas, <90min) ──────────────────────────────────────────

class _HeroLive extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final int range;
  const _HeroLive({
    required this.logs,
    required this.unit,
    required this.range,
  });

  /// Calcule la tendance réelle : delta mg/dL sur 30 min entre les 2 dernières mesures.
  String? _trend() {
    if (logs.length < 2) return null;
    final a = logs[0];
    final b = logs[1];
    final dt = (a.loggedAt ?? a.createdAt)
        .difference(b.loggedAt ?? b.createdAt)
        .inMinutes;
    if (dt == 0) return null;
    final delta = a.bloodSugar - b.bloodSugar;
    if (delta.abs() < 5) return null; // stable
    final per30 = (delta / dt * 30).round();
    return '${per30 >= 0 ? '+' : ''}$per30 / 30 min';
  }

  bool _isTrendUp() {
    if (logs.length < 2) return true;
    return logs[0].bloodSugar >= logs[1].bloodSugar;
  }

  @override
  Widget build(BuildContext context) {
    final latest = logs.isNotEmpty ? logs.first : null;
    final val = latest?.bloodSugar ?? 0;
    final minutesAgo = latest != null
        ? DateTime.now()
              .difference(latest.loggedAt ?? latest.createdAt)
              .inMinutes
        : 0;
    final mealLabel = latest?.mealType?.isNotEmpty == true
        ? latest!.mealType!
        : null;
    final insulin =
        latest?.insulinUnits != null && (latest!.insulinUnits ?? 0) > 0
        ? '${latest.insulinUnits!.toStringAsFixed(latest.insulinUnits! == latest.insulinUnits!.truncateToDouble() ? 0 : 1)}u rapide'
        : null;
    final trend = _trend();
    final trendUp = _isTrendUp();

    return ClipRRect(
      borderRadius: BorderRadius.circular(AminaTheme.radius3XL),
      child: Stack(
        children: [
          Positioned.fill(
            child: Container(decoration: AminaTheme.heroCardDecoration()),
          ),
          Positioned(
            top: -50,
            right: -50,
            child: Container(
              width: 220,
              height: 220,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    Colors.white.withValues(alpha: 0.14),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          Positioned.fill(child: CustomPaint(painter: _DotsPainter())),
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _HeroBadge(label: 'DERNIÈRE MESURE'),
                const SizedBox(height: 18),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      val > 0 ? val.toStringAsFixed(0) : '--',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 88,
                        fontWeight: FontWeight.w800,
                        height: 0.85,
                        letterSpacing: -4,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            unit,
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.72),
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          if (trend != null) ...[
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 3,
                              ),
                              decoration: BoxDecoration(
                                color: Colors.amber.withValues(alpha: 0.22),
                                borderRadius: BorderRadius.circular(99),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    trendUp
                                        ? Icons.arrow_upward
                                        : Icons.arrow_downward,
                                    color: const Color(0xFFFCD34D),
                                    size: 10,
                                  ),
                                  const SizedBox(width: 3),
                                  Text(
                                    trend,
                                    style: const TextStyle(
                                      color: Color(0xFFFCD34D),
                                      fontSize: 11,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    const Spacer(),
                    Padding(
                      padding: const EdgeInsets.only(bottom: 14),
                      child: _AnimatedEcg(
                        color: Colors.white.withValues(alpha: 0.75),
                        width: 140,
                        height: 32,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  minutesAgo == 0 ? 'à l\'instant' : 'il y a $minutesAgo min',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.65),
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 16),
                if (mealLabel != null || insulin != null)
                  Wrap(
                    spacing: 8,
                    children: [
                      if (mealLabel != null) _HeroChip(label: mealLabel),
                      if (insulin != null) _HeroChip(label: insulin),
                    ],
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
