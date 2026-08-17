import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/localization/dashboard_localized_copy.dart';
import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/companion_service.dart';
import 'widgets/dashboard_adaptive_kpi_section.dart';
import 'widgets/dashboard_insight_section.dart';
import 'widgets/dashboard_next_action_section.dart';
import 'widgets/dashboard_today_section.dart';
import 'widgets/dashboard_trend_section.dart';

String _t(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

const _futureTimestampTolerance = Duration(minutes: 5);

bool _readingTimestampNeedsReview(DateTime latestAt) => latestAt.isAfter(
      DateTime.now().add(_futureTimestampTolerance),
    );

Duration _safeReadingAge(DateTime latestAt) {
  final age = DateTime.now().difference(latestAt);
  return age.isNegative ? Duration.zero : age;
}

String _latestReadingFreshnessLabel(BuildContext context, DateTime latestAt) {
  final l10n = AppLocalizations.of(context)!;
  if (_readingTimestampNeedsReview(latestAt)) {
    return l10n.dashboardTimestampNeedsReview;
  }
  final age = _safeReadingAge(latestAt);
  if (age.inMinutes < 1) return l10n.dashboardFreshNow;
  if (age.inMinutes < 60) return l10n.dashboardFreshMinutes(age.inMinutes);
  if (age.inHours < 24) return l10n.dashboardFreshHours(age.inHours);
  return l10n.dashboardFreshDays(age.inDays);
}

bool _sameCalendarDay(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

String _latestReadingTimestampLabel(
  BuildContext context,
  DateTime latestAt,
  String locale,
) {
  final now = DateTime.now();
  final time = DateFormat('HH:mm', locale).format(latestAt);
  final l10n = AppLocalizations.of(context)!;
  if (_sameCalendarDay(now, latestAt)) return l10n.dashboardTodayAt(time);
  final yesterday = now.subtract(const Duration(days: 1));
  if (_sameCalendarDay(yesterday, latestAt)) {
    return l10n.dashboardYesterdayAt(time);
  }
  return DateFormat('d MMM · HH:mm', locale).format(latestAt);
}

class DashboardPremiumScreen extends StatelessWidget {
  final CompanionService? companionService;

  const DashboardPremiumScreen({super.key, this.companionService});

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();

    return StreamBuilder<PatientProfileData?>(
      stream: db.watchProfile(),
      builder: (context, profileSnap) {
        final profile = profileSnap.data;
        final unit = profile?.unitPreference ?? 'mg/dL';
        final low = profile?.targetRangeLow;
        final high = profile?.targetRangeHigh;

        return StreamBuilder<List<LogEntryData>>(
          stream: db.watchRecentLogs(limit: 1),
          builder: (context, logsSnap) {
            if (profileSnap.hasError || logsSnap.hasError) {
              return _PremiumState(
                icon: Icons.cloud_off_rounded,
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
              return _PremiumState(
                loading: true,
                title: _t(
                  context,
                  'Préparation',
                  'Preparing',
                  'جارٍ التحضير',
                ),
                body: _t(
                  context,
                  'IAmina prépare votre espace santé.',
                  'IAmina is preparing your health space.',
                  'تقوم IAmina بإعداد مساحتك الصحية.',
                ),
              );
            }

            final logs = [...?logsSnap.data]
              ..sort(
                (a, b) => (b.loggedAt ?? b.createdAt).compareTo(
                  a.loggedAt ?? a.createdAt,
                ),
              );

            return _DashboardBody(
              logs: logs,
              unit: unit,
              low: low,
              high: high,
              companionService: companionService,
            );
          },
        );
      },
    );
  }
}

class _DashboardBody extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final double? low;
  final double? high;
  final CompanionService? companionService;

  const _DashboardBody({
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
    required this.companionService,
  });

  String _display(double mg) => unit == 'mmol/L'
      ? (mg / 18.0).toStringAsFixed(1)
      : mg.toStringAsFixed(0);

  @override
  Widget build(BuildContext context) {
    final latest = logs.isEmpty ? null : logs.first;
    final latestAt = latest == null ? null : (latest.loggedAt ?? latest.createdAt);
    final hasTarget = low != null && high != null && low! < high!;
    final inRange =
        latest != null &&
        hasTarget &&
        latest.bloodSugar >= low! &&
        latest.bloodSugar <= high!;
    final highValue = latest != null && hasTarget && latest.bloodSugar > high!;
    final locale = Localizations.localeOf(context).toLanguageTag();

    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: Stack(
        children: [
          const Positioned.fill(child: _AmbientBackground()),
          SafeArea(
            bottom: false,
            child: CustomScrollView(
              physics: const BouncingScrollPhysics(),
              slivers: [
                SliverPadding(
                  padding: const EdgeInsetsDirectional.fromSTEB(
                    20,
                    16,
                    20,
                    128,
                  ),
                  sliver: SliverList(
                    delegate: SliverChildListDelegate([
                      const _PremiumBrandHeader(),
                      const SizedBox(height: 22),
                      Text(
                        _t(context, 'Bonjour', 'Welcome back', 'مرحباً'),
                        style: TextStyle(
                          fontFamily: 'Georgia',
                          fontSize: 31,
                          height: 1.02,
                          fontWeight: FontWeight.w700,
                          letterSpacing: -.8,
                          color: AminaVisualLanguage.primaryText(context),
                        ),
                      ),
                      const SizedBox(height: 18),
                      _LatestReadingCard(
                        latest: latest,
                        latestAt: latestAt,
                        display: latest == null
                            ? '—'
                            : _display(latest.bloodSugar),
                        unit: unit,
                        status: latest == null
                            ? _t(
                                context,
                                'Aucune mesure',
                                'No reading yet',
                                'لا توجد قراءة بعد',
                              )
                            : !hasTarget
                            ? AppLocalizations.of(
                                context,
                              )!.dashboardTargetNotConfigured
                            : inRange
                            ? _t(
                                context,
                                'Dans votre cible',
                                'In your range',
                                'ضمن نطاقك',
                              )
                            : highValue
                            ? _t(
                                context,
                                'Au-dessus de la cible',
                                'Above range',
                                'فوق النطاق',
                              )
                            : _t(
                                context,
                                'Sous la cible',
                                'Below range',
                                'تحت النطاق',
                              ),
                        inRange: inRange,
                        targetConfigured: hasTarget,
                        locale: locale,
                      ),
                      const SizedBox(height: 18),
                      DashboardTodaySection(
                        targetConfigured: hasTarget,
                        service: companionService,
                      ),
                      const SizedBox(height: 18),
                      DashboardTrendSection(
                        unit: unit,
                        low: low,
                        high: high,
                      ),
                      const SizedBox(height: 18),
                      DashboardAdaptiveKpiSection(
                        unit: unit,
                        low: low,
                        high: high,
                      ),
                      const SizedBox(height: 18),
                      DashboardInsightSection(service: companionService),
                      const SizedBox(height: 18),
                      DashboardNextActionSection(service: companionService),
                    ]),
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

class _PremiumBrandHeader extends StatelessWidget {
  const _PremiumBrandHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 72,
          height: 72,
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: .86),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: Colors.white.withValues(alpha: .95)),
            boxShadow: AminaVisualLanguage.cardShadowLight,
          ),
          child: Image.asset(
            'assets/images/logo_amina.png',
            fit: BoxFit.contain,
            filterQuality: FilterQuality.high,
          ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'IAmina',
                style: TextStyle(
                  fontSize: 22,
                  height: 1,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -.6,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
              const SizedBox(height: 5),
              Text(
                _t(
                  context,
                  'Votre compagnon du diabète',
                  'Your diabetes companion',
                  'رفيقك لمرض السكري',
                ),
                style: TextStyle(
                  fontSize: 12.5,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
            ],
          ),
        ),
        IconButton(
          key: const ValueKey('dashboard-reminders-action'),
          onPressed: () => context.go('/reminders'),
          icon: const Icon(Icons.notifications_none_rounded),
          style: IconButton.styleFrom(
            minimumSize: const Size(48, 48),
            backgroundColor: AminaVisualLanguage.controlSurface(context),
            foregroundColor: AminaVisualLanguage.forestDeep,
            side: BorderSide(
              color: AminaVisualLanguage.controlBorder(context),
            ),
          ),
        ),
      ],
    );
  }
}

class _LatestReadingCard extends StatelessWidget {
  final LogEntryData? latest;
  final DateTime? latestAt;
  final String display;
  final String unit;
  final String status;
  final bool inRange;
  final bool targetConfigured;
  final String locale;

  const _LatestReadingCard({
    required this.latest,
    required this.latestAt,
    required this.display,
    required this.unit,
    required this.status,
    required this.inRange,
    required this.targetConfigured,
    required this.locale,
  });

  @override
  Widget build(BuildContext context) {
    final hasData = latest != null && latestAt != null;
    final timestampNeedsReview =
        latestAt != null && _readingTimestampNeedsReview(latestAt!);
    final freshness = latestAt == null
        ? null
        : _latestReadingFreshnessLabel(context, latestAt!);
    final timestamp = latestAt == null
        ? null
        : _latestReadingTimestampLabel(context, latestAt!, locale);
    final foreground = hasData
        ? Colors.white
        : AminaVisualLanguage.primaryText(context);
    final secondary = hasData
        ? Colors.white.withValues(alpha: .78)
        : AminaVisualLanguage.secondary(context);
    final neutralStatus = hasData && !targetConfigured;
    final statusForeground = hasData && (inRange || neutralStatus)
        ? Colors.white
        : AminaVisualLanguage.primaryText(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: hasData
          ? BoxDecoration(
              gradient: AminaVisualLanguage.primaryGradient,
              borderRadius: BorderRadius.circular(26),
              border: Border.all(color: Colors.white.withValues(alpha: .18)),
              boxShadow: AminaVisualLanguage.cardShadow(context),
            )
          : AminaVisualLanguage.cardDecoration(context, radius: 26),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.water_drop_outlined,
                color: hasData
                    ? Colors.white.withValues(alpha: .9)
                    : AminaVisualLanguage.actionGreen,
                size: 18,
              ),
              const SizedBox(width: 7),
              Expanded(
                child: Text(
                  AppLocalizations.of(context)!.dashboardLatestKnownReading,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w700,
                    color: secondary,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: hasData
                      ? inRange || neutralStatus
                            ? Colors.white.withValues(alpha: .14)
                            : const Color(0xFFFFF1C7)
                      : const Color(0xFFF4F1E8),
                  borderRadius: BorderRadius.circular(999),
                  border: hasData && (inRange || neutralStatus)
                      ? Border.all(color: Colors.white.withValues(alpha: .16))
                      : null,
                ),
                child: Text(
                  status,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w800,
                    color: statusForeground,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 17),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Flexible(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: AlignmentDirectional.bottomStart,
                  child: Text(
                    display,
                    style: TextStyle(
                      fontFamily: 'Georgia',
                      fontSize: 56,
                      height: .9,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -1.8,
                      color: foreground,
                    ),
                  ),
                ),
              ),
              if (latest != null) ...[
                const SizedBox(width: 8),
                Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Text(
                    unit,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: secondary,
                    ),
                  ),
                ),
              ],
            ],
          ),
          if (timestamp != null && freshness != null) ...[
            const SizedBox(height: 13),
            Wrap(
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: 6,
              runSpacing: 4,
              children: [
                Icon(
                  timestampNeedsReview
                      ? Icons.warning_amber_rounded
                      : Icons.schedule_rounded,
                  size: 14,
                  color: secondary,
                ),
                Text(
                  timestamp,
                  key: const ValueKey('dashboard-latest-reading-timestamp'),
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: secondary,
                  ),
                ),
                Text(
                  '·',
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w800,
                    color: secondary,
                  ),
                ),
                Text(
                  freshness,
                  key: const ValueKey('dashboard-latest-reading-freshness'),
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: secondary,
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: FilledButton.icon(
              onPressed: () => context.go('/ajouter'),
              style: FilledButton.styleFrom(
                backgroundColor: hasData
                    ? Colors.white
                    : AminaVisualLanguage.forestDeep,
                foregroundColor: hasData
                    ? AminaVisualLanguage.forestDeep
                    : Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(
                    AminaVisualLanguage.controlRadius,
                  ),
                ),
                elevation: 0,
              ),
              icon: const Icon(Icons.add_rounded, size: 20),
              label: Text(
                _t(
                  context,
                  'Ajouter une mesure',
                  'Add a reading',
                  'إضافة قياس',
                ),
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AmbientBackground extends StatelessWidget {
  const _AmbientBackground();

  @override
  Widget build(BuildContext context) {
    if (AminaTheme.isDark(context)) return const SizedBox.shrink();
    return IgnorePointer(
      child: Stack(
        children: [
          PositionedDirectional(
            top: -120,
            end: -90,
            child: Container(
              width: 280,
              height: 280,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AminaVisualLanguage.mintWaveLight.withValues(alpha: .72),
              ),
            ),
          ),
          PositionedDirectional(
            bottom: -150,
            start: -80,
            child: Container(
              width: 330,
              height: 250,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(180),
                color: AminaVisualLanguage.mintWaveStrong.withValues(alpha: .45),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PremiumState extends StatelessWidget {
  final bool loading;
  final IconData? icon;
  final String title;
  final String body;

  const _PremiumState({
    this.loading = false,
    this.icon,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: Stack(
        children: [
          const Positioned.fill(child: _AmbientBackground()),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                children: [
                  const _PremiumBrandHeader(),
                  const Spacer(),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(26),
                    decoration: AminaVisualLanguage.cardDecoration(context),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (loading)
                          const CircularProgressIndicator()
                        else
                          Container(
                            width: 52,
                            height: 52,
                            decoration: AminaVisualLanguage.mintIconDecoration(
                              context,
                            ),
                            child: Icon(
                              icon ?? Icons.info_outline_rounded,
                              color: AminaVisualLanguage.actionGreen,
                            ),
                          ),
                        const SizedBox(height: 18),
                        Text(
                          title,
                          style: TextStyle(
                            fontFamily: 'Georgia',
                            fontSize: 24,
                            fontWeight: FontWeight.w700,
                            color: AminaVisualLanguage.primaryText(context),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          body,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            height: 1.45,
                            color: AminaVisualLanguage.secondary(context),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(flex: 2),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
