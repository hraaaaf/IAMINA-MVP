part of '../dashboard_screen.dart';

// ── TIR Card ──────────────────────────────────────────────────────────────────

class _TIRCard extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<LogEntryData> prevLogs;
  final double low, high;
  const _TIRCard({required this.logs, required this.prevLogs, required this.low, required this.high});

  @override
  Widget build(BuildContext context) {
    final tir      = ClinicalEngine.calcTIR(logs, low, high);
    final tirHigh  = ClinicalEngine.calcHigh(logs, high);
    final tirVHigh = ClinicalEngine.calcVeryHigh(logs);
    final tirLow   = ClinicalEngine.calcLow(logs, low);
    final tirVLow  = ClinicalEngine.calcVeryLow(logs);

    List<FlSpot> computeTirSpots() {
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
        final dailyTir  = ClinicalEngine.calcTIR(dailyLogs, low, high);
        return FlSpot(e.key.toDouble(), dailyTir);
      }).toList();
    }

    final tirSpots = computeTirSpots();

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const CardHead(title: 'Temps en cible', meta: '70–180'),
        const SizedBox(height: 16),
        Builder(builder: (context) {
          final prevTir  = ClinicalEngine.calcTIR(prevLogs, low, high);
          final delta    = tir - prevTir;
          final hasDelta = prevLogs.isNotEmpty && logs.isNotEmpty;
          return Row(crossAxisAlignment: CrossAxisAlignment.baseline, textBaseline: TextBaseline.alphabetic, children: [
            Text('$tir', style: TextStyle(fontSize: 60, fontWeight: FontWeight.w800, color: AminaTheme.textPrimary(context), letterSpacing: -2, height: 0.9)),
            const Text('%', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: AminaTheme.ink400)),
            if (hasDelta) ...[
              const SizedBox(width: 10),
              _DeltaChip(label: '${delta >= 0 ? '+' : ''}${delta.abs().round()} pts', positive: delta >= 0),
            ],
          ]);
        }),
        const SizedBox(height: 14),
        ClipRRect(
          borderRadius: BorderRadius.circular(99),
          child: SizedBox(height: 8, child: Row(children: [
            if (tirVLow > 0) Expanded(flex: tirVLow.round(), child: Container(color: const Color(0xFF3E5AA0))),
            if (tirLow > 0)  Expanded(flex: tirLow.round(),  child: Container(color: const Color(0xFF6A8ACB))),
            if (tir > 0)     Expanded(flex: tir.round(),     child: Container(color: AminaTheme.teal500)),
            if (tirHigh > 0) Expanded(flex: tirHigh.round(), child: Container(color: const Color(0xFFE4A85B))),
            if (tirVHigh > 0)Expanded(flex: tirVHigh.round(),child: Container(color: const Color(0xFFD46A5A))),
            if (logs.isEmpty) Expanded(child: Container(color: AminaTheme.ink200)),
          ])),
        ),
        const SizedBox(height: 12),
        if (tirSpots.length >= 2)
          SizedBox(
            height: 30,
            child: LineChart(LineChartData(
              gridData: const FlGridData(show: false),
              titlesData: const FlTitlesData(show: false),
              borderData: FlBorderData(show: false),
              lineBarsData: [LineChartBarData(
                spots: tirSpots,
                isCurved: true, curveSmoothness: 0.4,
                color: AminaTheme.teal500, barWidth: 1.5,
                dotData: const FlDotData(show: false),
                belowBarData: BarAreaData(show: true, gradient: LinearGradient(
                  colors: [AminaTheme.teal500.withValues(alpha: 0.15), AminaTheme.teal500.withValues(alpha: 0.0)],
                  begin: Alignment.topCenter, end: Alignment.bottomCenter,
                )),
              )],
            )),
          ),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(child: _LegendDot(color: AminaTheme.teal500, label: 'En cible', value: '$tir%')),
          Expanded(child: _LegendDot(color: const Color(0xFFE4A85B), label: 'Élevé', value: '$tirHigh%')),
        ]),
        const SizedBox(height: 4),
        Row(children: [
          Expanded(child: _LegendDot(color: const Color(0xFF6A8ACB), label: 'Bas', value: '$tirLow%')),
          Expanded(child: _LegendDot(color: const Color(0xFFD46A5A), label: 'Très élevé', value: '$tirVHigh%')),
        ]),
        const SizedBox(height: 12),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text('Objectif ADA · >70%', style: TextStyle(fontSize: 11, color: AminaTheme.textSecondary(context))),
          if (tir >= 70)
            const Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(Icons.check_circle_outline, size: 12, color: AminaTheme.teal500),
              SizedBox(width: 4),
              Text('Atteint', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AminaTheme.teal600)),
            ]),
        ]),
      ]),
    );
  }
}
