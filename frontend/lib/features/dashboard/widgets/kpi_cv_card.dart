part of '../dashboard_screen.dart';

// ── Recorded CV Card ──────────────────────────────────────────────────────────
// P1-EVIDENCE: local journal rows can support a descriptive coefficient of
// variation, but not a normative CGM stability judgement without verified sensor
// coverage. The card therefore shows the recorded-row statistic only.
class _CVCard extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<LogEntryData> prevLogs;

  const _CVCard({required this.logs, required this.prevLogs});

  static int _daysWithData(List<LogEntryData> values) => values
      .map((entry) {
        final date = entry.loggedAt ?? entry.createdAt;
        return '${date.year}-${date.month}-${date.day}';
      })
      .toSet()
      .length;

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    final cv = ClinicalEngine.calcCV(logs);
    final daysWithData = _daysWithData(logs);

    List<FlSpot> computeCvSpots() {
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
        return FlSpot(
          entry.key.toDouble(),
          ClinicalEngine.calcCV(entry.value.value),
        );
      }).toList();
    }

    final cvSpots = computeCvSpots();

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CardHead(
            title: l10n.dashboardCvTitle,
            meta: l10n.dashboardMeasurementCoverage(logs.length, daysWithData),
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                cv == 0 ? '--' : cv.toStringAsFixed(0),
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
            ],
          ),
          const SizedBox(height: 8),
          Text(
            l10n.dashboardMeasurementCoverage(logs.length, daysWithData),
            style: TextStyle(
              fontSize: 11,
              color: AminaTheme.textSecondary(context),
              height: 1.35,
            ),
          ),
          const SizedBox(height: 14),
          if (cvSpots.length >= 2)
            SizedBox(
              height: 42,
              child: LineChart(
                LineChartData(
                  gridData: const FlGridData(show: false),
                  titlesData: const FlTitlesData(show: false),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: cvSpots,
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
            )
          else
            SizedBox(
              height: 42,
              child: Center(
                child: Text(
                  l10n.dashboardInsufficientData,
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
