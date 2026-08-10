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
  String? _trend(BuildContext context) {
    if (logs.length < 2) return null;
    final latest = logs[0];
    final previous = logs[1];
    final elapsedMinutes = (latest.loggedAt ?? latest.createdAt)
        .difference(previous.loggedAt ?? previous.createdAt)
        .inMinutes;
    if (elapsedMinutes == 0) return null;
    final delta = latest.bloodSugar - previous.bloodSugar;
    if (delta.abs() < 5) return null;
    final per30 = (delta / elapsedMinutes * 30).round();
    final signed = '${per30 >= 0 ? '+' : ''}$per30';
    return AuditedPageCopy.of(context).l10n.dashboardTrendPer30Minutes(signed);
  }

  bool _isTrendUp() {
    if (logs.length < 2) return true;
    return logs[0].bloodSugar >= logs[1].bloodSugar;
  }

  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    final latest = logs.isNotEmpty ? logs.first : null;
    final value = latest?.bloodSugar ?? 0;
    final minutesAgo = latest != null
        ? DateTime.now()
              .difference(latest.loggedAt ?? latest.createdAt)
              .inMinutes
        : 0;
    final rawMealLabel = latest?.mealType?.isNotEmpty == true
        ? latest!.mealType!
        : null;
    final mealLabel = rawMealLabel == null ? null : copy.meal(rawMealLabel);
    final insulin = latest?.insulinUnits != null &&
            (latest!.insulinUnits ?? 0) > 0
        ? AuditedPageCopy.of(context).l10n.dashboardRapidInsulin(
            '\u2066${latest.insulinUnits!.toStringAsFixed(latest.insulinUnits! == latest.insulinUnits!.truncateToDouble() ? 0 : 1)}\u2069',
          )
        : null;
    final trend = _trend(context);
    final trendUp = _isTrendUp();

    return ClipRRect(
      borderRadius: BorderRadius.circular(AminaTheme.radius3XL),
      child: Stack(
        children: [
          Positioned.fill(
            child: Container(decoration: AminaTheme.heroCardDecoration()),
          ),
          PositionedDirectional(
            top: -50,
            end: -50,
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
            child: LayoutBuilder(
              builder: (context, constraints) {
                final compact = constraints.maxWidth < 600;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _HeroBadge(label: copy.latestReading),
                    SizedBox(height: compact ? 14 : 18),
                    Row(
                      children: [
                        Expanded(
                          child: FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: AlignmentDirectional.centerStart,
                            child: _MeasurementValue(
                              value: value,
                              unit: unit,
                              trend: trend,
                              trendUp: trendUp,
                              compact: compact,
                            ),
                          ),
                        ),
                        if (!compact) ...[
                          const SizedBox(width: 20),
                          _AnimatedEcg(
                            color: Colors.white.withValues(alpha: 0.75),
                            width: 140,
                            height: 32,
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      minutesAgo == 0 ? copy.justNow : copy.minutesAgo(minutesAgo),
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.65),
                        fontSize: 12,
                      ),
                    ),
                    if (mealLabel != null || insulin != null) ...[
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          if (mealLabel != null) _HeroChip(label: mealLabel),
                          if (insulin != null) _HeroChip(label: insulin),
                        ],
                      ),
                    ],
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _MeasurementValue extends StatelessWidget {
  final double value;
  final String unit;
  final String? trend;
  final bool trendUp;
  final bool compact;

  const _MeasurementValue({
    required this.value,
    required this.unit,
    required this.trend,
    required this.trendUp,
    required this.compact,
  });

  @override
  Widget build(BuildContext context) {
    final displayValue = value > 0 ? value.toStringAsFixed(0) : '--';
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          '\u2066$displayValue\u2069',
          style: TextStyle(
            color: Colors.white,
            fontSize: compact ? 68 : 88,
            fontWeight: FontWeight.w800,
            height: 0.85,
            letterSpacing: compact ? -2.5 : -4,
          ),
        ),
        const SizedBox(width: 8),
        Padding(
          padding: EdgeInsets.only(bottom: compact ? 7 : 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '\u2066$unit\u2069',
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
                        trendUp ? Icons.arrow_upward : Icons.arrow_downward,
                        color: const Color(0xFFFCD34D),
                        size: 10,
                      ),
                      const SizedBox(width: 3),
                      Text(
                        '\u2066${trend!}\u2069',
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
      ],
    );
  }
}
