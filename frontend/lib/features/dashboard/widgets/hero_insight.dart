part of '../dashboard_screen.dart';

// ── Hero Insight (default / longitudinal) ─────────────────────────────────────

class _HeroInsight extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final double low, high;
  final int range;

  const _HeroInsight({
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
    required this.range,
  });

  /// Prénom de l'utilisateur connecté, ou chaîne vide pour les comptes anonymes.
  static String _firstName() {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null || user.isAnonymous) return '';
    final name = user.displayName ?? user.email ?? '';
    if (name.isEmpty) return '';
    return name
        .split(RegExp(r'[\s@.]'))
        .firstWhere((p) => p.isNotEmpty, orElse: () => '');
  }

  String _headline(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    if (logs.isEmpty) return l10n.dashboardInsightStart;
    final tir = ClinicalEngine.calcTIR(logs, low, high);
    final mean = ClinicalEngine.calcMean(logs);
    if (tir >= 80) return l10n.dashboardInsightStrong(tir.round(), range);
    if (tir >= 60) {
      return l10n.dashboardInsightProgress(tir.round(), mean.round());
    }
    return l10n.dashboardInsightNeedsFocus(range);
  }

  String _subtitle(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    if (logs.isEmpty) return l10n.dashboardInsightFirstMeasurement;
    final cv = ClinicalEngine.calcCV(logs);
    final discoveries = math.min(logs.length ~/ 20 + 1, 5);
    final stability = cv < 36
        ? l10n.dashboardVariabilityStable
        : l10n.dashboardVariabilityWatch;
    return l10n.dashboardInsightSummary(discoveries, stability, logs.length);
  }

  String _displayValue(double raw) {
    if (unit == 'mmol/L') return (raw / 18.0).toStringAsFixed(1);
    return raw.toStringAsFixed(0);
  }

  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    final l10n = copy.l10n;
    final desktop = MediaQuery.sizeOf(context).width >= 900;
    final latest = logs.isNotEmpty ? logs.first : null;
    final latestAt = latest == null ? null : (latest.loggedAt ?? latest.createdAt);
    final rawMeal = latest?.mealType?.trim();
    final meal = rawMeal == null || rawMeal.isEmpty ? '' : copy.meal(rawMeal);

    return ClipRRect(
      borderRadius: BorderRadius.circular(AminaTheme.radius3XL),
      child: Stack(
        children: [
          Positioned.fill(
            child: Container(decoration: AminaTheme.heroCardDecoration()),
          ),
          PositionedDirectional(
            top: -68,
            end: -56,
            child: Container(
              width: 230,
              height: 230,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    Colors.white.withValues(alpha: 0.13),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          Positioned.fill(child: CustomPaint(painter: _DotsPainter())),
          if (desktop)
            PositionedDirectional(
              end: -8,
              bottom: 10,
              child: _AnimatedEcg(
                color: Colors.white.withValues(alpha: 0.16),
                width: 260,
                height: 60,
              ),
            ),
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 22, 22, 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _HeroBadge(label: copy.latestReading),
                    const Spacer(),
                    if (latestAt != null)
                      Text(
                        DateFormat.Hm().format(latestAt),
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.62),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 18),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final veryCompact = constraints.maxWidth < 335;
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Expanded(
                          flex: 5,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (meal.isNotEmpty) ...[
                                Text(
                                  meal,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: Colors.white.withValues(alpha: 0.72),
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 7),
                              ],
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Flexible(
                                    child: FittedBox(
                                      fit: BoxFit.scaleDown,
                                      alignment: AlignmentDirectional.centerStart,
                                      child: Text(
                                        latest == null
                                            ? '--'
                                            : _displayValue(latest.bloodSugar),
                                        style: TextStyle(
                                          color: Colors.white,
                                          fontSize: veryCompact ? 56 : 68,
                                          fontWeight: FontWeight.w800,
                                          height: 0.88,
                                          letterSpacing: -2.7,
                                        ),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 7),
                                  Padding(
                                    padding: const EdgeInsets.only(bottom: 5),
                                    child: Text(
                                      unit,
                                      style: TextStyle(
                                        color: Colors.white.withValues(alpha: 0.72),
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          flex: 6,
                          child: SizedBox(
                            height: 88,
                            child: _HeroSparkline(
                              logs: logs,
                              low: low,
                              high: high,
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 18),
                if (desktop)
                  _HeroFilledBtn(
                    label: l10n.dashboardViewDiscoveries,
                    onTap: () => GoRouter.of(context).go('/summary'),
                  )
                else
                  Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: () => GoRouter.of(context).go('/summary'),
                      borderRadius: BorderRadius.circular(16),
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 12,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.09),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.09),
                          ),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 34,
                              height: 34,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.11),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.insights_rounded,
                                color: Color(0xFF8FF3D4),
                                size: 17,
                              ),
                            ),
                            const SizedBox(width: 11),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    _headline(context),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 13,
                                      fontWeight: FontWeight.w700,
                                      height: 1.25,
                                    ),
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    _subtitle(context),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(
                                      color: Colors.white.withValues(alpha: 0.62),
                                      fontSize: 10.5,
                                      height: 1.2,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Icon(
                              Icons.chevron_right_rounded,
                              color: Colors.white.withValues(alpha: 0.7),
                              size: 20,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroSparkline extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low, high;

  const _HeroSparkline({
    required this.logs,
    required this.low,
    required this.high,
  });

  @override
  Widget build(BuildContext context) {
    if (logs.length < 2) {
      return Center(
        child: Icon(
          Icons.show_chart_rounded,
          color: Colors.white.withValues(alpha: 0.32),
          size: 38,
        ),
      );
    }

    final values = logs.take(12).toList().reversed.toList();
    final spots = values
        .asMap()
        .entries
        .map((entry) => FlSpot(entry.key.toDouble(), entry.value.bloodSugar))
        .toList();
    final ys = values.map((e) => e.bloodSugar);
    final minObserved = ys.reduce(math.min);
    final maxObserved = ys.reduce(math.max);
    final minY = math.min(minObserved, low) - 12;
    final maxY = math.max(maxObserved, high) + 12;

    return LineChart(
      LineChartData(
        minY: minY,
        maxY: maxY,
        gridData: const FlGridData(show: false),
        titlesData: const FlTitlesData(show: false),
        borderData: FlBorderData(show: false),
        extraLinesData: ExtraLinesData(
          horizontalLines: [
            HorizontalLine(
              y: low,
              color: Colors.white.withValues(alpha: 0.13),
              strokeWidth: 1,
              dashArray: [4, 4],
            ),
            HorizontalLine(
              y: high,
              color: Colors.white.withValues(alpha: 0.13),
              strokeWidth: 1,
              dashArray: [4, 4],
            ),
          ],
        ),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            curveSmoothness: 0.32,
            color: const Color(0xFF79E9C2),
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  const Color(0xFF79E9C2).withValues(alpha: 0.20),
                  const Color(0xFF79E9C2).withValues(alpha: 0.0),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
