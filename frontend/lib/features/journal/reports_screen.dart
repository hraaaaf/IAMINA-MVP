import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import 'ai_summary_screen.dart';

String _reportsText(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

String _reportsLocale(BuildContext context) {
  final locale = Localizations.localeOf(context);
  return switch (locale.languageCode) {
    'fr' => 'fr-FR',
    'ar' => 'ar-MA',
    'en' => 'en-US',
    _ => locale.toLanguageTag(),
  };
}

class ReportsScreen extends StatelessWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    if (kOfflineDemo) return const _OfflineDemoReportsScreen();
    return const AISummaryScreen();
  }
}

class _OfflineDemoReportsScreen extends StatefulWidget {
  const _OfflineDemoReportsScreen();

  @override
  State<_OfflineDemoReportsScreen> createState() =>
      _OfflineDemoReportsScreenState();
}

class _OfflineDemoReportsScreenState extends State<_OfflineDemoReportsScreen> {
  int _periodDays = 21;

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final now = DateTime.now();
    final start = now.subtract(Duration(days: _periodDays));

    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: StreamBuilder<PatientProfileData?>(
        stream: db.watchProfile(),
        builder: (context, profileSnapshot) {
          return StreamBuilder<List<LogEntryData>>(
            stream: db.watchLogsInRange(
              start,
              now.add(const Duration(minutes: 1)),
            ),
            builder: (context, logsSnapshot) {
              if (logsSnapshot.hasError || profileSnapshot.hasError) {
                return _ReportState(
                  icon: Icons.cloud_off_outlined,
                  title: _reportsText(
                    context,
                    'Rapport local indisponible',
                    'Local report unavailable',
                    'التقرير المحلي غير متاح',
                  ),
                  body: _reportsText(
                    context,
                    'IAmina ne peut pas lire les mesures locales pour le moment.',
                    'IAmina cannot read local measurements right now.',
                    'يتعذر على IAmina قراءة القياسات المحلية حالياً.',
                  ),
                );
              }

              if (logsSnapshot.connectionState == ConnectionState.waiting &&
                  (logsSnapshot.data?.isEmpty ?? true)) {
                return _ReportState(
                  loading: true,
                  title: _reportsText(
                    context,
                    'Préparation du rapport',
                    'Preparing report',
                    'جارٍ إعداد التقرير',
                  ),
                  body: _reportsText(
                    context,
                    'Lecture des mesures enregistrées sur cet appareil.',
                    'Reading measurements stored on this device.',
                    'تتم قراءة القياسات المحفوظة على هذا الجهاز.',
                  ),
                );
              }

              final logs = List<LogEntryData>.from(
                logsSnapshot.data ?? const <LogEntryData>[],
              )..sort(
                  (a, b) => _recordedAt(a).compareTo(_recordedAt(b)),
                );
              final stats = _LocalReportStats.from(
                logs: logs,
                profile: profileSnapshot.data,
              );

              return _OfflineReportBody(
                stats: stats,
                periodDays: _periodDays,
                onPeriodChanged: (days) => setState(() => _periodDays = days),
              );
            },
          );
        },
      ),
    );
  }

  static DateTime _recordedAt(LogEntryData log) =>
      log.loggedAt ?? log.createdAt;
}

class _OfflineReportBody extends StatelessWidget {
  final _LocalReportStats stats;
  final int periodDays;
  final ValueChanged<int> onPeriodChanged;

  const _OfflineReportBody({
    required this.stats,
    required this.periodDays,
    required this.onPeriodChanged,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final wide = constraints.maxWidth >= 900;
        final horizontalPadding = constraints.maxWidth >= 1280
            ? 40.0
            : constraints.maxWidth >= 700
            ? 28.0
            : 18.0;

        return SingleChildScrollView(
          padding: EdgeInsetsDirectional.fromSTEB(
            horizontalPadding,
            22,
            horizontalPadding,
            96,
          ),
          child: Align(
            alignment: AlignmentDirectional.topCenter,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1180),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _ReportHeader(
                    periodDays: periodDays,
                    onPeriodChanged: onPeriodChanged,
                  ),
                  const SizedBox(height: 18),
                  if (stats.logs.isEmpty)
                    _EmptyLocalReport(periodDays: periodDays)
                  else ...[
                    _KpiGrid(stats: stats),
                    const SizedBox(height: 18),
                    if (wide)
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            flex: 7,
                            child: _DistributionCard(stats: stats),
                          ),
                          const SizedBox(width: 18),
                          Expanded(
                            flex: 5,
                            child: _LatestReadingCard(stats: stats),
                          ),
                        ],
                      )
                    else ...[
                      _DistributionCard(stats: stats),
                      const SizedBox(height: 18),
                      _LatestReadingCard(stats: stats),
                    ],
                    const SizedBox(height: 18),
                    _TruthBoundaryCard(stats: stats),
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

class _ReportHeader extends StatelessWidget {
  final int periodDays;
  final ValueChanged<int> onPeriodChanged;

  const _ReportHeader({
    required this.periodDays,
    required this.onPeriodChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: AminaTheme.isDark(context)
            ? null
            : const LinearGradient(
                colors: [Color(0xFFFFFFFF), Color(0xFFF1FBF8)],
                begin: AlignmentDirectional.topStart,
                end: AlignmentDirectional.bottomEnd,
              ),
        color: AminaTheme.isDark(context)
            ? AminaTheme.surface(context)
            : null,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
        boxShadow: AminaVisualLanguage.cardShadow(context),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 720;
          final copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AminaVisualLanguage.mintSurface,
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: AminaVisualLanguage.mintBorder),
                ),
                child: Text(
                  _reportsText(
                    context,
                    'MODE DÉMO · LOCAL',
                    'DEMO MODE · LOCAL',
                    'وضع تجريبي · محلي',
                  ),
                  style: const TextStyle(
                    color: AminaVisualLanguage.actionGreen,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w900,
                    letterSpacing: .35,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                _reportsText(
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
                _reportsText(
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
            selected: periodDays,
            onChanged: onPeriodChanged,
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
  final int selected;
  final ValueChanged<int> onChanged;

  const _PeriodSelector({required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [7, 21, 90].map((days) {
        final active = days == selected;
        return InkWell(
          onTap: () => onChanged(days),
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
              '$days j',
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

class _KpiGrid extends StatelessWidget {
  final _LocalReportStats stats;

  const _KpiGrid({required this.stats});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 980
            ? 4
            : constraints.maxWidth >= 560
            ? 2
            : 1;
        final ratio = columns == 1 ? 3.2 : columns == 2 ? 2.3 : 1.75;
        return GridView.count(
          crossAxisCount: columns,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: ratio,
          children: [
            _MetricCard(
              icon: Icons.fact_check_outlined,
              value: '${stats.logs.length}',
              label: _reportsText(
                context,
                'Mesures enregistrées',
                'Recorded measurements',
                'القياسات المسجلة',
              ),
            ),
            _MetricCard(
              icon: Icons.analytics_outlined,
              value: '${stats.displayValue(stats.average)} ${stats.unit}',
              label: _reportsText(
                context,
                'Moyenne enregistrée',
                'Recorded average',
                'المتوسط المسجل',
              ),
            ),
            _MetricCard(
              icon: Icons.calendar_month_outlined,
              value: '${stats.daysCovered}',
              label: _reportsText(
                context,
                'Jours renseignés',
                'Days with data',
                'أيام بها بيانات',
              ),
            ),
            _MetricCard(
              icon: Icons.adjust_rounded,
              value: stats.hasTarget
                  ? '${stats.inTarget}/${stats.logs.length}'
                  : '—',
              label: stats.hasTarget
                  ? _reportsText(
                      context,
                      'Mesures dans la cible',
                      'Measurements in range',
                      'قياسات ضمن النطاق',
                    )
                  : _reportsText(
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

class _MetricCard extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;

  const _MetricCard({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: AminaVisualLanguage.cardDecoration(context, radius: 22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 20, color: AminaVisualLanguage.actionGreen),
          const SizedBox(height: 10),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontFamily: 'Georgia',
              fontSize: 25,
              height: 1,
              fontWeight: FontWeight.w700,
              letterSpacing: -.35,
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

class _DistributionCard extends StatelessWidget {
  final _LocalReportStats stats;

  const _DistributionCard({required this.stats});

  @override
  Widget build(BuildContext context) {
    final ratio = stats.hasTarget && stats.logs.isNotEmpty
        ? stats.inTarget / stats.logs.length
        : 0.0;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: AminaVisualLanguage.cardDecoration(context, radius: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _reportsText(
              context,
              'Répartition des mesures',
              'Measurement distribution',
              'توزيع القياسات',
            ),
            style: TextStyle(
              fontFamily: 'Georgia',
              fontSize: 21,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.primaryText(context),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            stats.hasTarget
                ? _reportsText(
                    context,
                    'Lecture descriptive par rapport à votre cible configurée.',
                    'Descriptive view against your configured target range.',
                    'عرض وصفي مقارنة بالنطاق المحدد لديك.',
                  )
                : _reportsText(
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
                    _reportsText(
                      context,
                      'dans la cible',
                      'in range',
                      'ضمن النطاق',
                    ),
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
                value: ratio.clamp(0.0, 1.0),
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
                  child: _DistributionStat(
                    label: _reportsText(
                      context,
                      'Sous',
                      'Below',
                      'أدنى',
                    ),
                    value: stats.belowTarget,
                  ),
                ),
                Expanded(
                  child: _DistributionStat(
                    label: _reportsText(
                      context,
                      'Dans cible',
                      'In range',
                      'ضمن النطاق',
                    ),
                    value: stats.inTarget,
                  ),
                ),
                Expanded(
                  child: _DistributionStat(
                    label: _reportsText(
                      context,
                      'Au-dessus',
                      'Above',
                      'أعلى',
                    ),
                    value: stats.aboveTarget,
                  ),
                ),
              ],
            ),
          ] else
            _TargetMissingState(),
        ],
      ),
    );
  }
}

class _DistributionStat extends StatelessWidget {
  final String label;
  final int value;

  const _DistributionStat({required this.label, required this.value});

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

class _TargetMissingState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(context),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
      ),
      child: Row(
        children: [
          const Icon(Icons.tune_rounded, color: AminaVisualLanguage.actionGreen),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              _reportsText(
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

class _LatestReadingCard extends StatelessWidget {
  final _LocalReportStats stats;

  const _LatestReadingCard({required this.stats});

  @override
  Widget build(BuildContext context) {
    final latest = stats.latest!;
    final at = latest.loggedAt ?? latest.createdAt;
    final locale = _reportsLocale(context);
    final tags = <String>[
      if (latest.glycemicContext != null)
        _contextLabel(context, latest.glycemicContext!),
      if (latest.mealType != null) _contextLabel(context, latest.mealType!),
    ].where((item) => item.trim().isNotEmpty).toList(growable: false);

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
            _reportsText(
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
                stats.displayValue(latest.bloodSugar),
                style: const TextStyle(
                  fontFamily: 'Georgia',
                  fontSize: 46,
                  height: .9,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                  letterSpacing: -1.2,
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
            DateFormat('d MMM · HH:mm', locale).format(at),
            style: TextStyle(
              fontSize: 12.5,
              color: Colors.white.withValues(alpha: .78),
            ),
          ),
          if (tags.isNotEmpty) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: tags
                  .map(
                    (tag) => Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: .12),
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: .16),
                        ),
                      ),
                      child: Text(
                        tag,
                        style: const TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  )
                  .toList(growable: false),
            ),
          ],
        ],
      ),
    );
  }
}

class _TruthBoundaryCard extends StatelessWidget {
  final _LocalReportStats stats;

  const _TruthBoundaryCard({required this.stats});

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
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .72),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.verified_user_outlined,
              size: 20,
              color: AminaVisualLanguage.actionGreen,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _reportsText(
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
                  _reportsText(
                    context,
                    'En mode démo hors ligne, IAmina calcule uniquement des statistiques sur ${stats.logs.length} mesures locales. Elle n’invente ni cause, ni diagnostic, ni analyse IA avancée.',
                    'In offline demo mode, IAmina only calculates statistics from ${stats.logs.length} local measurements. It does not invent causes, diagnoses, or advanced AI analysis.',
                    'في الوضع التجريبي دون اتصال، تحسب IAmina إحصاءات فقط من ${stats.logs.length} قياساً محلياً ولا تختلق أسباباً أو تشخيصاً أو تحليلاً متقدماً بالذكاء الاصطناعي.',
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

class _EmptyLocalReport extends StatelessWidget {
  final int periodDays;

  const _EmptyLocalReport({required this.periodDays});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 46),
      decoration: AminaVisualLanguage.cardDecoration(context, radius: 24),
      child: Column(
        children: [
          const Icon(
            Icons.analytics_outlined,
            size: 38,
            color: AminaVisualLanguage.actionGreen,
          ),
          const SizedBox(height: 14),
          Text(
            _reportsText(
              context,
              'Aucune mesure sur $periodDays jours',
              'No measurements in the last $periodDays days',
              'لا توجد قياسات خلال آخر $periodDays يوماً',
            ),
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
            _reportsText(
              context,
              'Le rapport apparaîtra dès que des mesures seront enregistrées.',
              'The report will appear as soon as measurements are recorded.',
              'سيظهر التقرير بمجرد تسجيل القياسات.',
            ),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 12.5,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _ReportState extends StatelessWidget {
  final IconData? icon;
  final bool loading;
  final String title;
  final String body;

  const _ReportState({
    this.icon,
    this.loading = false,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 520),
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
      ),
    );
  }
}

class _LocalReportStats {
  final List<LogEntryData> logs;
  final String unit;
  final double average;
  final int daysCovered;
  final double? low;
  final double? high;
  final int belowTarget;
  final int inTarget;
  final int aboveTarget;

  const _LocalReportStats({
    required this.logs,
    required this.unit,
    required this.average,
    required this.daysCovered,
    required this.low,
    required this.high,
    required this.belowTarget,
    required this.inTarget,
    required this.aboveTarget,
  });

  bool get hasTarget => low != null && high != null && low! < high!;
  LogEntryData? get latest => logs.isEmpty ? null : logs.last;

  String displayValue(double valueMgDl) => unit == 'mmol/L'
      ? (valueMgDl / 18.0).toStringAsFixed(1)
      : valueMgDl.toStringAsFixed(0);

  factory _LocalReportStats.from({
    required List<LogEntryData> logs,
    required PatientProfileData? profile,
  }) {
    final unit = profile?.unitPreference ?? 'mg/dL';
    final low = profile?.targetRangeLow;
    final high = profile?.targetRangeHigh;
    final hasTarget = low != null && high != null && low < high;
    final average = logs.isEmpty
        ? 0.0
        : logs.fold<double>(0, (sum, log) => sum + log.bloodSugar) /
              logs.length;
    final days = logs
        .map((log) {
          final at = log.loggedAt ?? log.createdAt;
          return '${at.year}-${at.month}-${at.day}';
        })
        .toSet()
        .length;
    var below = 0;
    var inside = 0;
    var above = 0;
    if (hasTarget) {
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
    return _LocalReportStats(
      logs: logs,
      unit: unit,
      average: average,
      daysCovered: days,
      low: low,
      high: high,
      belowTarget: below,
      inTarget: inside,
      aboveTarget: above,
    );
  }
}

String _contextLabel(BuildContext context, String key) {
  final normalized = key.trim().toLowerCase();
  return switch (normalized) {
    'fasting' => _reportsText(context, 'À jeun', 'Fasting', 'صائم'),
    'pre_meal' => _reportsText(context, 'Avant repas', 'Before meal', 'قبل الوجبة'),
    'post_meal' => _reportsText(context, 'Après repas', 'After meal', 'بعد الوجبة'),
    'breakfast' => _reportsText(context, 'Petit-déjeuner', 'Breakfast', 'الفطور'),
    'lunch' => _reportsText(context, 'Déjeuner', 'Lunch', 'الغداء'),
    'dinner' => _reportsText(context, 'Dîner', 'Dinner', 'العشاء'),
    'other' => _reportsText(context, 'Autre', 'Other', 'أخرى'),
    _ => key,
  };
}
