import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/localization/dashboard_kpi_localized_copy.dart';
import '../../../core/theme/amina_visual_language.dart';
import '../../../data/drift/dashboard_trend_queries.dart';
import '../../../data/drift/database.dart';

class DashboardAdaptiveKpiSection extends StatelessWidget {
  final String unit;
  final double? low;
  final double? high;

  const DashboardAdaptiveKpiSection({
    super.key,
    required this.unit,
    required this.low,
    required this.high,
  });

  DateTime _recordedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  String _displayValue(double mgDl) => unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

  bool _looksCgmLabelled(String source) {
    final normalized = source.trim().toLowerCase();
    return normalized.contains('cgm') ||
        normalized.contains('dexcom') ||
        normalized.contains('libre') ||
        normalized.contains('nightscout');
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final start = today.subtract(const Duration(days: 6));
    final targetConfigured = low != null && high != null && low! < high!;

    return StreamBuilder<List<LogEntryData>>(
      stream: db.watchDashboardTrendLogs(start, now),
      builder: (context, snapshot) {
        final l10n = AppLocalizations.of(context)!;
        if (snapshot.hasError) {
          return _KpiShell(
            child: _KpiState(
              icon: Icons.cloud_off_outlined,
              text: l10n.dashboardKpiUnavailable,
            ),
          );
        }

        final logs = List<LogEntryData>.from(
          snapshot.data ?? const <LogEntryData>[],
        )..sort((a, b) => _recordedAt(a).compareTo(_recordedAt(b)));

        if (snapshot.connectionState == ConnectionState.waiting && logs.isEmpty) {
          return const _KpiShell(
            child: _KpiState(loading: true, text: ''),
          );
        }

        if (logs.isEmpty) {
          return _KpiShell(
            child: _KpiState(
              icon: Icons.insights_outlined,
              text: l10n.dashboardKpiEmpty,
            ),
          );
        }

        final count = logs.length;
        final average = logs.fold<double>(
              0,
              (sum, log) => sum + log.bloodSugar,
            ) /
            count;
        final daysWithData = logs
            .map(_recordedAt)
            .map((date) => DateTime(date.year, date.month, date.day))
            .toSet()
            .length;
        final readingsInTarget = targetConfigured
            ? logs
                .where(
                  (log) =>
                      log.bloodSugar >= low! && log.bloodSugar <= high!,
                )
                .length
            : null;
        final hasCgmLabelledRows = logs.any(
          (log) => _looksCgmLabelled(log.source),
        );

        return _KpiShell(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      l10n.dashboardKpiRecordedMode,
                      style: TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                        color: AminaVisualLanguage.actionGreen,
                      ),
                    ),
                  ),
                  _PeriodPill(label: l10n.dashboardKpiPeriod7Days),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                l10n.dashboardKpiRecordedModeNote,
                style: TextStyle(
                  fontSize: 11.2,
                  height: 1.35,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
              const SizedBox(height: 14),
              LayoutBuilder(
                builder: (context, constraints) {
                  final compact = constraints.maxWidth < 310;
                  final cards = <Widget>[
                    _MetricTile(
                      icon: Icons.format_list_numbered_rounded,
                      label: l10n.dashboardKpiRecordedCount,
                      value: '$count',
                    ),
                    _MetricTile(
                      icon: Icons.calendar_today_outlined,
                      label: l10n.dashboardKpiDaysWithData,
                      value: '$daysWithData',
                    ),
                    _MetricTile(
                      icon: Icons.calculate_outlined,
                      label: l10n.dashboardKpiRecordedAverage,
                      value: '${_displayValue(average)} $unit',
                    ),
                    _MetricTile(
                      icon: targetConfigured
                          ? Icons.adjust_rounded
                          : Icons.tune_rounded,
                      label: targetConfigured
                          ? l10n.dashboardKpiReadingsInTarget
                          : l10n.dashboardKpiTargetMissing,
                      value: targetConfigured ? '$readingsInTarget/$count' : '—',
                    ),
                  ];

                  if (compact) {
                    return Column(
                      children: [
                        for (var i = 0; i < cards.length; i++) ...[
                          cards[i],
                          if (i != cards.length - 1)
                            const SizedBox(height: 8),
                        ],
                      ],
                    );
                  }

                  return Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: cards
                        .map(
                          (card) => SizedBox(
                            width: (constraints.maxWidth - 8) / 2,
                            child: card,
                          ),
                        )
                        .toList(growable: false),
                  );
                },
              ),
              if (targetConfigured) ...[
                const SizedBox(height: 8),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.info_outline_rounded,
                      size: 14,
                      color: AminaVisualLanguage.secondary(context),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        l10n.dashboardKpiNotTimeInRange,
                        style: TextStyle(
                          fontSize: 9.8,
                          height: 1.3,
                          color: AminaVisualLanguage.secondary(context),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
              const SizedBox(height: 12),
              _AdvancedMetricsLock(
                text: hasCgmLabelledRows
                    ? l10n.dashboardKpiCgmMarkedUnverified
                    : l10n.dashboardKpiAdvancedCgmLocked,
              ),
            ],
          ),
        );
      },
    );
  }
}

class _KpiShell extends StatelessWidget {
  final Widget child;
  const _KpiShell({required this.child});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: AminaVisualLanguage.cardDecoration(context, radius: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l10n.dashboardKpiHeading,
            style: TextStyle(
              fontFamily: 'Georgia',
              fontSize: 21,
              height: 1.05,
              fontWeight: FontWeight.w700,
              letterSpacing: -.35,
              color: AminaVisualLanguage.primaryText(context),
            ),
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _MetricTile({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(minHeight: 106),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(context),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: AminaVisualLanguage.actionGreen),
          const SizedBox(height: 8),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontFamily: 'Georgia',
              fontSize: 21,
              height: 1,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.primaryText(context),
            ),
          ),
          const SizedBox(height: 5),
          Text(
            label,
            style: TextStyle(
              fontSize: 10.8,
              height: 1.25,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _AdvancedMetricsLock extends StatelessWidget {
  final String text;
  const _AdvancedMetricsLock({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsetsDirectional.fromSTEB(12, 10, 12, 10),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface.withValues(alpha: .58),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AminaVisualLanguage.mintBorder.withValues(alpha: .78),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.lock_outline_rounded,
            size: 17,
            color: AminaVisualLanguage.actionGreen,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 10.8,
                height: 1.35,
                fontWeight: FontWeight.w600,
                color: AminaVisualLanguage.secondary(context),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PeriodPill extends StatelessWidget {
  final String label;
  const _PeriodPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AminaVisualLanguage.actionGreen,
          fontSize: 9.8,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _KpiState extends StatelessWidget {
  final bool loading;
  final IconData? icon;
  final String text;

  const _KpiState({this.loading = false, this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(minHeight: 120),
      alignment: Alignment.center,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (loading)
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2.2),
            )
          else
            Icon(
              icon ?? Icons.info_outline_rounded,
              size: 24,
              color: AminaVisualLanguage.actionGreen,
            ),
          if (loading || text.isNotEmpty) const SizedBox(height: 10),
          Text(
            loading ? l10n.dashboardKpiLoading : text,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 11.5,
              height: 1.35,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ],
      ),
    );
  }
}
