part of '../dashboard_screen.dart';

// ── Chart Section ─────────────────────────────────────────────────────────────

class _ChartSection extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low, high;
  final String unit;
  const _ChartSection({required this.logs, required this.low, required this.high, required this.unit});

  /// Number of unique calendar days covered by [logs].
  int _uniqueDays() {
    final days = <String>{};
    for (final l in logs) {
      final t = l.loggedAt ?? l.createdAt;
      days.add('${t.year}-${t.month}-${t.day}');
    }
    return days.length;
  }

  @override
  Widget build(BuildContext context) {
    final isWide  = MediaQuery.of(context).size.width >= 900;
    final daySpan = _uniqueDays();

    final chart = isWide
        ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(flex: 8, child: GlucoseChartWithEvents(logs: logs, low: low, high: high, unit: unit)),
            const SizedBox(width: 14),
            Expanded(flex: 4, child: _EventsPanel(logs: logs, low: low, high: high)),
          ])
        : Column(children: [
            GlucoseChartWithEvents(logs: logs, low: low, high: high, unit: unit),
            const SizedBox(height: 14),
            _EventsPanel(logs: logs, low: low, high: high),
          ]);

    // ADA recommendation: ≥ 14 days for a clinically meaningful AGP.
    if (daySpan < 14 && logs.isNotEmpty) {
      return Column(children: [
        _AgpSufficiencyBanner(daySpan: daySpan),
        const SizedBox(height: 10),
        chart,
      ]);
    }
    return chart;
  }
}

// ── AGP data-sufficiency banner ───────────────────────────────────────────────

class _AgpSufficiencyBanner extends StatelessWidget {
  final int daySpan;
  const _AgpSufficiencyBanner({required this.daySpan});

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8E1),   // amber 50
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFFE082)), // amber 200
      ),
      child: Row(children: [
        const Icon(Icons.info_outline, size: 16, color: Color(0xFFF9A825)),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            l10n.dashboardAgpSufficiency(daySpan),
            style: const TextStyle(fontSize: 12, color: Color(0xFF6D4C00), height: 1.4),
          ),
        ),
      ]),
    );
  }
}

class _EventsPanel extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low, high;
  const _EventsPanel({required this.logs, required this.low, required this.high});

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    final hypo  = logs.where((l) => l.bloodSugar < low).length;
    final hyper = logs.where((l) => l.bloodSugar > high).length;
    final inTgt = logs.where((l) => l.bloodSugar >= low && l.bloodSugar <= high).length;

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        CardHead(title: l10n.dashboardKeyEvents),
        const SizedBox(height: 14),
        _EventRow(icon: Icons.check_circle_outline, color: AminaTheme.goodFg,   bg: AminaTheme.goodBg,   label: l10n.dashboardInTarget,       count: inTgt, total: logs.length),
        const SizedBox(height: 10),
        _EventRow(icon: Icons.arrow_upward,         color: AminaTheme.warnFg,   bg: AminaTheme.warnBg,   label: l10n.dashboardHyperglycemia, count: hyper, total: logs.length),
        const SizedBox(height: 10),
        _EventRow(icon: Icons.arrow_downward,       color: AminaTheme.dangerFg, bg: AminaTheme.dangerBg, label: l10n.dashboardHypoglycemia,  count: hypo,  total: logs.length),
        const SizedBox(height: 14),
        Divider(color: AminaTheme.divider(context), height: 1),
        const SizedBox(height: 12),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(l10n.dashboardTotalMeasurements, style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),
          Text('${logs.length}', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AminaTheme.textPrimary(context))),
        ]),
      ]),
    );
  }
}

class _EventRow extends StatelessWidget {
  final IconData icon;
  final Color color, bg;
  final String label;
  final int count, total;
  const _EventRow({required this.icon, required this.color, required this.bg, required this.label, required this.count, required this.total});

  @override
  Widget build(BuildContext context) {
    final pct = total > 0 ? ((count / total) * 100).round() : 0;
    return Row(children: [
      Container(width: 30, height: 30, decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(9)),
        child: Icon(icon, size: 14, color: color)),
      const SizedBox(width: 10),
      Expanded(child: Text(label, style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context)))),
      Text('$count', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: color)),
      Text(' ($pct%)', style: TextStyle(fontSize: 11, color: AminaTheme.textSecondary(context))),
    ]);
  }
}
