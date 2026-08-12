part of '../dashboard_screen.dart';

// ── GMI Card ──────────────────────────────────────────────────────────────────
// P1-EVIDENCE: GMI is CGM-derived. Local journal rows do not carry a validated
// sensor wear-time/cadence contract, so this offline surface must fail closed
// instead of computing GMI from manual or mixed readings.
class _GMICard extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<LogEntryData> prevLogs;
  final int range;

  const _GMICard({
    required this.logs,
    required this.prevLogs,
    required this.range,
  });

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
    final daysCount = _daysWithData(logs);
    final mean = logs.isEmpty ? null : ClinicalEngine.calcMean(logs);

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CardHead(
            title: l10n.dashboardGmiEstimated,
            meta: '$range ${l10n.dayShort}',
          ),
          const SizedBox(height: 16),
          Text(
            '--',
            style: TextStyle(
              fontSize: 60,
              fontWeight: FontWeight.w800,
              color: AminaTheme.textPrimary(context),
              letterSpacing: -2,
              height: 0.9,
            ),
          ),
          const SizedBox(height: 8),
          if (mean != null)
            Text(
              l10n.dashboardGmiCoverage(
                mean.toStringAsFixed(0),
                logs.length,
                daysCount,
              ),
              style: TextStyle(
                fontSize: 11,
                color: AminaTheme.textSecondary(context),
                height: 1.35,
              ),
            ),
          const SizedBox(height: 10),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
            decoration: BoxDecoration(
              color: AminaTheme.ambre50,
              borderRadius: BorderRadius.circular(9),
              border: Border.all(
                color: AminaTheme.ambre500.withValues(alpha: 0.25),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.sensors_off_outlined,
                  size: 15,
                  color: AminaTheme.ambre700,
                ),
                const SizedBox(width: 7),
                Expanded(
                  child: Text(
                    l10n.dashboardInsufficientData,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AminaTheme.ambre700,
                      height: 1.35,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            l10n.dashboardGmiDisclaimer,
            style: TextStyle(
              fontSize: 10.5,
              color: AminaTheme.textSecondary(context),
              height: 1.35,
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            height: 44,
            child: Center(
              child: Icon(
                Icons.sensors_off_outlined,
                size: 24,
                color: AminaTheme.textSecondary(context),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
