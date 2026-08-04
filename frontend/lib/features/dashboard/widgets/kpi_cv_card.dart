part of '../dashboard_screen.dart';

// ── CV Card ───────────────────────────────────────────────────────────────────

class _CVCard extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<LogEntryData> prevLogs;
  const _CVCard({required this.logs, required this.prevLogs});

  @override
  Widget build(BuildContext context) {
    final cv     = ClinicalEngine.calcCV(logs);
    final isGood = cv < 36;

    List<FlSpot> computeCvSpots() {
      if (logs.isEmpty) return [];
      final sorted = List<LogEntryData>.from(logs)
        ..sort((a, b) => (a.loggedAt ?? a.createdAt).compareTo(b.loggedAt ?? b.createdAt));

      final Map<String, List<LogEntryData>> groups = {};
      for (final l in sorted) {
        final d = l.loggedAt ?? l.createdAt;
        final key = '${d.year}-${d.month}-${d.day}';
        groups.putIfAbsent(key, () => []).add(l);
      }

      final entries = groups.entries.toList();
      if (entries.length < 2) return [];

      return entries.asMap().entries.map((e) {
        final dailyLogs = e.value.value;
        final dailyCv   = ClinicalEngine.calcCV(dailyLogs);
        return FlSpot(e.key.toDouble(), dailyCv);
      }).toList();
    }

    final cvSpots     = computeCvSpots();
    final colorStatus = isGood ? AminaTheme.teal500 : AminaTheme.warningOrange;

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const CardHead(title: 'Variabilité (CV)', meta: '< 36% ADA'),
        const SizedBox(height: 16),
        Builder(builder: (context) {
          final prevCv   = ClinicalEngine.calcCV(prevLogs);
          final delta    = cv - prevCv;
          final hasDelta = prevLogs.isNotEmpty && logs.isNotEmpty && cv > 0;
          return Row(crossAxisAlignment: CrossAxisAlignment.baseline, textBaseline: TextBaseline.alphabetic, children: [
            Text(
              cv == 0 ? '--' : cv.toStringAsFixed(0),
              style: TextStyle(fontSize: 60, fontWeight: FontWeight.w800, color: AminaTheme.textPrimary(context), letterSpacing: -2, height: 0.9),
            ),
            const Text('%', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: AminaTheme.ink400)),
            if (hasDelta) ...[
              const SizedBox(width: 10),
              // CV: lower is better → negative delta = positive (green)
              _DeltaChip(
                label: '${delta >= 0 ? '+' : ''}${delta.abs().round()} pts',
                positive: delta <= 0,
              ),
            ],
          ]);
        }),
        const SizedBox(height: 14),
        if (cvSpots.length >= 2)
          SizedBox(
            height: 30,
            child: LineChart(LineChartData(
              gridData: const FlGridData(show: false),
              titlesData: const FlTitlesData(show: false),
              borderData: FlBorderData(show: false),
              lineBarsData: [LineChartBarData(
                spots: cvSpots,
                isCurved: true, curveSmoothness: 0.4,
                color: colorStatus, barWidth: 1.5,
                dotData: const FlDotData(show: false),
                belowBarData: BarAreaData(show: true, gradient: LinearGradient(
                  colors: [colorStatus.withValues(alpha: 0.15), colorStatus.withValues(alpha: 0.0)],
                  begin: Alignment.topCenter, end: Alignment.bottomCenter,
                )),
              )],
            )),
          ),
        const SizedBox(height: 14),
        Row(children: [
          SizedBox(
            width: 48, height: 48,
            child: Stack(alignment: Alignment.center, children: [
              CircularProgressIndicator(
                value: logs.isEmpty ? 0 : (cv / 100).clamp(0.0, 1.0),
                strokeWidth: 5,
                backgroundColor: AminaTheme.divider(context),
                valueColor: AlwaysStoppedAnimation<Color>(isGood ? AminaTheme.teal500 : AminaTheme.warningOrange),
                strokeCap: StrokeCap.round,
              ),
              Text(
                cv == 0 ? '--' : '${cv.toStringAsFixed(0)}%',
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: isGood ? AminaTheme.teal600 : AminaTheme.warningOrange),
              ),
            ]),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(
                isGood ? 'Stable' : 'Variable',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: isGood ? AminaTheme.teal600 : AminaTheme.warnFg),
              ),
              const SizedBox(height: 3),
              Text(
                isGood ? 'Objectif <36% atteint. Variabilité maîtrisée.' : 'Variabilité élevée. Objectif < 36%.',
                style: TextStyle(fontSize: 11, color: AminaTheme.textSecondary(context), height: 1.4),
              ),
            ]),
          ),
        ]),
      ]),
    );
  }
}
