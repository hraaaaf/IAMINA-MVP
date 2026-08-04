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
          Expanded(
            child: _CVCard(logs: logs, prevLogs: prevLogs),
          ),
        ],
      );
    }
    return Column(
      children: [
        _TIRCard(logs: logs, prevLogs: prevLogs, low: low, high: high),
        const SizedBox(height: 14),
        Row(
          children: [
            Expanded(
              child: _GMICard(logs: logs, prevLogs: prevLogs, range: range),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: _CVCard(logs: logs, prevLogs: prevLogs),
            ),
          ],
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
