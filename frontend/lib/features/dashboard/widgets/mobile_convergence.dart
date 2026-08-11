part of '../dashboard_screen.dart';

// UX-10 — mobile Dashboard composition converging on the approved reference.
// Data remains sourced exclusively from persisted IAmina logs/profile state.

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

  String _firstName() {
    final user = FirebaseAuth.instance.currentUser;
    final raw = user?.displayName?.trim();
    if (raw == null || raw.isEmpty) return '';
    return raw.split(RegExp(r'\s+')).first;
  }

  String _metric(double raw) {
    if (unit == 'mmol/L') return (raw / 18.0).toStringAsFixed(1);
    return raw.toStringAsFixed(0);
  }

  int _daysWithData() => logs
      .map((entry) {
        final date = entry.loggedAt ?? entry.createdAt;
        return '${date.year}-${date.month}-${date.day}';
      })
      .toSet()
      .length;

  String _observation(BuildContext context, int tir) {
    final l10n = AuditedPageCopy.of(context).l10n;
    if (tir >= 80) return l10n.dashboardInsightStrong(tir, range);
    if (tir >= 60) {
      return l10n.dashboardInsightProgress(
        tir,
        ClinicalEngine.calcMean(logs).round(),
      );
    }
    return l10n.dashboardInsightNeedsFocus(range);
  }

  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    final l10n = copy.l10n;
    final latest = logs.first;
    final latestAt = latest.loggedAt ?? latest.createdAt;
    final tir = ClinicalEngine.calcTIR(logs, low, high);
    final mean = ClinicalEngine.calcMean(logs);
    final daysWithData = _daysWithData();
    final gmiEligible = daysWithData >= 14 && logs.length >= 50;
    final gmi = gmiEligible ? ClinicalEngine.calcGMI(logs) : null;
    final inTarget = latest.bloodSugar >= low && latest.bloodSugar <= high;
    final readingStatus = latest.bloodSugar < low
        ? copy.low
        : latest.bloodSugar > high
        ? copy.high
        : copy.inRange;
    final firstName = _firstName();
    final greeting = copy.greeting(DateTime.now().hour, firstName);
    final bg = AminaTheme.isDark(context)
        ? AminaTheme.bg(context)
        : const Color(0xFFF8F5EF);

    return Scaffold(
      backgroundColor: bg,
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          physics: const BouncingScrollPhysics(),
          slivers: [
            SliverPadding(
              padding: const EdgeInsetsDirectional.fromSTEB(18, 12, 18, 120),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  _ReferenceBrandHeader(
                    syncService: syncService,
                    onChatTap: onChatTap,
                  ),
                  const SizedBox(height: 24),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              greeting,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 25,
                                height: 1.05,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -0.7,
                                color: AminaTheme.textPrimary(context),
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              copy.observation(range),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 12.5,
                                height: 1.35,
                                color: AminaTheme.textSecondary(context),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 10),
                      _RangeDatePill(
                        range: range,
                        onChanged: onRangeChanged,
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _ReferenceReadingHero(
                    logs: logs,
                    latest: latest,
                    latestAt: latestAt,
                    unit: unit,
                    low: low,
                    high: high,
                    displayValue: _metric(latest.bloodSugar),
                    status: readingStatus,
                    inTarget: inTarget,
                    observation: _observation(context, tir),
                  ),
                  const SizedBox(height: 14),
                  _ReferenceTrendsCard(
                    mean: mean,
                    unit: unit,
                    tir: tir,
                    gmi: gmi,
                    observation: _observation(context, tir),
                    onViewAll: () => GoRouter.of(context).go('/summary'),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    l10n.dashboardQuickActions,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w800,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                  const SizedBox(height: 10),
                  const _ReferenceQuickActions(),
                  const SizedBox(height: 24),
                  _ChartSection(logs: logs, low: low, high: high, unit: unit),
                  const SizedBox(height: 16),
                  _InsightsSection(
                    logs: logs,
                    summary: summary,
                    isLoading: isLoadingSummary,
                  ),
                  const SizedBox(height: 16),
                  _RecentEntries(
                    logs: logs,
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

  const _ReferenceBrandHeader({
    required this.syncService,
    required this.onChatTap,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    return Row(
      children: [
        const SizedBox(
          width: 45,
          height: 45,
          child: CustomPaint(painter: _IaminaSealPainter()),
        ),
        const SizedBox(width: 11),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'IAmina',
                style: TextStyle(
                  fontSize: 24,
                  height: 1,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.8,
                  color: AminaTheme.textPrimary(context),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                l10n.appTagline,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w600,
                  color: AminaTheme.textSecondary(context),
                ),
              ),
            ],
          ),
        ),
        ValueListenableBuilder<SyncUiState>(
          valueListenable: syncService.state,
          builder: (_, state, __) => Stack(
            clipBehavior: Clip.none,
            children: [
              Material(
                color: AminaTheme.surface(context),
                shape: const CircleBorder(),
                child: InkWell(
                  onTap: onChatTap,
                  customBorder: const CircleBorder(),
                  child: SizedBox(
                    width: 46,
                    height: 46,
                    child: Icon(
                      Icons.chat_bubble_outline_rounded,
                      size: 20,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                ),
              ),
              PositionedDirectional(
                top: 2,
                end: 2,
                child: Container(
                  width: 9,
                  height: 9,
                  decoration: BoxDecoration(
                    color: state == SyncUiState.failed
                        ? AminaTheme.dangerFg
                        : AminaTheme.teal500,
                    shape: BoxShape.circle,
                    border: Border.all(color: AminaTheme.surface(context), width: 2),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _RangeDatePill extends StatelessWidget {
  final int range;
  final ValueChanged<int> onChanged;

  const _RangeDatePill({required this.range, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<int>(
      onSelected: onChanged,
      itemBuilder: (_) => [7, 21, 90]
          .map((value) => PopupMenuItem<int>(
                value: value,
                child: Text('$value ${AuditedPageCopy.of(context).dayShort}'),
              ))
          .toList(),
      child: Container(
        height: 38,
        padding: const EdgeInsetsDirectional.fromSTEB(12, 0, 10, 0),
        decoration: BoxDecoration(
          color: AminaTheme.surface(context),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.calendar_today_outlined,
                size: 14, color: AminaTheme.textSecondary(context)),
            const SizedBox(width: 7),
            Text(
              '$range ${AuditedPageCopy.of(context).dayShort}',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: AminaTheme.textPrimary(context),
              ),
            ),
            const SizedBox(width: 4),
            Icon(Icons.keyboard_arrow_down_rounded,
                size: 16, color: AminaTheme.textSecondary(context)),
          ],
        ),
      ),
    );
  }
}

class _ReferenceReadingHero extends StatelessWidget {
  final List<LogEntryData> logs;
  final LogEntryData latest;
  final DateTime latestAt;
  final String unit;
  final double low;
  final double high;
  final String displayValue;
  final String status;
  final bool inTarget;
  final String observation;

  const _ReferenceReadingHero({
    required this.logs,
    required this.latest,
    required this.latestAt,
    required this.unit,
    required this.low,
    required this.high,
    required this.displayValue,
    required this.status,
    required this.inTarget,
    required this.observation,
  });

  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    final rawMeal = latest.mealType?.trim();
    final meal = rawMeal == null || rawMeal.isEmpty ? '' : copy.meal(rawMeal);
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 18, 18, 16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF063F45), Color(0xFF005A5E), Color(0xFF06484E)],
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
        ),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF063F45).withValues(alpha: 0.18),
            blurRadius: 24,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: const Color(0xFF54D79F).withValues(alpha: 0.18),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.water_drop_rounded,
                    color: Color(0xFF70E4AE), size: 19),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      copy.latestReading,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    if (meal.isNotEmpty)
                      Text(
                        '$meal · ${DateFormat.Hm().format(latestAt)}',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.68),
                          fontSize: 10.5,
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 17),
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Expanded(
                flex: 4,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      alignment: AlignmentDirectional.centerStart,
                      child: RichText(
                        text: TextSpan(
                          children: [
                            TextSpan(
                              text: displayValue,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 48,
                                height: 1,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -2,
                              ),
                            ),
                            TextSpan(
                              text: ' $unit',
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.72),
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
                      decoration: BoxDecoration(
                        color: (inTarget
                                ? const Color(0xFF41C88A)
                                : const Color(0xFFE7B14D))
                            .withValues(alpha: 0.20),
                        borderRadius: BorderRadius.circular(99),
                      ),
                      child: Text(
                        status,
                        style: TextStyle(
                          color: inTarget
                              ? const Color(0xFF8FF3C4)
                              : const Color(0xFFFFD98A),
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 6,
                child: SizedBox(
                  height: 112,
                  child: _HeroSparkline(logs: logs, low: low, high: high),
                ),
              ),
            ],
          ),
          const SizedBox(height: 15),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 11),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(13),
            ),
            child: Row(
              children: [
                const Icon(Icons.auto_awesome_rounded,
                    color: Color(0xFF7CE8C0), size: 16),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    observation,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.90),
                      fontSize: 10.5,
                      height: 1.3,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const Icon(Icons.chevron_right_rounded,
                    color: Colors.white70, size: 18),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ReferenceTrendsCard extends StatelessWidget {
  final double mean;
  final String unit;
  final int tir;
  final double? gmi;
  final String observation;
  final VoidCallback onViewAll;

  const _ReferenceTrendsCard({
    required this.mean,
    required this.unit,
    required this.tir,
    required this.gmi,
    required this.observation,
    required this.onViewAll,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    final displayMean = unit == 'mmol/L'
        ? (mean / 18.0).toStringAsFixed(1)
        : mean.toStringAsFixed(0);
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 15),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AminaTheme.divider(context)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.045),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  l10n.dashboardTrendsInsights,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
              ),
              TextButton(
                onPressed: onViewAll,
                child: Text(l10n.dashboardViewAll),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _TrendMetric(
                  icon: Icons.trending_up_rounded,
                  label: l10n.dashboardMeanLabel,
                  value: displayMean,
                  suffix: unit,
                ),
              ),
              Expanded(
                child: _TrendMetric(
                  icon: Icons.timelapse_rounded,
                  label: AuditedPageCopy.of(context).readingsInRange,
                  value: '$tir',
                  suffix: '%',
                ),
              ),
              Expanded(
                child: _TrendMetric(
                  icon: Icons.local_fire_department_outlined,
                  label: l10n.dashboardGmiEstimated,
                  value: gmi == null ? '--' : gmi!.toStringAsFixed(1),
                  suffix: gmi == null ? '' : '%',
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
            decoration: BoxDecoration(
              color: const Color(0xFFEAF7EF),
              borderRadius: BorderRadius.circular(13),
            ),
            child: Row(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: const BoxDecoration(
                    color: Color(0xFFD8F1E2),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.insights_rounded,
                      color: Color(0xFF0A8765), size: 17),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    observation,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 10.5,
                      height: 1.3,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF24443A),
                    ),
                  ),
                ),
                const Icon(Icons.chevron_right_rounded,
                    color: Color(0xFF0A8765), size: 18),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TrendMetric extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String suffix;

  const _TrendMetric({
    required this.icon,
    required this.label,
    required this.value,
    required this.suffix,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: const BoxDecoration(
              color: Color(0xFFE8F5EE),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 17, color: const Color(0xFF0A8765)),
          ),
          const SizedBox(height: 8),
          Text(
            label,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 9.5,
              height: 1.15,
              color: AminaTheme.textSecondary(context),
            ),
          ),
          const SizedBox(height: 3),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: AlignmentDirectional.centerStart,
            child: RichText(
              text: TextSpan(
                children: [
                  TextSpan(
                    text: value,
                    style: TextStyle(
                      fontSize: 23,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.7,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                  if (suffix.isNotEmpty)
                    TextSpan(
                      text: ' $suffix',
                      style: TextStyle(
                        fontSize: 8.5,
                        fontWeight: FontWeight.w600,
                        color: AminaTheme.textSecondary(context),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ReferenceQuickActions extends StatelessWidget {
  const _ReferenceQuickActions();

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    final items = <({IconData icon, String label, String route})>[
      (icon: Icons.menu_book_outlined, label: l10n.navJournal, route: '/journal'),
      (icon: Icons.add_rounded, label: l10n.addEntry, route: '/ajouter'),
      (icon: Icons.upload_file_outlined, label: l10n.navImport, route: '/importer'),
      (icon: Icons.description_outlined, label: l10n.summary, route: '/summary'),
      (icon: Icons.person_outline_rounded, label: l10n.profile, route: '/profile'),
    ];

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final item in items)
          Expanded(
            child: InkWell(
              onTap: () => GoRouter.of(context).go(item.route),
              borderRadius: BorderRadius.circular(16),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 2),
                child: Column(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: AminaTheme.surface(context),
                        borderRadius: BorderRadius.circular(15),
                        border: Border.all(color: AminaTheme.divider(context)),
                      ),
                      child: Icon(item.icon,
                          size: 20, color: const Color(0xFF064D50)),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      item.label,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.w600,
                        color: AminaTheme.textPrimary(context),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _IaminaSealPainter extends CustomPainter {
  const _IaminaSealPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final teal = Paint()
      ..color = const Color(0xFF075A5D)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.2
      ..strokeCap = StrokeCap.square
      ..strokeJoin = StrokeJoin.miter;
    final jade = Paint()
      ..color = const Color(0xFF27B984)
      ..style = PaintingStyle.fill;
    final s = size.width;
    final path = Path()
      ..moveTo(2, s * .72)
      ..lineTo(2, 2)
      ..lineTo(s * .72, 2)
      ..lineTo(s * .72, s * .30)
      ..lineTo(s * .36, s * .30)
      ..lineTo(s * .36, s * .58)
      ..lineTo(s * .82, s * .58)
      ..lineTo(s * .82, s * .92)
      ..lineTo(s * .18, s * .92)
      ..lineTo(s * .18, s * .72)
      ..lineTo(s * .58, s * .72);
    canvas.drawPath(path, teal);
    canvas.drawRect(Rect.fromLTWH(s * .84, s * .12, 6, 6), jade);
    canvas.drawRect(Rect.fromLTWH(s * .58, s * .40, 5, 5), jade);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
