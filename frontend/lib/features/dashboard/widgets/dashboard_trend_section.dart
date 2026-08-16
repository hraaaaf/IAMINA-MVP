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

extension on _TrendRange {
  Duration get duration => switch (this) {
        _TrendRange.hours24 => const Duration(hours: 24),
        _TrendRange.days7 => const Duration(days: 7),
        _TrendRange.days14 => const Duration(days: 14),
        _TrendRange.days30 => const Duration(days: 30),
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

  String _formatValue(double mgDl) => widget.unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _RangeSelector(
                selected: _range,
                onChanged: (value) {
                  setState(() {
                    _range = value;
                    _selectedLogId = null;
                  });
                },
              ),
              const SizedBox(height: 14),
              if (snapshot.hasError)
                _TrendState(
                  icon: Icons.cloud_off_outlined,
                  text: l10n.dashboardTrendUnavailable,
                )
              else if (snapshot.connectionState == ConnectionState.waiting &&
                  logs.isEmpty)
                _TrendState(loading: true, text: l10n.dashboardTrendLoading)
              else if (logs.isEmpty)
                _TrendState(
                  icon: Icons.scatter_plot_outlined,
                  text: l10n.dashboardTrendEmpty,
                )
              else
                _TrendContent(
                  logs: logs,
                  start: start,
                  end: now,
                  low: hasTarget ? widget.low : null,
                  high: hasTarget ? widget.high : null,
                  unit: widget.unit,
                  selectedLogId: _selectedLogId,
                  onSelect: (id) => setState(() => _selectedLogId = id),
                ),
            ],
          ),
        );
      },
    );
  }
}

class _TrendContent extends StatelessWidget {
  final List<LogEntryData> logs;
  final DateTime start;
  final DateTime end;
  final double? low;
  final double? high;
  final String unit;
  final int? selectedLogId;
  final ValueChanged<int> onSelect;

  const _TrendContent({
    required this.logs,
    required this.start,
    required this.end,
    required this.low,
    required this.high,
    required this.unit,
    required this.selectedLogId,
    required this.onSelect,
  });

  DateTime _recordedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

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
        final locale = Localizations.localeOf(context).toLanguageTag();
        final selected = _selected;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 220,
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
                onSelect: onSelect,
              ),
            ),
            const SizedBox(height: 10),
            _TrendLegend(
              logCount: logs.length,
              medicationCount: medications.length,
              targetConfigured: low != null && high != null,
            ),
            const SizedBox(height: 10),
            Text(
              AppLocalizations.of(context)!.dashboardTrendNoInterpolation,
              style: TextStyle(
                fontSize: 10.8,
                height: 1.35,
                color: AminaVisualLanguage.secondary(context),
              ),
            ),
            const SizedBox(height: 12),
            _TrendSelectionCard(log: selected, unit: unit, locale: locale),
          ],
        );
      },
    );
  }
}

class _TrendShell extends StatelessWidget {
  final int? count;
  final Widget child;

  const _TrendShell({required this.count, required this.child});

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
                        fontSize: 21,
                        height: 1.05,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -.35,
                        color: AminaVisualLanguage.primaryText(context),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      l10n.dashboardTrendSubheading,
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
}

class _RangeSelector extends StatelessWidget {
  final _TrendRange selected;
  final ValueChanged<_TrendRange> onChanged;

  const _RangeSelector({required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Row(
      children: _TrendRange.values.map((value) {
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
                  height: 38,
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
      }).toList(growable: false),
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
    required this.onSelect,
  });

  DateTime _recordedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final plotWidth = (constraints.maxWidth -
                DashboardTrendPainter.leftInset -
                DashboardTrendPainter.rightInset)
            .clamp(1.0, double.infinity)
            .toDouble();
        return Semantics(
          label:
              AppLocalizations.of(context)!.dashboardTrendPointCount(logs.length),
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTapDown: (details) {
              final dx = details.localPosition.dx
                  .clamp(
                    DashboardTrendPainter.leftInset,
                    constraints.maxWidth - DashboardTrendPainter.rightInset,
                  )
                  .toDouble();
              final fraction = ((dx - DashboardTrendPainter.leftInset) / plotWidth)
                  .clamp(0.0, 1.0)
                  .toDouble();
              final targetMs = start.millisecondsSinceEpoch +
                  ((end.millisecondsSinceEpoch - start.millisecondsSinceEpoch) *
                          fraction)
                      .round();
              var nearest = logs.first;
              var distance =
                  (_recordedAt(nearest).millisecondsSinceEpoch - targetMs).abs();
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
  final int logCount;
  final int medicationCount;
  final bool targetConfigured;

  const _TrendLegend({
    required this.logCount,
    required this.medicationCount,
    required this.targetConfigured,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Wrap(
      spacing: 10,
      runSpacing: 6,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        _LegendDot(
          color: AminaVisualLanguage.forestDeep,
          label: l10n.dashboardTrendPointCount(logCount),
        ),
        if (targetConfigured)
          _LegendBand(label: l10n.dashboardTrendTargetBand)
        else
          _LegendIcon(
            icon: Icons.tune_rounded,
            label: l10n.dashboardTrendTargetMissing,
          ),
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
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(context),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                _value(),
                style: TextStyle(
                  fontFamily: 'Georgia',
                  fontSize: 26,
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
              const Spacer(),
              _SourcePill(label: l10n.dashboardTrendSourceLabel(log.source)),
            ],
          ),
          const SizedBox(height: 7),
          Text(
            DateFormat('d MMM · HH:mm', locale).format(at),
            style: TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
          const SizedBox(height: 9),
          if (tags.isEmpty)
            Text(
              l10n.dashboardTrendNoContext,
              style: TextStyle(
                fontSize: 11.5,
                height: 1.35,
                color: AminaVisualLanguage.secondary(context),
              ),
            )
          else
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: tags
                  .map((tag) => _ContextPill(label: tag))
                  .toList(growable: false),
            ),
        ],
      ),
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
      constraints: const BoxConstraints(maxWidth: 132),
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        textAlign: TextAlign.center,
        style: const TextStyle(
          color: AminaVisualLanguage.actionGreen,
          fontSize: 9.8,
          fontWeight: FontWeight.w800,
        ),
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
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

class _ContextPill extends StatelessWidget {
  final String label;
  const _ContextPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface.withValues(alpha: .68),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AminaVisualLanguage.mintBorder),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10.2,
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
          width: 7,
          height: 7,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 5),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 220),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 10.2,
              color: AminaVisualLanguage.secondary(context),
            ),
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
          width: 14,
          height: 7,
          decoration: BoxDecoration(
            color: AminaVisualLanguage.mintSurface,
            borderRadius: BorderRadius.circular(3),
            border: Border.all(color: AminaVisualLanguage.mintBorder),
          ),
        ),
        const SizedBox(width: 5),
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
