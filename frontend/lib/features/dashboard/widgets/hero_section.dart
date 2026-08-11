part of '../dashboard_screen.dart';

// ── Page Head ─────────────────────────────────────────────────────────────────

class _PageHead extends StatelessWidget {
  final int logCount;
  final int range;
  final bool isDesktop;
  const _PageHead({required this.logCount, required this.range, this.isDesktop = false});

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final copy = AuditedPageCopy.of(context);
    return Padding(
      padding: EdgeInsets.only(top: isDesktop ? 32 : 18, bottom: isDesktop ? 4 : 2),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Builder(builder: (ctx) {
            final firstName = _HeroInsight._firstName();
            final salut = copy.greeting(now.hour, firstName);
            return Text(
              salut,
              style: TextStyle(
                fontSize: isDesktop ? 44 : 31,
                fontWeight: FontWeight.w700,
                color: AminaTheme.textPrimary(context),
                letterSpacing: -1.1,
                height: 1.04,
              ),
            );
          }),
          const SizedBox(height: 7),
          Text(
            logCount > 0 ? copy.observation(range) : copy.emptyAnalysis,
            style: TextStyle(
              fontSize: isDesktop ? 16 : 14,
              color: AminaTheme.textSecondary(context),
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Hero Contextuel ───────────────────────────────────────────────────────────
// A fresh measurement gets a live state; otherwise the latest measurement
// anchors a longitudinal summary. TIR stays in the metric block below so the
// first viewport does not repeat the same KPI twice.

enum _HeroMode { live, insight }

class _HeroContextual extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final double low, high;
  final int range;

  const _HeroContextual({
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
    required this.range,
  });

  _HeroMode _resolveMode() {
    final now = DateTime.now();
    if (logs.isEmpty) return _HeroMode.insight;
    final latest = logs.first;
    final minutesSince = now.difference(latest.loggedAt ?? latest.createdAt).inMinutes;
    return minutesSince >= 0 && minutesSince < 90
        ? _HeroMode.live
        : _HeroMode.insight;
  }

  @override
  Widget build(BuildContext context) {
    final mode = _resolveMode();
    return switch (mode) {
      _HeroMode.live => _HeroLive(
          logs: logs,
          unit: unit,
          low: low,
          high: high,
        ),
      _HeroMode.insight => _HeroInsight(
          logs: logs,
          unit: unit,
          low: low,
          high: high,
          range: range,
        ),
    };
  }
}
