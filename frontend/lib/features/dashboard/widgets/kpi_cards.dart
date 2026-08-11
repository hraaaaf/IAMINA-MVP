part of '../dashboard_screen.dart';

// ── Metric Row ────────────────────────────────────────────────────────────────

class _MetricRow extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<LogEntryData> prevLogs;
  final double low, high;
  final int range;

  const _MetricRow({
    required this.logs,
    required this.prevLogs,
    required this.low,
    required this.high,
    required this.range,
  });

  int _daysWithData() => logs
      .map((entry) {
        final date = entry.loggedAt ?? entry.createdAt;
        return '${date.year}-${date.month}-${date.day}';
      })
      .toSet()
      .length;

  @override
  Widget build(BuildContext context) {
    final isWide = MediaQuery.of(context).size.width >= 900;
    if (isWide) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: _TIRCard(
              logs: logs,
              prevLogs: prevLogs,
              low: low,
              high: high,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: _GMICard(logs: logs, prevLogs: prevLogs, range: range),
          ),
          const SizedBox(width: 14),
          Expanded(child: _CVCard(logs: logs, prevLogs: prevLogs)),
        ],
      );
    }

    final copy = AuditedPageCopy.of(context);
    final l10n = copy.l10n;
    final tir = ClinicalEngine.calcTIR(logs, low, high);
    final cv = ClinicalEngine.calcCV(logs);
    final daysWithData = _daysWithData();
    final gmiEligible = daysWithData >= 14 && logs.length >= 50;
    final gmi = gmiEligible ? ClinicalEngine.calcGMI(logs) : null;

    return ClinicalCard(
      padding: const EdgeInsets.fromLTRB(16, 15, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: AminaTheme.teal50,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: const Icon(
                  Icons.monitor_heart_outlined,
                  color: AminaTheme.teal600,
                  size: 17,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
                decoration: BoxDecoration(
                  color: AminaTheme.subtleBg(context),
                  borderRadius: BorderRadius.circular(99),
                  border: Border.all(color: AminaTheme.divider(context)),
                ),
                child: Text(
                  '$range ${copy.dayShort}',
                  style: TextStyle(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  child: _CompactMetricCell(
                    icon: Icons.timelapse_rounded,
                    label: copy.readingsInRange,
                    value: logs.isEmpty ? '--' : '$tir',
                    suffix: '%',
                    accent: AminaTheme.teal600,
                  ),
                ),
                VerticalDivider(
                  width: 18,
                  thickness: 1,
                  color: AminaTheme.divider(context),
                ),
                Expanded(
                  child: _CompactMetricCell(
                    icon: Icons.local_fire_department_outlined,
                    label: l10n.dashboardGmiEstimated,
                    value: gmi == null ? '--' : gmi.toStringAsFixed(1),
                    suffix: gmi == null ? '' : '%',
                    accent: AminaTheme.teal600,
                  ),
                ),
                VerticalDivider(
                  width: 18,
                  thickness: 1,
                  color: AminaTheme.divider(context),
                ),
                Expanded(
                  child: _CompactMetricCell(
                    icon: Icons.show_chart_rounded,
                    label: l10n.dashboardCvTitle,
                    value: cv == 0 ? '--' : cv.toStringAsFixed(0),
                    suffix: cv == 0 ? '' : '%',
                    accent: cv > 0 && cv < 36
                        ? AminaTheme.teal600
                        : AminaTheme.warningOrange,
                  ),
                ),
              ],
            ),
          ),
          if (!gmiEligible && logs.isNotEmpty) ...[
            const SizedBox(height: 13),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 9),
              decoration: BoxDecoration(
                color: AminaTheme.ambre50,
                borderRadius: BorderRadius.circular(11),
                border: Border.all(
                  color: AminaTheme.ambre500.withValues(alpha: 0.22),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.info_outline_rounded,
                    size: 14,
                    color: AminaTheme.ambre700,
                  ),
                  const SizedBox(width: 7),
                  Expanded(
                    child: Text(
                      l10n.dashboardGmiLimitedCoverage,
                      style: const TextStyle(
                        fontSize: 10.5,
                        color: AminaTheme.ambre700,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _CompactMetricCell extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String suffix;
  final Color accent;

  const _CompactMetricCell({
    required this.icon,
    required this.label,
    required this.value,
    required this.suffix,
    required this.accent,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 31,
          height: 31,
          decoration: BoxDecoration(
            color: accent.withValues(alpha: 0.09),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: accent, size: 16),
        ),
        const SizedBox(height: 9),
        Text(
          label,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            fontSize: 10.5,
            height: 1.18,
            fontWeight: FontWeight.w600,
            color: AminaTheme.textSecondary(context),
          ),
        ),
        const SizedBox(height: 5),
        FittedBox(
          fit: BoxFit.scaleDown,
          alignment: AlignmentDirectional.centerStart,
          child: RichText(
            text: TextSpan(
              children: [
                TextSpan(
                  text: value,
                  style: TextStyle(
                    color: AminaTheme.textPrimary(context),
                    fontSize: 28,
                    height: 1,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -1.0,
                  ),
                ),
                if (suffix.isNotEmpty)
                  TextSpan(
                    text: suffix,
                    style: TextStyle(
                      color: AminaTheme.textSecondary(context),
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

// ── Delta chip ────────────────────────────────────────────────────────────────

class _DeltaChip extends StatelessWidget {
  final String label;
  final bool positive;
  const _DeltaChip({required this.label, required this.positive});

  @override
  Widget build(BuildContext context) {
    final color = positive ? AminaTheme.teal500 : AminaTheme.dangerRed;
    final bg = positive ? AminaTheme.teal50 : AminaTheme.dangerBg;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(99),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            positive ? Icons.arrow_upward : Icons.arrow_downward,
            size: 9,
            color: color,
          ),
          const SizedBox(width: 3),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Legend dot ────────────────────────────────────────────────────────────────

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  final String value;
  const _LegendDot({
    required this.color,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) => Row(
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 5),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: AminaTheme.textSecondary(context),
              ),
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: AminaTheme.textPrimary(context),
            ),
          ),
        ],
      );
}
