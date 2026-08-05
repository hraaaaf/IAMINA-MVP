part of '../dashboard_screen.dart';

// ── GMI Card ──────────────────────────────────────────────────────────────────

class _GMICard extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<LogEntryData> prevLogs;
  final int range;

  const _GMICard({
    required this.logs,
    required this.prevLogs,
    required this.range,
  });

  static int _daysWithData(List<LogEntryData> values) => values.map((entry) {
    final date = entry.loggedAt ?? entry.createdAt;
    return '${date.year}-${date.month}-${date.day}';
  }).toSet().length;

  @override
  Widget build(BuildContext context) {
    final gmi = ClinicalEngine.calcGMI(logs);
    final mean = ClinicalEngine.calcMean(logs);
    final daysCount = _daysWithData(logs);
    final hasLimitedCoverage = daysCount < 14 || logs.length < 50;
    final spots = logs.reversed
        .toList()
        .asMap()
        .entries
        .where((entry) => entry.key % math.max(1, logs.length ~/ 20) == 0)
        .map((entry) => FlSpot(entry.key.toDouble(), entry.value.bloodSugar))
        .toList();

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CardHead(title: 'GMI estimée', meta: '$range j'),
          const SizedBox(height: 16),
          Builder(
            builder: (context) {
              final prevGmi = ClinicalEngine.calcGMI(prevLogs);
              final delta = gmi - prevGmi;
              final hasComparablePeriod =
                  prevLogs.isNotEmpty && logs.isNotEmpty;
              return Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    logs.isEmpty ? '--' : gmi.toStringAsFixed(1),
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
                  if (hasComparablePeriod) ...[
                    const SizedBox(width: 10),
                    _DeltaChip(
                      label:
                          '${delta >= 0 ? '+' : ''}${delta.toStringAsFixed(1)} pt',
                      positive: delta <= 0,
                    ),
                  ],
                ],
              );
            },
          ),
          if (logs.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              'Moyenne ${mean.toStringAsFixed(0)} mg/dL · ${logs.length} mesures · $daysCount jour${daysCount > 1 ? 's' : ''} de données',
              style: TextStyle(
                fontSize: 11,
                color: AminaTheme.textSecondary(context),
                height: 1.35,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 7),
              decoration: BoxDecoration(
                color: hasLimitedCoverage
                    ? AminaTheme.ambre50
                    : AminaTheme.teal50,
                borderRadius: BorderRadius.circular(9),
                border: Border.all(
                  color: hasLimitedCoverage
                      ? AminaTheme.ambre500.withValues(alpha: 0.25)
                      : AminaTheme.teal200,
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    hasLimitedCoverage
                        ? Icons.info_outline
                        : Icons.calculate_outlined,
                    size: 14,
                    color: hasLimitedCoverage
                        ? AminaTheme.ambre700
                        : AminaTheme.teal700,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      hasLimitedCoverage
                          ? 'Couverture limitée : moins de 14 jours ou 50 mesures. Résultat indicatif.'
                          : 'Calculée à partir de la moyenne glycémique disponible.',
                      style: TextStyle(
                        fontSize: 10.5,
                        color: hasLimitedCoverage
                            ? AminaTheme.ambre700
                            : AminaTheme.teal700,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Cette estimation ne remplace pas une HbA1c de laboratoire.',
              style: TextStyle(
                fontSize: 10.5,
                color: AminaTheme.textSecondary(context),
                height: 1.35,
              ),
            ),
          ],
          const SizedBox(height: 14),
          if (spots.length >= 2)
            SizedBox(
              height: 44,
              child: LineChart(
                LineChartData(
                  gridData: const FlGridData(show: false),
                  titlesData: const FlTitlesData(show: false),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      curveSmoothness: 0.4,
                      color: AminaTheme.teal500,
                      barWidth: 2,
                      isStrokeCapRound: true,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        gradient: LinearGradient(
                          colors: [
                            AminaTheme.teal500.withValues(alpha: 0.14),
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
            )
          else
            SizedBox(
              height: 44,
              child: Center(
                child: Text(
                  'Données insuffisantes',
                  style: TextStyle(
                    fontSize: 11,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
