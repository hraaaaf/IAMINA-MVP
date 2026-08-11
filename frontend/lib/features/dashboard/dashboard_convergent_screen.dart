import 'dart:math' as math;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../l10n/app_localizations.dart';
import 'clinical_engine.dart';

/// UX-10 mobile-only Dashboard composition.
/// It intentionally reuses only persisted IAmina data and deterministic metrics.
class DashboardConvergentScreen extends StatefulWidget {
  const DashboardConvergentScreen({super.key});

  @override
  State<DashboardConvergentScreen> createState() =>
      _DashboardConvergentScreenState();
}

class _DashboardConvergentScreenState extends State<DashboardConvergentScreen> {
  int _range = 21;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted || !kDebugMode) return;
      final db = context.read<AppDatabase>();
      final count = await db
          .select(db.logEntries)
          .get()
          .then((rows) => rows.length);
      if (count == 0) await db.seedDemoData();
    });
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final now = DateTime.now();
    final start = now.subtract(Duration(days: _range));

    return StreamBuilder<PatientProfileData?>(
      stream: db.watchProfile(),
      builder: (context, profileSnap) {
        final profile = profileSnap.data;
        final unit = profile?.unitPreference ?? 'mg/dL';
        final low = profile?.targetRangeLow ?? 70.0;
        final high = profile?.targetRangeHigh ?? 180.0;
        return StreamBuilder<List<LogEntryData>>(
          stream: db.watchLogsInRange(start, now),
          builder: (context, logsSnap) {
            if (profileSnap.hasError || logsSnap.hasError) {
              return _ConvergentState(
                icon: Icons.error_outline_rounded,
                title: _t(
                  context,
                  'Données indisponibles',
                  'Data unavailable',
                  'البيانات غير متاحة',
                ),
                body: _t(
                  context,
                  'IAmina ne peut pas lire vos données locales pour le moment.',
                  'IAmina cannot read your local data right now.',
                  'يتعذر على IAmina قراءة بياناتك المحلية حالياً.',
                ),
              );
            }
            if (profileSnap.connectionState == ConnectionState.waiting ||
                logsSnap.connectionState == ConnectionState.waiting) {
              return _ConvergentState(
                loading: true,
                title: _t(context, 'Chargement', 'Loading', 'جارٍ التحميل'),
                body: _t(
                  context,
                  'IAmina prépare votre tableau de bord.',
                  'IAmina is preparing your dashboard.',
                  'تقوم IAmina بإعداد لوحة المتابعة.',
                ),
              );
            }

            final logs = logsSnap.data ?? const <LogEntryData>[];
            if (logs.isEmpty) {
              return _ConvergentEmpty(
                onAdd: () => GoRouter.of(context).go('/ajouter'),
                onImport: () => GoRouter.of(context).go('/importer'),
              );
            }

            final sorted = [...logs]
              ..sort(
                (a, b) => (b.loggedAt ?? b.createdAt).compareTo(
                  a.loggedAt ?? a.createdAt,
                ),
              );
            return _PopulatedReferenceDashboard(
              logs: sorted,
              unit: unit,
              low: low,
              high: high,
              range: _range,
              onRangeChanged: (value) => setState(() => _range = value),
            );
          },
        );
      },
    );
  }
}

class _PopulatedReferenceDashboard extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final double low;
  final double high;
  final int range;
  final ValueChanged<int> onRangeChanged;

  const _PopulatedReferenceDashboard({
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
    required this.range,
    required this.onRangeChanged,
  });

  int _daysWithData() => logs
      .map((e) {
        final d = e.loggedAt ?? e.createdAt;
        return '${d.year}-${d.month}-${d.day}';
      })
      .toSet()
      .length;

  String _display(double mg) =>
      unit == 'mmol/L' ? (mg / 18.0).toStringAsFixed(1) : mg.toStringAsFixed(0);

  String _firstName() {
    try {
      final raw = FirebaseAuth.instance.currentUser?.displayName?.trim();
      if (raw == null || raw.isEmpty) return '';
      return raw.split(RegExp(r'\s+')).first;
    } on Exception {
      return '';
    }
  }

  String _observation(BuildContext context, double tir) {
    if (tir >= 80) {
      return _t(
        context,
        '${tir.toStringAsFixed(0)} % des mesures enregistrées sont dans votre cible sur $range jours.',
        '${tir.toStringAsFixed(0)}% of recorded readings are in your range over $range days.',
        '${tir.toStringAsFixed(0)}٪ من القياسات المسجلة ضمن نطاقك خلال $range يوماً.',
      );
    }
    if (tir >= 60) {
      return _t(
        context,
        'Vos mesures montrent un équilibre intermédiaire sur les $range derniers jours.',
        'Your readings show an intermediate balance over the last $range days.',
        'تُظهر قياساتك توازناً متوسطاً خلال آخر $range يوماً.',
      );
    }
    return _t(
      context,
      'Vos mesures montrent davantage de valeurs hors cible sur les $range derniers jours.',
      'Your readings show more out-of-range values over the last $range days.',
      'تُظهر قياساتك قيماً أكثر خارج النطاق خلال آخر $range يوماً.',
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final latest = logs.first;
    final latestAt = latest.loggedAt ?? latest.createdAt;
    final tir = ClinicalEngine.calcTIR(logs, low, high);
    final mean = ClinicalEngine.calcMean(logs);
    final days = _daysWithData();
    final gmi = days >= 14 && logs.length >= 50
        ? ClinicalEngine.calcGMI(logs)
        : null;
    final isTarget = latest.bloodSugar >= low && latest.bloodSugar <= high;
    final status = latest.bloodSugar < low
        ? l10n.low
        : latest.bloodSugar > high
        ? l10n.high
        : l10n.inRange;
    final rawMeal = latest.mealType?.trim();
    final meal = rawMeal == null || rawMeal.isEmpty ? null : rawMeal;
    final firstName = _firstName();
    final greetingBase = DateTime.now().hour < 12
        ? l10n.goodMorning
        : DateTime.now().hour < 18
        ? l10n.goodAfternoon
        : l10n.goodEvening;
    final greeting = firstName.isEmpty
        ? '$greetingBase !'
        : '$greetingBase, $firstName';
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
              padding: const EdgeInsetsDirectional.fromSTEB(18, 10, 18, 118),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  _BrandRow(),
                  const SizedBox(height: 22),
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
                                letterSpacing: -0.8,
                                color: AminaTheme.textPrimary(context),
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              _t(
                                context,
                                "Voici votre résumé santé d'aujourd'hui.",
                                "Here is today's health summary.",
                                'إليك ملخص صحتك اليوم.',
                              ),
                              style: TextStyle(
                                fontSize: 12.5,
                                color: AminaTheme.textSecondary(context),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      _RangePill(range: range, onChanged: onRangeChanged),
                    ],
                  ),
                  const SizedBox(height: 15),
                  _GlucoseHero(
                    latest: latest,
                    latestAt: latestAt,
                    logs: logs,
                    unit: unit,
                    low: low,
                    high: high,
                    display: _display(latest.bloodSugar),
                    status: status,
                    inTarget: isTarget,
                    meal: meal,
                    observation: _observation(context, tir),
                  ),
                  const SizedBox(height: 14),
                  _TrendsPanel(
                    mean: mean,
                    unit: unit,
                    tir: tir,
                    gmi: gmi,
                    observation: _observation(context, tir),
                  ),
                  const SizedBox(height: 18),
                  Text(
                    _t(
                      context,
                      'Actions rapides',
                      'Quick actions',
                      'إجراءات سريعة',
                    ),
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w800,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                  const SizedBox(height: 9),
                  const _QuickActionsRow(),
                  const SizedBox(height: 26),
                  _DetailedTrendCard(
                    logs: logs,
                    low: low,
                    high: high,
                    unit: unit,
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

class _BrandRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Row(
      children: [
        const SizedBox(
          width: 46,
          height: 46,
          child: CustomPaint(painter: _SealPainter()),
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
        Material(
          color: AminaTheme.surface(context),
          shape: const CircleBorder(),
          child: InkWell(
            key: const ValueKey('dashboard-import-action'),
            onTap: () => GoRouter.of(context).go('/importer'),
            customBorder: const CircleBorder(),
            child: SizedBox(
              width: 46,
              height: 46,
              child: Icon(
                Icons.upload_file_outlined,
                size: 21,
                color: AminaTheme.textPrimary(context),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _RangePill extends StatelessWidget {
  final int range;
  final ValueChanged<int> onChanged;
  const _RangePill({required this.range, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<int>(
      onSelected: onChanged,
      itemBuilder: (_) => [
        7,
        21,
        90,
      ].map((v) => PopupMenuItem<int>(value: v, child: Text('$v j'))).toList(),
      child: Container(
        height: 38,
        padding: const EdgeInsetsDirectional.fromSTEB(11, 0, 9, 0),
        decoration: BoxDecoration(
          color: AminaTheme.surface(context),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.calendar_today_outlined,
              size: 14,
              color: AminaTheme.textSecondary(context),
            ),
            const SizedBox(width: 7),
            Text(
              '$range j',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                color: AminaTheme.textPrimary(context),
              ),
            ),
            const SizedBox(width: 3),
            Icon(
              Icons.keyboard_arrow_down_rounded,
              size: 16,
              color: AminaTheme.textSecondary(context),
            ),
          ],
        ),
      ),
    );
  }
}

class _GlucoseHero extends StatelessWidget {
  final LogEntryData latest;
  final DateTime latestAt;
  final List<LogEntryData> logs;
  final String unit;
  final double low;
  final double high;
  final String display;
  final String status;
  final bool inTarget;
  final String? meal;
  final String observation;

  const _GlucoseHero({
    required this.latest,
    required this.latestAt,
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
    required this.display,
    required this.status,
    required this.inTarget,
    required this.meal,
    required this.observation,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 17, 18, 15),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF063C43), Color(0xFF00575D), Color(0xFF073E44)],
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
        ),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF06484D).withValues(alpha: 0.18),
            blurRadius: 24,
            offset: const Offset(0, 11),
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
                  color: const Color(0xFF5AD7A1).withValues(alpha: 0.18),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.water_drop_rounded,
                  color: Color(0xFF74E7B2),
                  size: 19,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _t(
                        context,
                        'Glycémie actuelle',
                        'Current glucose',
                        'سكر الدم الحالي',
                      ),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    Text(
                      '${meal ?? _t(context, 'Mesure', 'Reading', 'قياس')} · ${DateFormat.Hm().format(latestAt)}',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.66),
                        fontSize: 10.5,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
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
                              text: display,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 49,
                                height: 1,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -2.2,
                              ),
                            ),
                            TextSpan(
                              text: ' $unit',
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.72),
                                fontSize: 11.5,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 11,
                        vertical: 7,
                      ),
                      decoration: BoxDecoration(
                        color:
                            (inTarget
                                    ? const Color(0xFF35C780)
                                    : const Color(0xFFE8AC42))
                                .withValues(alpha: 0.20),
                        borderRadius: BorderRadius.circular(99),
                      ),
                      child: Text(
                        status,
                        style: TextStyle(
                          color: inTarget
                              ? const Color(0xFF89F0BC)
                              : const Color(0xFFFFD889),
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
                  child: _MiniGlucoseChart(logs: logs, low: low, high: high),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          InkWell(
            onTap: () => GoRouter.of(context).go('/summary'),
            borderRadius: BorderRadius.circular(13),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(13),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.auto_awesome_rounded,
                    color: Color(0xFF78E7BE),
                    size: 16,
                  ),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      observation,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.91),
                        fontSize: 10.2,
                        height: 1.3,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const Icon(
                    Icons.chevron_right_rounded,
                    color: Colors.white70,
                    size: 18,
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

class _TrendsPanel extends StatelessWidget {
  final double mean;
  final String unit;
  final double tir;
  final double? gmi;
  final String observation;

  const _TrendsPanel({
    required this.mean,
    required this.unit,
    required this.tir,
    required this.gmi,
    required this.observation,
  });

  @override
  Widget build(BuildContext context) {
    final meanDisplay = unit == 'mmol/L'
        ? (mean / 18.0).toStringAsFixed(1)
        : mean.toStringAsFixed(0);
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
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
                  _t(
                    context,
                    'Tendances & Insights',
                    'Trends & Insights',
                    'الاتجاهات والمؤشرات',
                  ),
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
              ),
              TextButton(
                onPressed: () => GoRouter.of(context).go('/summary'),
                child: Text(_t(context, 'Voir tout', 'View all', 'عرض الكل')),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _MetricTile(
                  icon: Icons.trending_up_rounded,
                  label: _t(context, 'Moyenne', 'Average', 'المتوسط'),
                  value: meanDisplay,
                  suffix: unit,
                ),
              ),
              Expanded(
                child: _MetricTile(
                  icon: Icons.timelapse_rounded,
                  label: _t(context, 'Dans la cible', 'In range', 'ضمن النطاق'),
                  value: tir.toStringAsFixed(0),
                  suffix: '%',
                ),
              ),
              Expanded(
                child: _MetricTile(
                  icon: Icons.local_fire_department_outlined,
                  label: 'GMI',
                  value: gmi == null ? '--' : gmi!.toStringAsFixed(1),
                  suffix: gmi == null ? '' : '%',
                ),
              ),
            ],
          ),
          const SizedBox(height: 13),
          InkWell(
            onTap: () => GoRouter.of(context).go('/summary'),
            borderRadius: BorderRadius.circular(13),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFFEAF6EE),
                borderRadius: BorderRadius.circular(13),
              ),
              child: Row(
                children: [
                  Container(
                    width: 34,
                    height: 34,
                    decoration: const BoxDecoration(
                      color: Color(0xFFD8F0E1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.insights_rounded,
                      color: Color(0xFF0B8766),
                      size: 17,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      observation,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 10.3,
                        height: 1.3,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF27433A),
                      ),
                    ),
                  ),
                  const Icon(
                    Icons.chevron_right_rounded,
                    color: Color(0xFF0B8766),
                    size: 18,
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

class _MetricTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String suffix;

  const _MetricTile({
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
              color: Color(0xFFE8F4ED),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 17, color: const Color(0xFF0B8766)),
          ),
          const SizedBox(height: 7),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 9.5,
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

class _QuickActionsRow extends StatelessWidget {
  const _QuickActionsRow();

  @override
  Widget build(BuildContext context) {
    final actions = <({IconData icon, String label, String route})>[
      (
        icon: Icons.menu_book_outlined,
        label: _t(context, 'Journal', 'Journal', 'السجل'),
        route: '/journal',
      ),
      (
        icon: Icons.restaurant_outlined,
        label: _t(context, 'Alimentation', 'Food', 'التغذية'),
        route: '/ajouter?focus=meal',
      ),
      (
        icon: Icons.directions_run_rounded,
        label: _t(context, 'Activité', 'Activity', 'النشاط'),
        route: '/ajouter?focus=activity',
      ),
      (
        icon: Icons.medication_outlined,
        label: _t(context, 'Médicaments', 'Medications', 'الأدوية'),
        route: '/medications',
      ),
      (
        icon: Icons.notifications_none_rounded,
        label: _t(context, 'Rappels', 'Reminders', 'التذكيرات'),
        route: '/reminders',
      ),
    ];
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final action in actions)
          Expanded(
            child: InkWell(
              key: ValueKey('dashboard-action-${action.route}'),
              onTap: () => GoRouter.of(context).go(action.route),
              borderRadius: BorderRadius.circular(15),
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
                    child: Icon(
                      action.icon,
                      size: 20,
                      color: const Color(0xFF064E52),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    action.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 8.8,
                      fontWeight: FontWeight.w600,
                      color: AminaTheme.textPrimary(context),
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

class _DetailedTrendCard extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low;
  final double high;
  final String unit;

  const _DetailedTrendCard({
    required this.logs,
    required this.low,
    required this.high,
    required this.unit,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _t(context, 'Évolution récente', 'Recent trend', 'الاتجاه الأخير'),
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: AminaTheme.textPrimary(context),
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            height: 155,
            child: _MiniGlucoseChart(
              logs: logs,
              low: low,
              high: high,
              light: true,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            _t(
              context,
              'Courbe construite uniquement à partir des mesures enregistrées.',
              'Chart built only from recorded readings.',
              'تم إنشاء المنحنى فقط من القياسات المسجلة.',
            ),
            style: TextStyle(
              fontSize: 10.5,
              color: AminaTheme.textSecondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _MiniGlucoseChart extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low;
  final double high;
  final bool light;

  const _MiniGlucoseChart({
    required this.logs,
    required this.low,
    required this.high,
    this.light = false,
  });

  @override
  Widget build(BuildContext context) {
    final values = logs.take(14).toList().reversed.toList();
    if (values.length < 2) return const SizedBox.shrink();
    final spots = values
        .asMap()
        .entries
        .map((e) => FlSpot(e.key.toDouble(), e.value.bloodSugar))
        .toList();
    final observed = values.map((e) => e.bloodSugar);
    final minY = math.min(observed.reduce(math.min), low) - 12;
    final maxY = math.max(observed.reduce(math.max), high) + 12;
    final line = light ? const Color(0xFF0B9470) : const Color(0xFF74E7B2);
    final guide = light
        ? const Color(0xFF0B9470).withValues(alpha: 0.18)
        : Colors.white.withValues(alpha: 0.14);

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
              color: guide,
              strokeWidth: 1,
              dashArray: [4, 4],
            ),
            HorizontalLine(
              y: high,
              color: guide,
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
            color: line,
            barWidth: light ? 2.5 : 3,
            isStrokeCapRound: true,
            dotData: FlDotData(
              show: true,
              checkToShowDot: (spot, data) => spot.x == spots.last.x,
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  line.withValues(alpha: 0.18),
                  line.withValues(alpha: 0),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SealPainter extends CustomPainter {
  const _SealPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final stroke = Paint()
      ..color = const Color(0xFF075A5D)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.2
      ..strokeCap = StrokeCap.square
      ..strokeJoin = StrokeJoin.miter;
    final accent = Paint()
      ..color = const Color(0xFF27B984)
      ..style = PaintingStyle.fill;
    final s = size.width;
    final p = Path()
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
    canvas.drawPath(p, stroke);
    canvas.drawRect(Rect.fromLTWH(s * .84, s * .12, 6, 6), accent);
    canvas.drawRect(Rect.fromLTWH(s * .58, s * .40, 5, 5), accent);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ConvergentState extends StatelessWidget {
  final bool loading;
  final IconData icon;
  final String title;
  final String body;

  const _ConvergentState({
    this.loading = false,
    this.icon = Icons.hourglass_empty_rounded,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F5EF),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (loading)
                const CircularProgressIndicator()
              else
                Icon(icon, size: 34, color: AminaTheme.teal600),
              const SizedBox(height: 16),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 7),
              Text(body, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConvergentEmpty extends StatelessWidget {
  final VoidCallback onAdd;
  final VoidCallback onImport;

  const _ConvergentEmpty({required this.onAdd, required this.onImport});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: const Color(0xFFF8F5EF),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _BrandRow(),
              const Spacer(),
              Text(
                l10n.emptyDashboardTitle,
                style: const TextStyle(
                  fontSize: 27,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 8),
              Text(l10n.emptyDashboardBody),
              const SizedBox(height: 22),
              FilledButton(
                onPressed: onAdd,
                child: Text(l10n.addFirstMeasurement),
              ),
              const SizedBox(height: 10),
              OutlinedButton(
                onPressed: onImport,
                child: Text(l10n.importDocument),
              ),
              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }
}

String _t(BuildContext context, String fr, String en, String ar) {
  return switch (Localizations.localeOf(context).languageCode) {
    'ar' => ar,
    'en' => en,
    _ => fr,
  };
}
