part of '../dashboard_screen.dart';

// ── CV Card ───────────────────────────────────────────────────────────────────

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
    final isBelowGeneralReference = cv > 0 && cv < 36;
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
        final dailyLogs = entry.value.value;
        final dailyCv = ClinicalEngine.calcCV(dailyLogs);
        return FlSpot(entry.key.toDouble(), dailyCv);
      }).toList();
    }

    final cvSpots = computeCvSpots();
    final colorStatus = isBelowGeneralReference
        ? AminaTheme.teal500
        : AminaTheme.warningOrange;

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CardHead(
            title: l10n.dashboardCvTitle,
            meta: l10n.dashboardCvReferenceShort,
          ),
          const SizedBox(height: 16),
          Builder(
            builder: (context) {
              final prevCv = ClinicalEngine.calcCV(prevLogs);
              final delta = cv - prevCv;
              final hasComparablePeriod =
                  prevLogs.isNotEmpty && logs.isNotEmpty && cv > 0;
              return Row(
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
                  if (hasComparablePeriod) ...[
                    const SizedBox(width: 10),
                    _DeltaChip(
                      label:
                          '${delta >= 0 ? '+' : ''}${delta.toStringAsFixed(0)} pts',
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
              l10n.dashboardMeasurementCoverage(
                logs.length,
                daysWithData,
              ),
              style: TextStyle(
                fontSize: 11,
                color: AminaTheme.textSecondary(context),
              ),
            ),
          ],
          const SizedBox(height: 14),
          if (cvSpots.length >= 2)
            SizedBox(
              height: 30,
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
                      color: colorStatus,
                      barWidth: 1.5,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        gradient: LinearGradient(
                          colors: [
                            colorStatus.withValues(alpha: 0.15),
                            colorStatus.withValues(alpha: 0.0),
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
          const SizedBox(height: 14),
          Row(
            children: [
              SizedBox(
                width: 48,
                height: 48,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    CircularProgressIndicator(
                      value: logs.isEmpty ? 0 : (cv / 100).clamp(0.0, 1.0),
                      strokeWidth: 5,
                      backgroundColor: AminaTheme.divider(context),
                      valueColor: AlwaysStoppedAnimation<Color>(colorStatus),
                      strokeCap: StrokeCap.round,
                    ),
                    Text(
                      cv == 0 ? '--' : '${cv.toStringAsFixed(0)}%',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: colorStatus,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      cv == 0
                          ? l10n.dashboardInsufficientData
                          : isBelowGeneralReference
                          ? l10n.dashboardCvBelowReference
                          : l10n.dashboardCvAboveReference,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: cv == 0
                            ? AminaTheme.textSecondary(context)
                            : colorStatus,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      l10n.dashboardCvReferenceExplanation,
                      style: TextStyle(
                        fontSize: 11,
                        color: AminaTheme.textSecondary(context),
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
