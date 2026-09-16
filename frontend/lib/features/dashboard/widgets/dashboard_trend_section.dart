import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/amina_visual_language.dart';
import '../../../data/drift/dashboard_trend_queries.dart';
import '../../../data/drift/database.dart';
import 'dashboard_trend_view.dart';

enum _TrendRange { hours24, days7, days14, days30 }

String _dashboardTrendDateLocale(BuildContext context) {
  final locale = Localizations.localeOf(context);
  return switch (locale.languageCode) {
    'fr' => 'fr-FR',
    'ar' => 'ar-MA',
    'en' => 'en-US',
    _ => locale.toLanguageTag(),
  };
}

extension on _TrendRange {
  Duration get duration => switch (this) {
    _TrendRange.hours24 => const Duration(hours: 24),
    _TrendRange.days7 => const Duration(days: 7),
    _TrendRange.days14 => const Duration(days: 14),
    _TrendRange.days30 => const Duration(days: 30),
  };

  bool get useDailySummary => this != _TrendRange.hours24;

  String label(AppLocalizations l10n) => switch (this) {
    _TrendRange.hours24 => l10n.dashboardTrendRangeHours(24),
    _TrendRange.days7 => l10n.dashboardTrendRangeDays(7),
    _TrendRange.days14 => l10n.dashboardTrendRangeDays(14),
    _TrendRange.days30 => l10n.dashboardTrendRangeDays(30),
  };
}

class DashboardTrendSection extends StatefulWidget {
  final String unit;
  final double? low;
  final double? high;

  const DashboardTrendSection({
    super.key,
    required this.unit,
    required this.low,
    required this.high,
  });

  @override
  State<DashboardTrendSection> createState() => _DashboardTrendSectionState();
}

class _DashboardTrendSectionState extends State<DashboardTrendSection> {
  _TrendRange _range = _TrendRange.days7;
  int? _selectedLogId;

  DateTime _recordedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final now = DateTime.now();
    final start = now.subtract(_range.duration);
    final hasTarget =
        widget.low != null && widget.high != null && widget.low! < widget.high!;

    return StreamBuilder<List<LogEntryData>>(
      stream: db.watchDashboardTrendLogs(start, now),
      builder: (context, snapshot) {
        final l10n = AppLocalizations.of(context)!;
        final logs = List<LogEntryData>.from(
          snapshot.data ?? const <LogEntryData>[],
        )..sort((a, b) => _recordedAt(a).compareTo(_recordedAt(b)));

        return _TrendShell(
          count: logs.isEmpty ? null : logs.length,
          range: _range,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (snapshot.hasError)
                DashboardTrendState(
                  icon: Icons.cloud_off_outlined,
                  text: l10n.dashboardTrendUnavailable,
                )
              else if (snapshot.connectionState == ConnectionState.waiting &&
                  logs.isEmpty)
                DashboardTrendState(
                  loading: true,
                  text: l10n.dashboardTrendLoading,
                )
              else if (logs.isEmpty)
                Column(
                  children: [
                    _RangeSelector(
                      selected: _range,
                      onChanged: _setRange,
                    ),
                    const SizedBox(height: 16),
                    DashboardTrendState(
                      icon: Icons.insights_outlined,
                      text: l10n.dashboardTrendEmpty,
                    ),
                  ],
                )
              else
                _TrendContent(
                  logs: logs,
                  range: _range,
                  start: start,
                  end: now,
                  low: hasTarget ? widget.low : null,
                  high: hasTarget ? widget.high : null,
                  unit: widget.unit,
                  selectedLogId: _selectedLogId,
                  onSelect: (id) => setState(() => _selectedLogId = id),
                  onRangeChanged: _setRange,
                ),
            ],
          ),
        );
      },
    );
  }

  void _setRange(_TrendRange value) {
    setState(() {
      _range = value;
      _selectedLogId = null;
    });
  }
}

class _TrendContent extends StatelessWidget {
  final List<LogEntryData> logs;
  final _TrendRange range;
  final DateTime start;
  final DateTime end;
  final double? low;
  final double? high;
  final String unit;
  final int? selectedLogId;
  final ValueChanged<int> onSelect;
  final ValueChanged<_TrendRange> onRangeChanged;

  const _TrendContent({
    required this.logs,
    required this.range,
    required this.start,
    required this.end,
    required this.low,
    required this.high,
    required this.unit,
    required this.selectedLogId,
    required this.onSelect,
    required this.onRangeChanged,
  });

  LogEntryData get _selected => selectedLogId == null
      ? logs.last
      : logs.firstWhere(
          (log) => log.id == selectedLogId,
          orElse: () => logs.last,
        );

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    return StreamBuilder<List<MedicationEventData>>(
      stream: db.watchDashboardMedicationEvents(start, end),
      builder: (context, snapshot) {
        final medications = snapshot.hasError
            ? const <MedicationEventData>[]
            : List<MedicationEventData>.from(
                snapshot.data ?? const <MedicationEventData>[],
              );
        final locale = _dashboardTrendDateLocale(context);
        final selected = _selected;
        final average = logs.fold<double>(
              0,
              (sum, log) => sum + log.bloodSugar,
            ) /
            logs.length;
        final targetConfigured = low != null && high != null && low! < high!;
        final inTarget = targetConfigured
            ? logs
                .where(
                  (log) => log.bloodSugar >= low! && log.bloodSugar <= high!,
                )
                .length
            : null;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DashboardTrendSummary(
              recent: logs.last,
              average: average,
              inTarget: inTarget,
              count: logs.length,
              unit: unit,
            ),
            const SizedBox(height: 14),
            _RangeSelector(selected: range, onChanged: onRangeChanged),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsetsDirectional.fromSTEB(10, 12, 10, 10),
              decoration: BoxDecoration(
                color: AminaVisualLanguage.controlSurface(context),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: AminaVisualLanguage.controlBorder(context),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsetsDirectional.only(start: 4),
                    child: Text(
                      unit,
                      style: TextStyle(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                        color: AminaVisualLanguage.secondary(context),
                      ),
                    ),
                  ),
                  const SizedBox(height: 2),
                  SizedBox(
                    height: 250,
                    child: DashboardTrendPlot(
                      logs: logs,
                      medications: medications,
                      start: start,
                      end: end,
                      low: low,
                      high: high,
                      selectedLogId: selected.id,
                      unit: unit,
                      locale: locale,
                      dailySummary: range.useDailySummary,
                      onSelect: onSelect,
                    ),
                  ),
                  const SizedBox(height: 8),
                  DashboardTrendLegend(
                    unit: unit,
                    low: low,
                    high: high,
                    dailySummary: range.useDailySummary,
                    medicationCount: medications.length,
                  ),
                  const SizedBox(height: 10),
                  Text(
                    range.useDailySummary
                        ? _dailySummaryNote(context)
                        : AppLocalizations.of(
                            context,
                          )!.dashboardTrendNoInterpolation,
                    style: TextStyle(
                      fontSize: 10.6,
                      height: 1.35,
                      color: AminaVisualLanguage.secondary(context),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            DashboardTrendSelectionCard(
              log: selected,
              unit: unit,
              locale: locale,
            ),
          ],
        );
      },
    );
  }

  String _dailySummaryNote(BuildContext context) {
    final code = Localizations.localeOf(context).languageCode;
    if (code == 'ar') {
      return 'كل نقطة تمثل الوسيط اليومي للقياسات. الأشرطة العمودية تمثل القيم الدنيا والعليا المسجلة.';
    }
    if (code == 'en') {
      return 'Each point is the daily median of recorded measurements. Vertical bars show the observed minimum and maximum.';
    }
    return 'Chaque point représente la médiane des mesures du jour. Les barres verticales indiquent la valeur minimale et maximale observée.';
  }
}

class _TrendShell extends StatelessWidget {
  final int? count;
  final _TrendRange range;
  final Widget child;

  const _TrendShell({
    required this.count,
    required this.range,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return DashboardTrendShell(
      count: count,
      subtitle: _subtitle(context, range),
      child: child,
    );
  }

  String _subtitle(BuildContext context, _TrendRange range) {
    final code = Localizations.localeOf(context).languageCode;
    final period = switch (range) {
      _TrendRange.hours24 => code == 'fr' ? '24 dernières heures' : '24 hours',
      _TrendRange.days7 => code == 'fr' ? '7 derniers jours' : 'last 7 days',
      _TrendRange.days14 => code == 'fr' ? '14 derniers jours' : 'last 14 days',
      _TrendRange.days30 => code == 'fr' ? '30 derniers jours' : 'last 30 days',
    };
    if (code == 'ar') return 'تطور سكر الدم · الفترة المحددة';
    if (code == 'fr') return 'Évolution de votre glycémie · Données des $period';
    return 'Your glucose trend · Data from the $period';
  }
}

class _RangeSelector extends StatelessWidget {
  final _TrendRange selected;
  final ValueChanged<_TrendRange> onChanged;

  const _RangeSelector({required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final values = _TrendRange.values;
    return DashboardTrendRangeSelector(
      labels: values.map((value) => value.label(l10n)).toList(growable: false),
      selectedIndex: values.indexOf(selected),
      onChanged: (index) => onChanged(values[index]),
    );
  }
}
