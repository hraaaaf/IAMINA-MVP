part of '../dashboard_screen.dart';

// ── Target-range Card ─────────────────────────────────────────────────────────

class _TIRCard extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<LogEntryData> prevLogs;
  final double low, high;
  const _TIRCard({
    required this.logs,
    required this.prevLogs,
    required this.low,
    required this.high,
  });

  int _daysWithData(List<LogEntryData> values) => values
      .map((entry) {
        final date = entry.loggedAt ?? entry.createdAt;
        return '${date.year}-${date.month}-${date.day}';
      })
      .toSet()
      .length;

  @override
  Widget build(BuildContext context) {
    final tir = ClinicalEngine.calcTIR(logs, low, high);
    final tirHigh = ClinicalEngine.calcHigh(logs, high);
    final tirVHigh = ClinicalEngine.calcVeryHigh(logs);
    final tirLow = ClinicalEngine.calcLow(logs, low);
    final tirVLow = ClinicalEngine.calcVeryLow(logs);
    final daysWithData = _daysWithData(logs);

    List<FlSpot> computeTirSpots() {
      if (logs.isEmpty) return [];
      final sorted = List<LogEntryData>.from(logs)
        ..sort(
          (a, b) =>
              (a.loggedAt ?? a.createdAt).compareTo(b.loggedAt ?? b.createdAt),
        );

      final Map<String, List<LogEntryData>> groups = {};
      for (final log in sorted) {
        final date = log.loggedAt ?? log.createdAt;
        final key = '${date.year}-${date.month}-${date.day}';
        groups.putIfAbsent(key, () => []).add(log);
      }

      final entries = groups.entries.toList();
      if (entries.length < 2) return [];

      return entries.asMap().entries.map((entry) {
        final dailyLogs = entry.value.value;
        final dailyTir = ClinicalEngine.calcTIR(dailyLogs, low, high);
        return FlSpot(entry.key.toDouble(), dailyTir);
      }).toList();
    }

    final tirSpots = computeTirSpots();

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CardHead(title: 'Mesures dans la cible', meta: 'Repère 70–180'),
          const SizedBox(height: 16),
          Builder(
            builder: (context) {
              final prevTir = ClinicalEngine.calcTIR(prevLogs, low, high);
              final delta = tir - prevTir;
              final hasDelta = prevLogs.isNotEmpty && logs.isNotEmpty;
              return Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    logs.isEmpty ? '--' : '$tir',
                    style: TextStyle(
                      fontSize: 60,
                      fontWeight: FontWeight.w800,
                      color: AminaTheme.textPrimary(context),
                      letterSpacing: -2,
                      height: 0.9,
                    ),
                  ),
                  const Text(
                    '%',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w600,
                      color: AminaTheme.ink400,
                    ),
                  ),
                  if (hasDelta) ...[
                    const SizedBox(width: 10),
                    _DeltaChip(
                      label: '${delta >= 0 ? '+' : ''}${delta.round()} pts',
                      positive: delta >= 0,
                    ),
                  ],
                ],
              );
            },
          ),
          if (logs.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              '${logs.length} mesures sur $daysWithData jour${daysWithData > 1 ? 's' : ''} · proportion de mesures, pas durée CGM',
              style: TextStyle(
                fontSize: 11,
                color: AminaTheme.textSecondary(context),
                height: 1.35,
              ),
            ),
          ],
          const SizedBox(height: 14),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: SizedBox(
              height: 8,
              child: Row(
                children: [
                  if (tirVLow > 0)
                    Expanded(
                      flex: tirVLow.round(),
                      child: Container(color: const Color(0xFF3E5AA0)),
                    ),
                  if (tirLow > 0)
                    Expanded(
                      flex: tirLow.round(),
                      child: Container(color: const Color(0xFF6A8ACB)),
                    ),
                  if (tir > 0)
                    Expanded(
                      flex: tir.round(),
                      child: Container(color: AminaTheme.teal500),
                    ),
                  if (tirHigh > 0)
                    Expanded(
                      flex: tirHigh.round(),
                      child: Container(color: const Color(0xFFE4A85B)),
                    ),
                  if (tirVHigh > 0)
                    Expanded(
                      flex: tirVHigh.round(),
                      child: Container(color: const Color(0xFFD46A5A)),
                    ),
                  if (logs.isEmpty)
                    Expanded(child: Container(color: AminaTheme.ink200)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          if (tirSpots.length >= 2)
            SizedBox(
              height: 30,
              child: LineChart(
                LineChartData(
                  gridData: const FlGridData(show: false),
                  titlesData: const FlTitlesData(show: false),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: tirSpots,
                      isCurved: true,
                      curveSmoothness: 0.4,
                      color: AminaTheme.teal500,
                      barWidth: 1.5,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        gradient: LinearGradient(
                          colors: [
                            AminaTheme.teal500.withValues(alpha: 0.15),
                            AminaTheme.teal500.withValues(alpha: 0.0),
                          ],
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _LegendDot(
                  color: AminaTheme.teal500,
                  label: 'Dans la cible',
                  value: '$tir%',
                ),
              ),
              Expanded(
                child: _LegendDot(
                  color: const Color(0xFFE4A85B),
                  label: 'Élevé',
                  value: '$tirHigh%',
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Expanded(
                child: _LegendDot(
                  color: const Color(0xFF6A8ACB),
                  label: 'Bas',
                  value: '$tirLow%',
                ),
              ),
              Expanded(
                child: _LegendDot(
                  color: const Color(0xFFD46A5A),
                  label: 'Très élevé',
                  value: '$tirVHigh%',
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Repère général : plus de 70 % des mesures dans 70–180 mg/dL. Votre cible personnelle peut être différente.',
            style: TextStyle(
              fontSize: 11,
              color: AminaTheme.textSecondary(context),
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}
