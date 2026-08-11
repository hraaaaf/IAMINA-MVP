part of '../dashboard_screen.dart';

// ── Hero Live (mesure fraîche, <90 min) ───────────────────────────────────────

class _HeroLive extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final double low, high;

  const _HeroLive({
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
  });

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

  double _displayValue(double raw) => unit == 'mmol/L' ? raw / 18.0 : raw;

  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    final latest = logs.isNotEmpty ? logs.first : null;
    final value = latest == null ? 0.0 : _displayValue(latest.bloodSugar);
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
            top: -68,
            end: -56,
            child: Container(
              width: 230,
              height: 230,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    Colors.white.withValues(alpha: 0.13),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          Positioned.fill(child: CustomPaint(painter: _DotsPainter())),
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 22, 22, 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _HeroBadge(label: copy.latestReading),
                    const Spacer(),
                    Text(
                      minutesAgo == 0 ? copy.justNow : copy.minutesAgo(minutesAgo),
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.62),
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      flex: 5,
                      child: FittedBox(
                        fit: BoxFit.scaleDown,
                        alignment: AlignmentDirectional.centerStart,
                        child: _MeasurementValue(
                          value: value,
                          unit: unit,
                          trend: trend,
                          trendUp: trendUp,
                          compact: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      flex: 6,
                      child: SizedBox(
                        height: 88,
                        child: _HeroSparkline(
                          logs: logs,
                          low: low,
                          high: high,
                        ),
                      ),
                    ),
                  ],
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
    final displayValue = value > 0
        ? value.toStringAsFixed(unit == 'mmol/L' ? 1 : 0)
        : '--';
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          '\u2066$displayValue\u2069',
          style: TextStyle(
            color: Colors.white,
            fontSize: compact ? 62 : 88,
            fontWeight: FontWeight.w800,
            height: 0.86,
            letterSpacing: compact ? -2.3 : -4,
          ),
        ),
        const SizedBox(width: 7),
        Padding(
          padding: EdgeInsets.only(bottom: compact ? 5 : 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '\u2066$unit\u2069',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.72),
                  fontSize: compact ? 12 : 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              if (trend != null) ...[
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(99),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        trendUp ? Icons.arrow_upward : Icons.arrow_downward,
                        color: const Color(0xFF8FF3D4),
                        size: 10,
                      ),
                      const SizedBox(width: 3),
                      Text(
                        '\u2066${trend!}\u2069',
                        style: const TextStyle(
                          color: Color(0xFF8FF3D4),
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
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
