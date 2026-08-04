part of '../dashboard_screen.dart';

// ── Recent Entries ────────────────────────────────────────────────────────────

class _RecentEntries extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final double low, high;
  final bool isDesktop;
  const _RecentEntries({
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
    this.isDesktop = false,
  });

  @override
  Widget build(BuildContext context) {
    final recent = logs.take(isDesktop ? 10 : 5).toList();
    if (recent.isEmpty) return const SizedBox.shrink();

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(child: CardHead(title: 'Journal · Aujourd\'hui')),
              GestureDetector(
                onTap: () => GoRouter.of(context).go('/journal'),
                child: const Text(
                  'Voir tout →',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AminaTheme.teal600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...recent.map(
            (log) => _LogRow(
              log: log,
              unit: unit,
              low: low,
              high: high,
              isDesktop: isDesktop,
            ),
          ),
        ],
      ),
    );
  }
}

class _LogRow extends StatelessWidget {
  final LogEntryData log;
  final String unit;
  final double low, high;
  final bool isDesktop;
  const _LogRow({
    required this.log,
    required this.unit,
    required this.low,
    required this.high,
    this.isDesktop = false,
  });

  Color _valueColor(double v) {
    if (v < low) return AminaTheme.dangerRed;
    if (v > high) return AminaTheme.warningOrange;
    return AminaTheme.teal600;
  }

  @override
  Widget build(BuildContext context) {
    final time = DateFormat.Hm().format(log.loggedAt ?? log.createdAt);
    final val = log.bloodSugar;
    final meal = log.mealType ?? '';
    final iconSize = isDesktop ? 44.0 : 36.0;
    final nameFontSize = isDesktop ? 15.0 : 13.0;
    final timeFontSize = isDesktop ? 12.0 : 11.0;
    final valFontSize = isDesktop ? 22.0 : 18.0;
    final unitFontSize = isDesktop ? 11.0 : 10.0;

    return Padding(
      padding: EdgeInsets.symmetric(vertical: isDesktop ? 10 : 8),
      child: Row(
        children: [
          Container(
            width: iconSize,
            height: iconSize,
            decoration: BoxDecoration(
              color: AminaTheme.subtleBg(context),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(
                _mealEmoji(meal),
                style: TextStyle(fontSize: isDesktop ? 20 : 16),
              ),
            ),
          ),
          SizedBox(width: isDesktop ? 16 : 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  meal.isNotEmpty ? meal : 'Mesure',
                  style: TextStyle(
                    fontSize: nameFontSize,
                    fontWeight: FontWeight.w600,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
                Text(
                  time,
                  style: TextStyle(
                    fontSize: timeFontSize,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                val.toStringAsFixed(0),
                style: TextStyle(
                  fontSize: valFontSize,
                  fontWeight: FontWeight.w800,
                  color: _valueColor(val),
                  letterSpacing: -0.5,
                ),
              ),
              Text(
                unit,
                style: TextStyle(
                  fontSize: unitFontSize,
                  color: AminaTheme.textSecondary(context),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _mealEmoji(String type) {
    return switch (type) {
      'Petit-déjeuner' => '🥐',
      'Déjeuner' => '🥗',
      'Dîner' => '🍽️',
      'En-cas' => '🍎',
      'À jeun' => '☕',
      _ => '💧',
    };
  }
}
