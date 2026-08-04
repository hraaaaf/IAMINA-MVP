part of '../dashboard_screen.dart';

// ── Page Head ─────────────────────────────────────────────────────────────────

class _PageHead extends StatelessWidget {
  final int logCount;
  final int range;
  final bool isDesktop;
  const _PageHead({
    required this.logCount,
    required this.range,
    this.isDesktop = false,
  });

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final greeting = now.hour < 12
        ? 'Bonjour'
        : now.hour < 18
        ? 'Bon après-midi'
        : 'Bonsoir';
    return Padding(
      padding: EdgeInsets.only(
        top: isDesktop ? 32 : 16,
        bottom: isDesktop ? 4 : 0,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Builder(
            builder: (ctx) {
              final firstName = _HeroInsight._firstName();
              final salut = firstName.isNotEmpty
                  ? '$greeting, $firstName.'
                  : '$greeting !';
              return Text(
                salut,
                style: TextStyle(
                  fontSize: isDesktop ? 44 : 30,
                  fontWeight: FontWeight.w700,
                  color: AminaTheme.textPrimary(context),
                  letterSpacing: -1.0,
                  height: 1.05,
                ),
              );
            },
          ),
          const SizedBox(height: 8),
          Text(
            logCount > 0
                ? 'Voici ce qu\'IAmina a observé sur vos $range derniers jours.'
                : 'Chargez des données pour voir votre analyse IAmina.',
            style: TextStyle(
              fontSize: isDesktop ? 16 : 14,
              color: AminaTheme.textSecondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Hero Contextuel ───────────────────────────────────────────────────────────
// 3 modes : insight (matin) / live (post-repas, CGM) / tir (mid-day)

enum _HeroMode { live, tir, insight }

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
    final minutesSince = now
        .difference(latest.loggedAt ?? latest.createdAt)
        .inMinutes;
    if (minutesSince < 90) return _HeroMode.live;
    if (now.hour >= 11 && now.hour < 15) return _HeroMode.tir;
    return _HeroMode.insight;
  }

  @override
  Widget build(BuildContext context) {
    final mode = _resolveMode();
    return switch (mode) {
      _HeroMode.live => _HeroLive(logs: logs, unit: unit, range: range),
      _HeroMode.tir => _HeroTIR(logs: logs, low: low, high: high, range: range),
      _HeroMode.insight => _HeroInsight(logs: logs, range: range),
    };
  }
}
