part of '../dashboard_screen.dart';

// ── GMI Card ──────────────────────────────────────────────────────────────────

class _GMICard extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<LogEntryData> prevLogs;
  final int range;
  const _GMICard({required this.logs, required this.prevLogs, required this.range});

  /// Mirror of backend AnalyticalKPIs.gmi_confidence (ADA thresholds).
  static String? _confidence(List<LogEntryData> logs) {
    if (logs.length < 5) return null;
    final days = logs.map((e) {
      final d = e.loggedAt ?? e.createdAt;
      return '${d.year}-${d.month}-${d.day}';
    }).toSet().length;
    if (days >= 14 && logs.length >= 50) return 'high';
    if (days >= 7  || logs.length >= 25) return 'medium';
    return 'low';
  }

  static int _daysWithData(List<LogEntryData> logs) => logs.map((e) {
    final d = e.loggedAt ?? e.createdAt;
    return '${d.year}-${d.month}-${d.day}';
  }).toSet().length;

  @override
  Widget build(BuildContext context) {
    final gmi        = ClinicalEngine.calcGMI(logs);
    final mean       = ClinicalEngine.calcMean(logs);
    final confidence = _confidence(logs);
    final daysCount  = _daysWithData(logs);
    final spots = logs.reversed.toList().asMap().entries
        .where((e) => e.key % math.max(1, logs.length ~/ 20) == 0)
        .map((e) => FlSpot(e.key.toDouble(), e.value.bloodSugar))
        .toList();

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        CardHead(title: 'HbA1c estimée (GMI)', meta: '${range}j'),
        const SizedBox(height: 16),
        Builder(builder: (context) {
          final prevGmi  = ClinicalEngine.calcGMI(prevLogs);
          final delta    = gmi - prevGmi;
          final hasDelta = prevLogs.isNotEmpty && logs.isNotEmpty;
          return Row(crossAxisAlignment: CrossAxisAlignment.baseline, textBaseline: TextBaseline.alphabetic, children: [
            Text(
              logs.isEmpty ? '--' : gmi.toStringAsFixed(1),
              style: TextStyle(fontSize: 60, fontWeight: FontWeight.w800, color: AminaTheme.textPrimary(context), letterSpacing: -2, height: 0.9),
            ),
            const Text('%', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: AminaTheme.ink400)),
            if (hasDelta) ...[
              const SizedBox(width: 10),
              // GMI: lower is better → negative delta = positive (green)
              _DeltaChip(
                label: '${delta >= 0 ? '+' : ''}${delta.toStringAsFixed(1)} pt',
                positive: delta <= 0,
              ),
            ],
          ]);
        }),
        if (logs.isNotEmpty) ...[
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'Moy. ${mean.toStringAsFixed(0)} mg/dL · ${logs.length} mesures · ${daysCount}j',
              style: TextStyle(fontSize: 11, color: AminaTheme.textSecondary(context)),
            ),
          ),
          if (confidence == 'low' || confidence == 'medium')
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: _GmiConfidenceBadge(confidence: confidence!),
            ),
        ],
        const SizedBox(height: 14),
        if (spots.length >= 2)
          SizedBox(height: 44, child: LineChart(LineChartData(
            gridData: const FlGridData(show: false),
            titlesData: const FlTitlesData(show: false),
            borderData: FlBorderData(show: false),
            lineBarsData: [LineChartBarData(
              spots: spots, isCurved: true, curveSmoothness: 0.4,
              color: AminaTheme.teal500, barWidth: 2,
              isStrokeCapRound: true,
              dotData: const FlDotData(show: false),
              belowBarData: BarAreaData(show: true, gradient: LinearGradient(
                colors: [AminaTheme.teal500.withValues(alpha: 0.14), AminaTheme.teal500.withValues(alpha: 0.0)],
                begin: Alignment.topCenter, end: Alignment.bottomCenter,
              )),
            )],
          )))
        else
          SizedBox(height: 44, child: Center(child: Text('Données insuffisantes', style: TextStyle(fontSize: 11, color: AminaTheme.textSecondary(context))))),
      ]),
    );
  }
}

/// Small inline badge displayed below GMI value when confidence is not "high".
/// "medium" → blue info chip, "low" → amber warning chip.
class _GmiConfidenceBadge extends StatelessWidget {
  final String confidence; // "medium" | "low"
  const _GmiConfidenceBadge({required this.confidence});

  @override
  Widget build(BuildContext context) {
    final isLow   = confidence == 'low';
    final color   = isLow ? AminaTheme.ambre500 : const Color(0xFF3B82F6);
    final bgColor = isLow
        ? AminaTheme.ambre500.withValues(alpha: 0.12)
        : const Color(0xFF3B82F6).withValues(alpha: 0.10);
    final icon    = isLow ? Icons.warning_amber_rounded : Icons.info_outline_rounded;
    final label   = isLow
        ? 'Peu de données — estimation indicative'
        : 'Basé sur moins de 14 jours — indicatif';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: bgColor, borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: color),
        const SizedBox(width: 4),
        Text(label, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: color)),
      ]),
    );
  }
}
