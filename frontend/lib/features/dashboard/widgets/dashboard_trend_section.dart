import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../../core/localization/dashboard_trend_localized_copy.dart';
import '../../../core/theme/amina_visual_language.dart';
import '../../../data/drift/dashboard_trend_queries.dart';
import '../../../data/drift/database.dart';
import 'dashboard_trend_painter.dart';

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

  int get dayCount => switch (this) {
    _TrendRange.hours24 => 1,
    _TrendRange.days7 => 7,
    _TrendRange.days14 => 14,
    _TrendRange.days30 => 30,
  };

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
                _TrendState(
                  icon: Icons.cloud_off_outlined,
                  text: l10n.dashboardTrendUnavailable,
                )
              else if (snapshot.connectionState == ConnectionState.waiting &&
                  logs.isEmpty)
                _TrendState(loading: true, text: l10n.dashboardTrendLoading)
              else if (logs.isEmpty)
                Column(
                  children: [
                    _RangeSelector(
                      selected: _range,
                      onChanged: _setRange,
                    ),
                    const SizedBox(height: 16),
                    _TrendState(
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

  String _displayValue(double mgDl) => unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

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
            _TrendSummary(
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
                    child: _TrendPlot(
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
                  _TrendLegend(
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
            _TrendSelectionCard(log: selected, unit: unit, locale: locale),
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

  const _TrendShell({required this.count, required this.range, required this.child});

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
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l10n.dashboardTrendHeading,
                      style: TextStyle(
                        fontFamily: 'Georgia',
                        fontSize: 23,
                        height: 1.02,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -.45,
                        color: AminaVisualLanguage.primaryText(context),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _subtitle(context, range),
                      style: TextStyle(
                        fontSize: 11.5,
                        height: 1.3,
                        color: AminaVisualLanguage.secondary(context),
                      ),
                    ),
                  ],
                ),
              ),
              if (count != null) ...[
                const SizedBox(width: 8),
                _CountPill(text: l10n.dashboardTrendPointCount(count!)),
              ],
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
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

class _TrendSummary extends StatelessWidget {
  final LogEntryData recent;
  final double average;
  final int? inTarget;
  final int count;
  final String unit;

  const _TrendSummary({
    required this.recent,
    required this.average,
    required this.inTarget,
    required this.count,
    required this.unit,
  });

  String _display(double mgDl) => unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

  @override
  Widget build(BuildContext context) {
    final cards = <Widget>[
      _SummaryMetric(
        icon: Icons.water_drop_outlined,
        value: _display(recent.bloodSugar),
        unit: unit,
        label: _pick(context, 'Récent', 'Recent', 'الأحدث'),
      ),
      _SummaryMetric(
        icon: Icons.show_chart_rounded,
        value: _display(average),
        unit: unit,
        label: _pick(context, 'Moyenne', 'Average', 'المتوسط'),
      ),
      _SummaryMetric(
        icon: Icons.adjust_rounded,
        value: inTarget == null ? '—' : '$inTarget / $count',
        label: _pick(context, 'Dans la cible', 'In range', 'ضمن النطاق'),
      ),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 650) {
          return Row(
            children: [
              for (var i = 0; i < cards.length; i++) ...[
                Expanded(child: cards[i]),
                if (i != cards.length - 1) const SizedBox(width: 10),
              ],
            ],
          );
        }
        return Column(
          children: [
            for (var i = 0; i < cards.length; i++) ...[
              cards[i],
              if (i != cards.length - 1) const SizedBox(height: 8),
            ],
          ],
        );
      },
    );
  }

  String _pick(BuildContext context, String fr, String en, String ar) {
    return switch (Localizations.localeOf(context).languageCode) {
      'fr' => fr,
      'ar' => ar,
      _ => en,
    };
  }
}

class _SummaryMetric extends StatelessWidget {
  final IconData icon;
  final String value;
  final String? unit;
  final String label;

  const _SummaryMetric({
    required this.icon,
    required this.value,
    this.unit,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 94),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface.withValues(alpha: .32),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AminaVisualLanguage.mintSurface,
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 23, color: AminaVisualLanguage.actionGreen),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Flexible(
                      child: Text(
                        value,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontFamily: 'Georgia',
                          fontSize: 26,
                          height: 1,
                          fontWeight: FontWeight.w700,
                          letterSpacing: -.5,
                          color: AminaVisualLanguage.primaryText(context),
                        ),
                      ),
                    ),
                    if (unit != null) ...[
                      const SizedBox(width: 6),
                      Padding(
                        padding: const EdgeInsets.only(bottom: 2),
                        child: Text(
                          unit!,
                          style: TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w700,
                            color: AminaVisualLanguage.secondary(context),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        label,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w700,
                          color: AminaVisualLanguage.secondary(context),
                        ),
                      ),
                    ),
                    const SizedBox(width: 5),
                    Icon(
                      Icons.info_outline_rounded,
                      size: 14,
                      color: AminaVisualLanguage.secondary(context),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RangeSelector extends StatelessWidget {
  final _TrendRange selected;
  final ValueChanged<_TrendRange> onChanged;

  const _RangeSelector({required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Row(
      children: _TrendRange.values
          .map((value) {
            final active = value == selected;
            return Expanded(
              child: Padding(
                padding: EdgeInsetsDirectional.only(
                  end: value == _TrendRange.values.last ? 0 : 6,
                ),
                child: Semantics(
                  selected: active,
                  button: true,
                  child: InkWell(
                    onTap: () => onChanged(value),
                    borderRadius: BorderRadius.circular(12),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 160),
                      height: 42,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: active
                            ? AminaVisualLanguage.mintSurface
                            : AminaVisualLanguage.controlSurface(context),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: active
                              ? AminaVisualLanguage.mintBorder
                              : AminaVisualLanguage.controlBorder(context),
                        ),
                      ),
                      child: Text(
                        value.label(l10n),
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w800,
                          color: active
                              ? AminaVisualLanguage.actionGreen
                              : AminaVisualLanguage.secondary(context),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            );
          })
          .toList(growable: false),
    );
  }
}

class _TrendPlot extends StatelessWidget {
  final List<LogEntryData> logs;
  final List<MedicationEventData> medications;
  final DateTime start;
  final DateTime end;
  final double? low;
  final double? high;
  final int selectedLogId;
  final String unit;
  final String locale;
  final bool dailySummary;
  final ValueChanged<int> onSelect;

  const _TrendPlot({
    required this.logs,
    required this.medications,
    required this.start,
    required this.end,
    required this.low,
    required this.high,
    required this.selectedLogId,
    required this.unit,
    required this.locale,
    required this.dailySummary,
    required this.onSelect,
  });

  DateTime _recordedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final plotWidth =
            (constraints.maxWidth -
                    DashboardTrendPainter.leftInset -
                    DashboardTrendPainter.rightInset)
                .clamp(1.0, double.infinity)
                .toDouble();
        return Semantics(
          label: AppLocalizations.of(
            context,
          )!.dashboardTrendPointCount(logs.length),
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTapDown: (details) {
              final dx = details.localPosition.dx
                  .clamp(
                    DashboardTrendPainter.leftInset,
                    constraints.maxWidth - DashboardTrendPainter.rightInset,
                  )
                  .toDouble();
              final fraction =
                  ((dx - DashboardTrendPainter.leftInset) / plotWidth)
                      .clamp(0.0, 1.0)
                      .toDouble();
              final targetMs =
                  start.millisecondsSinceEpoch +
                  ((end.millisecondsSinceEpoch - start.millisecondsSinceEpoch) *
                          fraction)
                      .round();
              var nearest = logs.first;
              var distance =
                  (_recordedAt(nearest).millisecondsSinceEpoch - targetMs)
                      .abs();
              for (final log in logs.skip(1)) {
                final candidate =
                    (_recordedAt(log).millisecondsSinceEpoch - targetMs).abs();
                if (candidate < distance) {
                  nearest = log;
                  distance = candidate;
                }
              }
              onSelect(nearest.id);
            },
            child: CustomPaint(
              painter: DashboardTrendPainter(
                logs: logs,
                medications: medications,
                start: start,
                end: end,
                low: low,
                high: high,
                selectedLogId: selectedLogId,
                unit: unit,
                locale: locale,
                isDark: Theme.of(context).brightness == Brightness.dark,
                dailySummary: dailySummary,
              ),
              child: const SizedBox.expand(),
            ),
          ),
        );
      },
    );
  }
}

class _TrendLegend extends StatelessWidget {
  final String unit;
  final double? low;
  final double? high;
  final bool dailySummary;
  final int medicationCount;

  const _TrendLegend({
    required this.unit,
    required this.low,
    required this.high,
    required this.dailySummary,
    required this.medicationCount,
  });

  String _display(double mgDl) => unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final targetConfigured = low != null && high != null && low! < high!;
    final code = Localizations.localeOf(context).languageCode;
    final medianLabel = code == 'fr'
        ? 'Médiane journalière'
        : code == 'ar'
        ? 'الوسيط اليومي'
        : 'Daily median';
    final minMaxLabel = code == 'fr'
        ? 'Min – Max (observé)'
        : code == 'ar'
        ? 'الأدنى – الأعلى (مسجل)'
        : 'Min – Max (observed)';

    return Wrap(
      spacing: 14,
      runSpacing: 7,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        _LegendDot(
          color: AminaVisualLanguage.forestDeep,
          label: dailySummary ? medianLabel : l10n.dashboardTrendPointCount(1),
        ),
        if (targetConfigured)
          _LegendBand(
            label: code == 'fr'
                ? 'Plage cible (${_display(low!)} – ${_display(high!)} $unit)'
                : '${l10n.dashboardTrendTargetBand} (${_display(low!)} – ${_display(high!)} $unit)',
          )
        else
          _LegendIcon(
            icon: Icons.tune_rounded,
            label: l10n.dashboardTrendTargetMissing,
          ),
        if (dailySummary)
          _LegendWhisker(label: minMaxLabel),
        if (medicationCount > 0)
          _LegendDot(
            color: const Color(0xFFC9852B),
            label: l10n.dashboardTrendMedicationEvents(medicationCount),
          ),
      ],
    );
  }
}

class _TrendSelectionCard extends StatelessWidget {
  final LogEntryData log;
  final String unit;
  final String locale;

  const _TrendSelectionCard({
    required this.log,
    required this.unit,
    required this.locale,
  });

  String _value() => unit == 'mmol/L'
      ? (log.bloodSugar / 18.0).toStringAsFixed(1)
      : log.bloodSugar.toStringAsFixed(0);

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final at = log.loggedAt ?? log.createdAt;
    final tags = <String>{};

    void addTag(String? key) {
      if (key == null || key.trim().isEmpty) return;
      final label = l10n.dashboardTrendContextLabel(key.trim());
      if (label != null) tags.add(label);
    }

    addTag(log.glycemicContext);
    addTag(log.mealType);
    if (log.isStressed) addTag('stress');
    if (log.isActive) addTag('activity');
    if (log.isSick) addTag('illness');
    if (log.isTired || (log.fatigueLevel ?? 0) > 0) addTag('fatigue');

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(context),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 660;
          final value = _SelectionValue(value: _value(), unit: unit);
          final date = _SelectionDate(at: at, locale: locale);
          final contextTags = tags.isEmpty
              ? Text(
                  l10n.dashboardTrendNoContext,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: AminaVisualLanguage.secondary(context),
                  ),
                )
              : Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: tags
                      .map((tag) => _ContextPill(label: tag))
                      .toList(growable: false),
                );
          final source = _SourcePill(
            label: l10n.dashboardTrendSourceLabel(log.source),
          );

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [Expanded(child: value), source]),
                const SizedBox(height: 10),
                date,
                const SizedBox(height: 10),
                contextTags,
              ],
            );
          }

          return Row(
            children: [
              SizedBox(width: 150, child: value),
              _VerticalDivider(),
              Expanded(flex: 2, child: date),
              _VerticalDivider(),
              Expanded(flex: 3, child: contextTags),
              _VerticalDivider(),
              source,
            ],
          );
        },
      ),
    );
  }
}

class _SelectionValue extends StatelessWidget {
  final String value;
  final String unit;
  const _SelectionValue({required this.value, required this.unit});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          value,
          style: TextStyle(
            fontFamily: 'Georgia',
            fontSize: 29,
            height: 1,
            fontWeight: FontWeight.w700,
            color: AminaVisualLanguage.primaryText(context),
          ),
        ),
        const SizedBox(width: 6),
        Padding(
          padding: const EdgeInsets.only(bottom: 2),
          child: Text(
            unit,
            style: TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ),
      ],
    );
  }
}

class _SelectionDate extends StatelessWidget {
  final DateTime at;
  final String locale;
  const _SelectionDate({required this.at, required this.locale});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          Icons.calendar_month_outlined,
          size: 18,
          color: AminaVisualLanguage.secondary(context),
        ),
        const SizedBox(width: 8),
        Flexible(
          child: Text(
            DateFormat('d MMM · HH:mm', locale).format(at),
            style: TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ),
      ],
    );
  }
}

class _VerticalDivider extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 1,
      height: 36,
      margin: const EdgeInsets.symmetric(horizontal: 14),
      color: AminaVisualLanguage.controlBorder(context),
    );
  }
}

class _TrendState extends StatelessWidget {
  final bool loading;
  final IconData? icon;
  final String text;

  const _TrendState({this.loading = false, this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(minHeight: 150),
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
              color: AminaVisualLanguage.actionGreen,
              size: 26,
            ),
          const SizedBox(height: 10),
          Text(
            text,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 12,
              height: 1.4,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _CountPill extends StatelessWidget {
  final String text;
  const _CountPill({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(maxWidth: 152),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.bar_chart_rounded,
            size: 13,
            color: AminaVisualLanguage.actionGreen,
          ),
          const SizedBox(width: 5),
          Flexible(
            child: Text(
              text,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AminaVisualLanguage.actionGreen,
                fontSize: 9.8,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SourcePill extends StatelessWidget {
  final String label;
  const _SourcePill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AminaVisualLanguage.actionGreen,
          fontSize: 10.2,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _ContextPill extends StatelessWidget {
  final String label;
  const _ContextPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface.withValues(alpha: .68),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AminaVisualLanguage.mintBorder),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10.4,
          fontWeight: FontWeight.w700,
          color: AminaVisualLanguage.secondary(context),
        ),
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 10.2,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
      ],
    );
  }
}

class _LegendBand extends StatelessWidget {
  final String label;
  const _LegendBand({required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 19,
          height: 9,
          decoration: BoxDecoration(
            color: AminaVisualLanguage.mintSurface,
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: AminaVisualLanguage.mintBorder),
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 10.2,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
      ],
    );
  }
}

class _LegendWhisker extends StatelessWidget {
  final String label;
  const _LegendWhisker({required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 2,
          height: 15,
          decoration: BoxDecoration(
            color: AminaVisualLanguage.forestDeep.withValues(alpha: .65),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 10.2,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
      ],
    );
  }
}

class _LegendIcon extends StatelessWidget {
  final IconData icon;
  final String label;
  const _LegendIcon({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 13, color: AminaVisualLanguage.actionGreen),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 10.2,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
      ],
    );
  }
}
