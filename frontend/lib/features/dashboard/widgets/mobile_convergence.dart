part of '../dashboard_screen.dart';

class _DashboardMobileConvergence extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final double low;
  final double high;
  final int range;
  final SyncService syncService;
  final ValueChanged<int> onRangeChanged;
  final VoidCallback onChatTap;
  final SummaryResponse? summary;
  final bool isLoadingSummary;

  const _DashboardMobileConvergence({
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
    required this.range,
    required this.syncService,
    required this.onRangeChanged,
    required this.onChatTap,
    required this.summary,
    required this.isLoadingSummary,
  });

  String _t(BuildContext context, String fr, String en, String ar) {
    final code = Localizations.localeOf(context).languageCode;
    if (code == 'ar') return ar;
    if (code == 'en') return en;
    return fr;
  }

  int _daysWithData() => logs
      .map((e) {
        final d = e.loggedAt ?? e.createdAt;
        return '${d.year}-${d.month}-${d.day}';
      })
      .toSet()
      .length;

  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    final latest = List<LogEntryData>.from(logs)
      ..sort((a, b) => (b.loggedAt ?? b.createdAt).compareTo(a.loggedAt ?? a.createdAt));
    final current = latest.first;
    final currentTime = current.loggedAt ?? current.createdAt;
    final display = unit == 'mmol/L'
        ? (current.bloodSugar / 18.0).toStringAsFixed(1)
        : current.bloodSugar.toStringAsFixed(0);
    final inTarget = current.bloodSugar >= low && current.bloodSugar <= high;
    final tir = ClinicalEngine.calcTIR(logs, low, high);
    final cv = ClinicalEngine.calcCV(logs);
    final mean = ClinicalEngine.calcMean(logs);
    final gmiEligible = _daysWithData() >= 14 && logs.length >= 50;
    final gmi = gmiEligible ? ClinicalEngine.calcGMI(logs) : null;
    final firstName = _HeroInsight._firstName();

    return Scaffold(
      backgroundColor: const Color(0xFFF5F3EC),
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          physics: const BouncingScrollPhysics(),
          slivers: [
            SliverPadding(
              padding: const EdgeInsetsDirectional.fromSTEB(18, 10, 18, 116),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  _ReferenceBrandHeader(
                    syncService: syncService,
                    onChatTap: onChatTap,
                    subtitle: copy.overview,
                  ),
                  const SizedBox(height: 24),
                  Text(
                    copy.greeting(DateTime.now().hour, firstName),
                    style: const TextStyle(
                      color: Color(0xFF14221F),
                      fontSize: 27,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.8,
                      height: 1.05,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _t(
                      context,
                      'Voici votre équilibre glycémique actuel.',
                      'Here is your current glucose balance.',
                      'هذه لمحة عن توازنك السكري الحالي.',
                    ),
                    style: const TextStyle(
                      color: Color(0xFF7A827E),
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 18),
                  _ReferenceGlucoseHero(
                    logs: latest,
                    value: display,
                    unit: unit,
                    low: low,
                    high: high,
                    inTarget: inTarget,
                    currentTime: currentTime,
                  ),
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          _t(context, 'Tendances & Insights', 'Trends & Insights', 'الاتجاهات والمؤشرات'),
                          style: const TextStyle(
                            color: Color(0xFF172420),
                            fontSize: 19,
                            fontWeight: FontWeight.w800,
                            letterSpacing: -0.35,
                          ),
                        ),
                      ),
                      _RangeSelector(range: range, onChanged: onRangeChanged),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _ReferenceTrendsCard(
                    tir: tir,
                    gmi: gmi,
                    cv: cv,
                    mean: mean,
                    unit: unit,
                    range: range,
                    gmiEligible: gmiEligible,
                  ),
                  const SizedBox(height: 21),
                  Text(
                    _t(context, 'Actions rapides', 'Quick actions', 'إجراءات سريعة'),
                    style: const TextStyle(
                      color: Color(0xFF172420),
                      fontSize: 19,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.35,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _QuickActions(onChatTap: onChatTap),
                  const SizedBox(height: 20),
                  _ReferenceInsightCard(
                    summary: summary,
                    isLoading: isLoadingSummary,
                    logs: logs,
                    range: range,
                  ),
                  const SizedBox(height: 18),
                  _RecentEntries(
                    logs: latest,
                    unit: unit,
                    low: low,
                    high: high,
                    isDesktop: false,
                  ),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ReferenceBrandHeader extends StatelessWidget {
  final SyncService syncService;
  final VoidCallback onChatTap;
  final String subtitle;

  const _ReferenceBrandHeader({
    required this.syncService,
    required this.onChatTap,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: const Color(0xFF07575A),
            borderRadius: BorderRadius.circular(14),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF07575A).withValues(alpha: 0.18),
                blurRadius: 16,
                offset: const Offset(0, 7),
              ),
            ],
          ),
          child: const _ReferenceMark(),
        ),
        const SizedBox(width: 11),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'IAmina',
                style: TextStyle(
                  color: Color(0xFF10201D),
                  fontSize: 18,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -0.35,
                ),
              ),
              Text(
                subtitle,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Color(0xFF89908C),
                  fontSize: 10.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
        IconButton(
          onPressed: onChatTap,
          tooltip: AuditedPageCopy.of(context).talk,
          icon: const Icon(Icons.chat_bubble_outline_rounded, size: 19),
          style: IconButton.styleFrom(
            foregroundColor: const Color(0xFF46605A),
            backgroundColor: Colors.white,
            minimumSize: const Size(42, 42),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: Color(0xFFE8E8E1)),
            ),
          ),
        ),
        const SizedBox(width: 7),
        ValueListenableBuilder<SyncUiState>(
          valueListenable: syncService.state,
          builder: (_, state, __) {
            final syncing = state == SyncUiState.syncing;
            return IconButton(
              onPressed: syncing ? null : syncService.syncPendingLogs,
              tooltip: AuditedPageCopy.of(context).overview,
              icon: syncing
                  ? const SizedBox(
                      width: 17,
                      height: 17,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.notifications_none_rounded, size: 21),
              style: IconButton.styleFrom(
                foregroundColor: const Color(0xFF46605A),
                backgroundColor: Colors.white,
                minimumSize: const Size(42, 42),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                  side: const BorderSide(color: Color(0xFFE8E8E1)),
                ),
              ),
            );
          },
        ),
      ],
    );
  }
}

class _ReferenceMark extends StatelessWidget {
  const _ReferenceMark();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(9),
      child: CustomPaint(painter: _ReferenceMarkPainter()),
    );
  }
}

class _ReferenceMarkPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.2
      ..strokeCap = StrokeCap.square
      ..strokeJoin = StrokeJoin.miter;
    final path = Path()
      ..moveTo(1, size.height - 1)
      ..lineTo(1, 1)
      ..lineTo(size.width - 1, 1)
      ..lineTo(size.width - 1, size.height * .44)
      ..lineTo(size.width * .55, size.height * .44)
      ..lineTo(size.width * .55, size.height * .78)
      ..lineTo(size.width * .25, size.height * .78)
      ..lineTo(size.width * .25, size.height * .34)
      ..lineTo(size.width * .72, size.height * .34);
    canvas.drawPath(path, p);
    canvas.drawRect(
      Rect.fromLTWH(size.width * .68, size.height * .72, 4, 4),
      Paint()..color = const Color(0xFF7FE0B9),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ReferenceGlucoseHero extends StatelessWidget {
  final List<LogEntryData> logs;
  final String value;
  final String unit;
  final double low;
  final double high;
  final bool inTarget;
  final DateTime currentTime;

  const _ReferenceGlucoseHero({
    required this.logs,
    required this.value,
    required this.unit,
    required this.low,
    required this.high,
    required this.inTarget,
    required this.currentTime,
  });

  String _t(BuildContext context, String fr, String en, String ar) {
    final code = Localizations.localeOf(context).languageCode;
    return code == 'ar' ? ar : code == 'en' ? en : fr;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 214,
      padding: const EdgeInsetsDirectional.fromSTEB(19, 17, 14, 15),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0A6260), Color(0xFF064B50), Color(0xFF04383F)],
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
        ),
        borderRadius: BorderRadius.circular(27),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF073F43).withValues(alpha: 0.25),
            blurRadius: 26,
            offset: const Offset(0, 13),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  _t(context, 'GLUCOSE ACTUEL', 'CURRENT GLUCOSE', 'الجلوكوز الحالي'),
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.72),
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.05,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(99),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.13)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 7,
                      height: 7,
                      decoration: BoxDecoration(
                        color: inTarget ? const Color(0xFF75E3B8) : const Color(0xFFFFC46A),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      inTarget
                          ? _t(context, 'Dans la cible', 'In range', 'ضمن النطاق')
                          : _t(context, 'Hors cible', 'Out of range', 'خارج النطاق'),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const Spacer(),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                flex: 5,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      alignment: AlignmentDirectional.centerStart,
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '\u2066$value\u2069',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 53,
                              height: .9,
                              fontWeight: FontWeight.w900,
                              letterSpacing: -2.0,
                            ),
                          ),
                          const SizedBox(width: 7),
                          Padding(
                            padding: const EdgeInsets.only(bottom: 5),
                            child: Text(
                              '\u2066$unit\u2069',
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.7),
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 9),
                    Text(
                      DateFormat.Hm(Localizations.localeOf(context).toLanguageTag()).format(currentTime),
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.62),
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                flex: 6,
                child: SizedBox(
                  height: 92,
                  child: _ReferenceSparkline(logs: logs, low: low, high: high),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(height: 1, color: Colors.white.withValues(alpha: 0.11)),
          const SizedBox(height: 11),
          Row(
            children: [
              Icon(Icons.auto_awesome_rounded, color: Colors.white.withValues(alpha: .72), size: 14),
              const SizedBox(width: 7),
              Expanded(
                child: Text(
                  _t(
                    context,
                    'Valeur issue de votre dernière mesure enregistrée.',
                    'Value from your latest recorded measurement.',
                    'القيمة مأخوذة من آخر قياس مسجل لديك.',
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: .68),
                    fontSize: 10.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ReferenceSparkline extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low;
  final double high;
  const _ReferenceSparkline({required this.logs, required this.low, required this.high});

  @override
  Widget build(BuildContext context) {
    final points = logs.take(14).toList().reversed.toList();
    if (points.length < 2) return const SizedBox.shrink();
    final spots = <FlSpot>[];
    for (var i = 0; i < points.length; i++) {
      spots.add(FlSpot(i.toDouble(), points[i].bloodSugar));
    }
    final values = points.map((e) => e.bloodSugar).toList();
    final minY = math.max(0, values.reduce(math.min) - 20).toDouble();
    final maxY = (values.reduce(math.max) + 20).toDouble();
    return LineChart(
      LineChartData(
        minY: minY,
        maxY: maxY,
        gridData: const FlGridData(show: false),
        titlesData: const FlTitlesData(show: false),
        borderData: FlBorderData(show: false),
        lineTouchData: const LineTouchData(enabled: false),
        extraLinesData: ExtraLinesData(horizontalLines: [
          if (low >= minY && low <= maxY)
            HorizontalLine(y: low, color: Colors.white.withValues(alpha: .13), strokeWidth: 1),
          if (high >= minY && high <= maxY)
            HorizontalLine(y: high, color: Colors.white.withValues(alpha: .13), strokeWidth: 1),
        ]),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            curveSmoothness: .32,
            color: const Color(0xFF78E3BC),
            barWidth: 2.4,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, percent, bar, index) => FlDotCirclePainter(
                radius: index == spots.length - 1 ? 3.2 : 0,
                color: const Color(0xFF78E3BC),
                strokeWidth: 2,
                strokeColor: Colors.white,
              ),
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  const Color(0xFF78E3BC).withValues(alpha: .23),
                  const Color(0xFF78E3BC).withValues(alpha: .01),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RangeSelector extends StatelessWidget {
  final int range;
  final ValueChanged<int> onChanged;
  const _RangeSelector({required this.range, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: const Color(0xFFECEBE4),
        borderRadius: BorderRadius.circular(11),
      ),
      child: Row(
        children: [7, 21, 90].map((r) {
          final active = r == range;
          return InkWell(
            onTap: () => onChanged(r),
            borderRadius: BorderRadius.circular(8),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
              decoration: BoxDecoration(
                color: active ? Colors.white : Colors.transparent,
                borderRadius: BorderRadius.circular(8),
                boxShadow: active
                    ? [BoxShadow(color: Colors.black.withValues(alpha: .06), blurRadius: 7)]
                    : null,
              ),
              child: Text(
                '$r j',
                style: TextStyle(
                  color: active ? const Color(0xFF15302B) : const Color(0xFF818782),
                  fontSize: 9.5,
                  fontWeight: active ? FontWeight.w800 : FontWeight.w600,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ReferenceTrendsCard extends StatelessWidget {
  final double tir;
  final double? gmi;
  final double cv;
  final double mean;
  final String unit;
  final int range;
  final bool gmiEligible;

  const _ReferenceTrendsCard({
    required this.tir,
    required this.gmi,
    required this.cv,
    required this.mean,
    required this.unit,
    required this.range,
    required this.gmiEligible,
  });

  String _t(BuildContext context, String fr, String en, String ar) {
    final code = Localizations.localeOf(context).languageCode;
    return code == 'ar' ? ar : code == 'en' ? en : fr;
  }

  @override
  Widget build(BuildContext context) {
    final meanDisplay = unit == 'mmol/L' ? (mean / 18).toStringAsFixed(1) : mean.toStringAsFixed(0);
    return Container(
      padding: const EdgeInsets.fromLTRB(15, 16, 15, 13),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE9E8E1)),
        boxShadow: [
          BoxShadow(color: const Color(0xFF22322E).withValues(alpha: .05), blurRadius: 18, offset: const Offset(0, 8)),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(child: _TrendMetric(label: 'TIR', value: tir.toStringAsFixed(0), suffix: '%', icon: Icons.timelapse_rounded)),
              Container(width: 1, height: 58, color: const Color(0xFFECEBE5)),
              Expanded(child: _TrendMetric(label: 'GMI', value: gmi == null ? '--' : gmi!.toStringAsFixed(1), suffix: gmi == null ? '' : '%', icon: Icons.water_drop_outlined)),
              Container(width: 1, height: 58, color: const Color(0xFFECEBE5)),
              Expanded(child: _TrendMetric(label: 'CV', value: cv == 0 ? '--' : cv.toStringAsFixed(0), suffix: cv == 0 ? '' : '%', icon: Icons.show_chart_rounded)),
            ],
          ),
          const SizedBox(height: 13),
          Container(height: 1, color: const Color(0xFFF0EFE9)),
          const SizedBox(height: 11),
          Row(
            children: [
              const Icon(Icons.analytics_outlined, size: 16, color: Color(0xFF0A8765)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '${_t(context, 'Moyenne', 'Average', 'المتوسط')} · \u2066$meanDisplay $unit\u2069',
                  style: const TextStyle(color: Color(0xFF61706A), fontSize: 11.5, fontWeight: FontWeight.w650),
                ),
              ),
              Text(
                '$range j',
                style: const TextStyle(color: Color(0xFF9BA19D), fontSize: 10.5, fontWeight: FontWeight.w700),
              ),
            ],
          ),
          if (!gmiEligible) ...[
            const SizedBox(height: 8),
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: Text(
                AuditedPageCopy.of(context).l10n.dashboardGmiLimitedCoverage,
                style: const TextStyle(color: Color(0xFFA66D19), fontSize: 9.5, height: 1.25),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _TrendMetric extends StatelessWidget {
  final String label;
  final String value;
  final String suffix;
  final IconData icon;
  const _TrendMetric({required this.label, required this.value, required this.suffix, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(icon, size: 14, color: const Color(0xFF0A8765)),
            const SizedBox(width: 5),
            Text(label, style: const TextStyle(color: Color(0xFF7E8883), fontSize: 10, fontWeight: FontWeight.w700)),
          ]),
          const SizedBox(height: 8),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: AlignmentDirectional.centerStart,
            child: Text.rich(
              TextSpan(children: [
                TextSpan(text: value, style: const TextStyle(color: Color(0xFF172521), fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: -1.1)),
                TextSpan(text: suffix, style: const TextStyle(color: Color(0xFF6F7A75), fontSize: 11, fontWeight: FontWeight.w700)),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  final VoidCallback onChatTap;
  const _QuickActions({required this.onChatTap});

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    final actions = <(IconData, String, VoidCallback)>[
      (Icons.add_rounded, l10n.addEntry, () => GoRouter.of(context).go('/ajouter')),
      (Icons.history_rounded, l10n.navJournal, () => GoRouter.of(context).go('/journal')),
      (Icons.upload_file_outlined, l10n.navImport, () => GoRouter.of(context).go('/importer')),
      (Icons.chat_bubble_outline_rounded, AuditedPageCopy.of(context).talk, onChatTap),
    ];
    return Row(
      children: actions.asMap().entries.map((entry) {
        final item = entry.value;
        return Expanded(
          child: Padding(
            padding: EdgeInsetsDirectional.only(end: entry.key == actions.length - 1 ? 0 : 9),
            child: InkWell(
              onTap: item.$3,
              borderRadius: BorderRadius.circular(18),
              child: Container(
                height: 82,
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0xFFE9E8E1)),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 33,
                      height: 33,
                      decoration: const BoxDecoration(color: Color(0xFFE7F4EF), shape: BoxShape.circle),
                      child: Icon(item.$1, size: 17, color: const Color(0xFF0A8765)),
                    ),
                    const SizedBox(height: 7),
                    Text(
                      item.$2,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Color(0xFF465650), fontSize: 9.5, fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

class _ReferenceInsightCard extends StatelessWidget {
  final SummaryResponse? summary;
  final bool isLoading;
  final List<LogEntryData> logs;
  final int range;

  const _ReferenceInsightCard({required this.summary, required this.isLoading, required this.logs, required this.range});

  String _t(BuildContext context, String fr, String en, String ar) {
    final code = Localizations.localeOf(context).languageCode;
    return code == 'ar' ? ar : code == 'en' ? en : fr;
  }

  @override
  Widget build(BuildContext context) {
    final tir = ClinicalEngine.calcTIR(logs, 70, 180).round();
    final text = isLoading
        ? AuditedPageCopy.of(context).l10n.dashboardAnalyzingPatterns
        : _t(
            context,
            '$tir% de vos mesures sont dans la plage observée sur $range jours.',
            '$tir% of your readings are within the observed range over $range days.',
            '$tir% من قياساتك ضمن النطاق المرصود خلال $range يومًا.',
          );
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFEAF5F1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFD7EAE3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 35,
            height: 35,
            decoration: const BoxDecoration(color: Color(0xFF0A8765), shape: BoxShape.circle),
            child: const Icon(Icons.auto_awesome_rounded, color: Colors.white, size: 17),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _t(context, 'Insight IAmina', 'IAmina insight', 'مؤشر IAmina'),
                  style: const TextStyle(color: Color(0xFF0B684F), fontSize: 11, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 4),
                Text(
                  text,
                  style: const TextStyle(color: Color(0xFF3E5C53), fontSize: 11.5, height: 1.4, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
