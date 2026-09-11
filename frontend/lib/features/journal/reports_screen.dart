import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import 'ai_summary_screen.dart';

String _t(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

String _dateLocale(BuildContext context) => switch (
      Localizations.localeOf(context).languageCode,
    ) {
      'fr' => 'fr-FR',
      'ar' => 'ar-MA',
      'en' => 'en-US',
      _ => Localizations.localeOf(context).toLanguageTag(),
    };

class ReportsScreen extends StatelessWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    if (kOfflineDemo) return const _OfflineReportsScreen();
    return const AISummaryScreen();
  }
}

class _OfflineReportsScreen extends StatefulWidget {
  const _OfflineReportsScreen();

  @override
  State<_OfflineReportsScreen> createState() => _OfflineReportsScreenState();
}

class _OfflineReportsScreenState extends State<_OfflineReportsScreen> {
  int _days = 21;

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final end = DateTime.now().add(const Duration(minutes: 1));
    final start = end.subtract(Duration(days: _days));

    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: StreamBuilder<PatientProfileData?>(
        stream: db.watchProfile(),
        builder: (context, profileSnapshot) {
          return StreamBuilder<List<LogEntryData>>(
            stream: db.watchLogsInRange(start, end),
            builder: (context, logsSnapshot) {
              if (profileSnapshot.hasError || logsSnapshot.hasError) {
                return _StatePanel(
                  icon: Icons.cloud_off_outlined,
                  title: _t(
                    context,
                    'Rapport local indisponible',
                    'Local report unavailable',
                    'التقرير المحلي غير متاح',
                  ),
                  body: _t(
                    context,
                    'IAmina ne peut pas lire les mesures locales pour le moment.',
                    'IAmina cannot read local measurements right now.',
                    'يتعذر على IAmina قراءة القياسات المحلية حالياً.',
                  ),
                );
              }
              if (logsSnapshot.connectionState == ConnectionState.waiting &&
                  (logsSnapshot.data?.isEmpty ?? true)) {
                return _StatePanel(
                  loading: true,
                  title: _t(
                    context,
                    'Préparation du rapport',
                    'Preparing report',
                    'جارٍ إعداد التقرير',
                  ),
                  body: _t(
                    context,
                    'Lecture des mesures enregistrées sur cet appareil.',
                    'Reading measurements stored on this device.',
                    'تتم قراءة القياسات المحفوظة على هذا الجهاز.',
                  ),
                );
              }

              final logs = List<LogEntryData>.from(
                logsSnapshot.data ?? const <LogEntryData>[],
              )..sort((a, b) => _at(a).compareTo(_at(b)));
              final stats = _Stats.from(logs, profileSnapshot.data);
              return _ReportView(
                stats: stats,
                days: _days,
                onDaysChanged: (value) => setState(() => _days = value),
              );
            },
          );
        },
      ),
    );
  }

  static DateTime _at(LogEntryData log) => log.loggedAt ?? log.createdAt;
}

class _ReportView extends StatelessWidget {
  final _Stats stats;
  final int days;
  final ValueChanged<int> onDaysChanged;

  const _ReportView({
    required this.stats,
    required this.days,
    required this.onDaysChanged,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final wide = constraints.maxWidth >= 900;
        final padding = constraints.maxWidth >= 1200
            ? 36.0
            : constraints.maxWidth >= 700
                ? 26.0
                : 18.0;
        return SingleChildScrollView(
          padding: EdgeInsetsDirectional.fromSTEB(
            padding,
            22,
            padding,
            96,
          ),
          child: Align(
            alignment: AlignmentDirectional.topCenter,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1180),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _Header(days: days, onDaysChanged: onDaysChanged),
                  const SizedBox(height: 18),
                  if (stats.logs.isEmpty)
                    _EmptyReport(days: days)
                  else ...[
                    _Metrics(stats: stats),
                    const SizedBox(height: 18),
                    if (wide)
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            flex: 7,
                            child: _Distribution(stats: stats),
                          ),
                          const SizedBox(width: 18),
                          Expanded(flex: 5, child: _Latest(stats: stats)),
                        ],
                      )
                    else ...[
                      _Distribution(stats: stats),
                      const SizedBox(height: 18),
                      _Latest(stats: stats),
                    ],
                    const SizedBox(height: 18),
                    _TruthBoundary(count: stats.logs.length),
                  ],
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _Header extends StatelessWidget {
  final int days;
  final ValueChanged<int> onDaysChanged;

  const _Header({required this.days, required this.onDaysChanged});

  @override
  Widget build(BuildContext context) {
    return _Surface(
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 720;
          final copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: AminaVisualLanguage.mintSurface,
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: AminaVisualLanguage.mintBorder),
                ),
                child: Text(
                  _t(
                    context,
                    'MODE DÉMO · LOCAL',
                    'DEMO MODE · LOCAL',
                    'وضع تجريبي · محلي',
                  ),
                  style: const TextStyle(
                    color: AminaVisualLanguage.actionGreen,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w900,
                    letterSpacing: .3,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                _t(
                  context,
                  'Rapport de vos mesures',
                  'Measurement report',
                  'تقرير قياساتك',
                ),
                style: TextStyle(
                  fontFamily: 'Georgia',
                  fontSize: compact ? 27 : 32,
                  height: 1.05,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -.6,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
              const SizedBox(height: 7),
              Text(
                _t(
                  context,
                  'Synthèse calculée uniquement à partir des mesures enregistrées sur cet appareil.',
                  'Summary calculated only from measurements stored on this device.',
                  'ملخص محسوب فقط من القياسات المحفوظة على هذا الجهاز.',
                ),
                style: TextStyle(
                  fontSize: 13,
                  height: 1.45,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
            ],
          );
          final selector = _PeriodSelector(
            days: days,
            onChanged: onDaysChanged,
          );
          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [copy, const SizedBox(height: 18), selector],
            );
          }
          return Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(child: copy),
              const SizedBox(width: 24),
              selector,
            ],
          );
        },
      ),
    );
  }
}

class _PeriodSelector extends StatelessWidget {
  final int days;
  final ValueChanged<int> onChanged;

  const _PeriodSelector({required this.days, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [7, 21, 90].map((value) {
        final active = value == days;
        return InkWell(
          onTap: () => onChanged(value),
          borderRadius: BorderRadius.circular(999),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
            decoration: BoxDecoration(
              color: active
                  ? AminaVisualLanguage.forestDeep
                  : AminaVisualLanguage.controlSurface(context),
              borderRadius: BorderRadius.circular(999),
              border: Border.all(
                color: active
                    ? AminaVisualLanguage.forestDeep
                    : AminaVisualLanguage.controlBorder(context),
              ),
            ),
            child: Text(
              '$value j',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                color: active
                    ? Colors.white
                    : AminaVisualLanguage.secondary(context),
              ),
            ),
          ),
        );
      }).toList(growable: false),
    );
  }
}

class _Metrics extends StatelessWidget {
  final _Stats stats;

  const _Metrics({required this.stats});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 980
            ? 4
            : constraints.maxWidth >= 560
                ? 2
                : 1;
        return GridView.count(
          crossAxisCount: columns,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: columns == 4 ? 1.75 : columns == 2 ? 2.3 : 3.2,
          children: [
            _Metric(
              icon: Icons.fact_check_outlined,
              value: '${stats.logs.length}',
              label: _t(
                context,
                'Mesures enregistrées',
                'Recorded measurements',
                'القياسات المسجلة',
              ),
            ),
            _Metric(
              icon: Icons.analytics_outlined,
              value: '${stats.display(stats.average)} ${stats.unit}',
              label: _t(
                context,
                'Moyenne enregistrée',
                'Recorded average',
                'المتوسط المسجل',
              ),
            ),
            _Metric(
              icon: Icons.calendar_month_outlined,
              value: '${stats.daysCovered}',
              label: _t(
                context,
                'Jours renseignés',
                'Days with data',
                'أيام بها بيانات',
              ),
            ),
            _Metric(
              icon: Icons.adjust_rounded,
              value: stats.hasTarget
                  ? '${stats.inside}/${stats.logs.length}'
                  : '—',
              label: stats.hasTarget
                  ? _t(
                      context,
                      'Mesures dans la cible',
                      'Measurements in range',
                      'قياسات ضمن النطاق',
                    )
                  : _t(
                      context,
                      'Cible non configurée',
                      'Target not configured',
                      'النطاق غير مضبوط',
                    ),
            ),
          ],
        );
      },
    );
  }
}

class _Metric extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;

  const _Metric({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return _Surface(
      padding: 18,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 20, color: AminaVisualLanguage.actionGreen),
          const SizedBox(height: 9),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontFamily: 'Georgia',
              fontSize: 25,
              height: 1,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.primaryText(context),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            label,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 11.5,
              height: 1.3,
              fontWeight: FontWeight.w600,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _Distribution extends StatelessWidget {
  final _Stats stats;

  const _Distribution({required this.stats});

  @override
  Widget build(BuildContext context) {
    final ratio = stats.hasTarget && stats.logs.isNotEmpty
        ? stats.inside / stats.logs.length
        : 0.0;
    return _Surface(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _title(
            context,
            _t(
              context,
              'Répartition des mesures',
              'Measurement distribution',
              'توزيع القياسات',
            ),
          ),
          const SizedBox(height: 6),
          Text(
            stats.hasTarget
                ? _t(
                    context,
                    'Lecture descriptive par rapport à votre cible configurée.',
                    'Descriptive view against your configured target range.',
                    'عرض وصفي مقارنة بالنطاق المحدد لديك.',
                  )
                : _t(
                    context,
                    'Configurez une cible pour obtenir la répartition sous / dans / au-dessus.',
                    'Configure a target to see below / in-range / above distribution.',
                    'اضبط نطاقاً لعرض القياسات أسفل / داخل / أعلى النطاق.',
                  ),
            style: TextStyle(
              fontSize: 12.5,
              height: 1.4,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
          const SizedBox(height: 22),
          if (stats.hasTarget) ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${(ratio * 100).round()}%',
                  style: TextStyle(
                    fontFamily: 'Georgia',
                    fontSize: 38,
                    height: .95,
                    fontWeight: FontWeight.w700,
                    color: AminaVisualLanguage.primaryText(context),
                  ),
                ),
                const SizedBox(width: 9),
                Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Text(
                    _t(context, 'dans la cible', 'in range', 'ضمن النطاق'),
                    style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w700,
                      color: AminaVisualLanguage.secondary(context),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                value: ratio.clamp(0.0, 1.0).toDouble(),
                minHeight: 12,
                backgroundColor: AminaVisualLanguage.controlSurface(context),
                valueColor: const AlwaysStoppedAnimation<Color>(
                  AminaVisualLanguage.actionGreen,
                ),
              ),
            ),
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: _SmallStat(
                    value: stats.below,
                    label: _t(context, 'Sous', 'Below', 'أدنى'),
                  ),
                ),
                Expanded(
                  child: _SmallStat(
                    value: stats.inside,
                    label: _t(
                      context,
                      'Dans cible',
                      'In range',
                      'ضمن النطاق',
                    ),
                  ),
                ),
                Expanded(
                  child: _SmallStat(
                    value: stats.above,
                    label: _t(context, 'Au-dessus', 'Above', 'أعلى'),
                  ),
                ),
              ],
            ),
          ] else
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AminaVisualLanguage.controlSurface(context),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: AminaVisualLanguage.controlBorder(context),
                ),
              ),
              child: Text(
                _t(
                  context,
                  'Aucune classification n’est inventée tant que la cible personnelle n’est pas configurée.',
                  'No classification is invented until a personal target range is configured.',
                  'لا يتم اختراع أي تصنيف قبل ضبط النطاق الشخصي.',
                ),
                style: TextStyle(
                  fontSize: 12.5,
                  height: 1.4,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _SmallStat extends StatelessWidget {
  final int value;
  final String label;

  const _SmallStat({required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$value',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: AminaVisualLanguage.primaryText(context),
          ),
        ),
        const SizedBox(height: 3),
        Text(
          label,
          style: TextStyle(
            fontSize: 11.5,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
      ],
    );
  }
}

class _Latest extends StatelessWidget {
  final _Stats stats;

  const _Latest({required this.stats});

  @override
  Widget build(BuildContext context) {
    final latest = stats.logs.last;
    final at = latest.loggedAt ?? latest.createdAt;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: AminaVisualLanguage.primaryGradient,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withValues(alpha: .16)),
        boxShadow: AminaVisualLanguage.cardShadow(context),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _t(
              context,
              'Dernière mesure enregistrée',
              'Latest recorded measurement',
              'آخر قياس مسجل',
            ),
            style: TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w700,
              color: Colors.white.withValues(alpha: .78),
            ),
          ),
          const SizedBox(height: 18),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                stats.display(latest.bloodSugar),
                style: const TextStyle(
                  fontFamily: 'Georgia',
                  fontSize: 46,
                  height: .9,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
              const SizedBox(width: 7),
              Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text(
                  stats.unit,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: Colors.white.withValues(alpha: .75),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            DateFormat('d MMM · HH:mm', _dateLocale(context)).format(at),
            style: TextStyle(
              fontSize: 12.5,
              color: Colors.white.withValues(alpha: .78),
            ),
          ),
          if (latest.glycemicContext != null || latest.mealType != null) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: [
                if (latest.glycemicContext != null)
                  _Tag(_contextLabel(context, latest.glycemicContext!)),
                if (latest.mealType != null)
                  _Tag(_contextLabel(context, latest.mealType!)),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  final String label;
  const _Tag(this.label);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: .12),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withValues(alpha: .16)),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 10.5,
          fontWeight: FontWeight.w700,
          color: Colors.white,
        ),
      ),
    );
  }
}

class _TruthBoundary extends StatelessWidget {
  final int count;
  const _TruthBoundary({required this.count});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AminaVisualLanguage.mintBorder),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.verified_user_outlined,
            size: 22,
            color: AminaVisualLanguage.actionGreen,
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _t(
                    context,
                    'Ce rapport reste descriptif',
                    'This report stays descriptive',
                    'هذا التقرير وصفي فقط',
                  ),
                  style: const TextStyle(
                    color: AminaVisualLanguage.forestDeep,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  _t(
                    context,
                    'En mode démo hors ligne, IAmina calcule uniquement des statistiques sur $count mesures locales. Elle n’invente ni cause, ni diagnostic, ni analyse IA avancée.',
                    'In offline demo mode, IAmina only calculates statistics from $count local measurements. It does not invent causes, diagnoses, or advanced AI analysis.',
                    'في الوضع التجريبي دون اتصال، تحسب IAmina إحصاءات فقط من $count قياساً محلياً ولا تختلق أسباباً أو تشخيصاً أو تحليلاً متقدماً بالذكاء الاصطناعي.',
                  ),
                  style: const TextStyle(
                    color: AminaVisualLanguage.forestDeep,
                    fontSize: 12.5,
                    height: 1.45,
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

class _EmptyReport extends StatelessWidget {
  final int days;
  const _EmptyReport({required this.days});

  @override
  Widget build(BuildContext context) {
    return _Surface(
      padding: 42,
      child: Column(
        children: [
          const Icon(
            Icons.analytics_outlined,
            size: 38,
            color: AminaVisualLanguage.actionGreen,
          ),
          const SizedBox(height: 14),
          Text(
            _t(
              context,
              'Aucune mesure sur $days jours',
              'No measurements in the last $days days',
              'لا توجد قياسات خلال آخر $days يوماً',
            ),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'Georgia',
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.primaryText(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _Surface extends StatelessWidget {
  final Widget child;
  final double padding;

  const _Surface({required this.child, this.padding = 22});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(padding),
      decoration: AminaVisualLanguage.cardDecoration(context, radius: 24),
      child: child,
    );
  }
}

class _StatePanel extends StatelessWidget {
  final IconData? icon;
  final bool loading;
  final String title;
  final String body;

  const _StatePanel({
    this.icon,
    this.loading = false,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (loading)
              const CircularProgressIndicator()
            else
              Icon(
                icon ?? Icons.info_outline,
                size: 40,
                color: AminaVisualLanguage.actionGreen,
              ),
            const SizedBox(height: 16),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Georgia',
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: AminaVisualLanguage.primaryText(context),
              ),
            ),
            const SizedBox(height: 7),
            Text(
              body,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12.5,
                height: 1.4,
                color: AminaVisualLanguage.secondary(context),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Stats {
  final List<LogEntryData> logs;
  final String unit;
  final double average;
  final int daysCovered;
  final double? low;
  final double? high;
  final int below;
  final int inside;
  final int above;

  const _Stats({
    required this.logs,
    required this.unit,
    required this.average,
    required this.daysCovered,
    required this.low,
    required this.high,
    required this.below,
    required this.inside,
    required this.above,
  });

  bool get hasTarget => low != null && high != null && low! < high!;

  String display(double mgDl) => unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

  factory _Stats.from(List<LogEntryData> logs, PatientProfileData? profile) {
    final unit = profile?.unitPreference ?? 'mg/dL';
    final low = profile?.targetRangeLow;
    final high = profile?.targetRangeHigh;
    final average = logs.isEmpty
        ? 0.0
        : logs.fold<double>(0.0, (sum, log) => sum + log.bloodSugar) /
              logs.length;
    final daysCovered = logs.map((log) {
      final at = log.loggedAt ?? log.createdAt;
      return '${at.year}-${at.month}-${at.day}';
    }).toSet().length;

    var below = 0;
    var inside = 0;
    var above = 0;
    if (low != null && high != null && low < high) {
      for (final log in logs) {
        if (log.bloodSugar < low) {
          below++;
        } else if (log.bloodSugar > high) {
          above++;
        } else {
          inside++;
        }
      }
    }

    return _Stats(
      logs: logs,
      unit: unit,
      average: average,
      daysCovered: daysCovered,
      low: low,
      high: high,
      below: below,
      inside: inside,
      above: above,
    );
  }
}

Text _title(BuildContext context, String value) => Text(
      value,
      style: TextStyle(
        fontFamily: 'Georgia',
        fontSize: 21,
        fontWeight: FontWeight.w700,
        color: AminaVisualLanguage.primaryText(context),
      ),
    );

String _contextLabel(BuildContext context, String key) =>
    switch (key.trim().toLowerCase()) {
      'fasting' => _t(context, 'À jeun', 'Fasting', 'صائم'),
      'pre_meal' => _t(context, 'Avant repas', 'Before meal', 'قبل الوجبة'),
      'post_meal' => _t(context, 'Après repas', 'After meal', 'بعد الوجبة'),
      'breakfast' => _t(context, 'Petit-déjeuner', 'Breakfast', 'الفطور'),
      'lunch' => _t(context, 'Déjeuner', 'Lunch', 'الغداء'),
      'dinner' => _t(context, 'Dîner', 'Dinner', 'العشاء'),
      _ => key,
    };
