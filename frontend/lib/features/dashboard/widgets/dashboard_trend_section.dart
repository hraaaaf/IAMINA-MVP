import 'dart:math' as math;

import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../../core/localization/dashboard_trend_localized_copy.dart';
import '../../../core/theme/amina_visual_language.dart';
import '../../../data/drift/dashboard_trend_queries.dart';
import '../../../data/drift/database.dart';

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

  DateTime _loggedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  double _displayValue(double mgDl) =>
      widget.unit == 'mmol/L' ? mgDl / 18.0 : mgDl;

  String _formatValue(double mgDl) => widget.unit == 'mmol/L'
      ? _displayValue(mgDl).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final now = DateTime.now();
    final start = now.subtract(_range.duration);
    final targetConfigured =
        widget.low != null && widget.high != null && widget.low! < widget.high!;

    return StreamBuilder<List<LogEntryData>>(
      stream: db.watchDashboardTrendLogs(start, now),
      builder: (context, logSnapshot) {
        final l10n = AppLocalizations.of(context)!;
        final logs = [...?logSnapshot.data]
          ..sort((a, b) => _loggedAt(a).compareTo(_loggedAt(b)));

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
                  if (logs.isNotEmpty)
                    _CountPill(text: l10n.dashboardTrendPointCount(logs.length)),
                ],
              ),
              const SizedBox(height: 14),
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
              if (logSnapshot.hasError)
                _TrendState(
                  icon: Icons.cloud_off_outlined,
                  text: l10n.dashboardTrendUnavailable,
                )
              else if (logSnapshot.connectionState == ConnectionState.waiting &&
                  logs.isEmpty)
                _TrendState(loading: true, text: l10n.dashboardTrendLoading)
              else if (logs.isEmpty)
                _TrendState(
                  icon: Icons.scatter_plot_outlined,
                  text: l10n.dashboardTrendEmpty,
                )
              else
                StreamBuilder<List<MedicationEventData>>(
                  stream: db.watchDashboardMedicationEvents(start, now),
                  builder: (context, medicationSnapshot) {
                    final medications = medicationSnapshot.hasError
                        ? const <MedicationEventData>[]
                        : [...?medicationSnapshot.data];
                    final selected = _selectedLog(logs);
                    final locale = Localizations.localeOf(context).toLanguageTag();

                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          height: 220,
                          child: _TrendPlot(
                            logs: logs,
                            medications: medications,
                            start: start,
                            end: now,
                            low: targetConfigured ? widget.low : null,
                            high: targetConfigured ? widget.high : null,
                            selectedLogId: selected.id,
                            unit: widget.unit,
                            locale: locale,
                            onSelect: (id) => setState(() => _selectedLogId = id),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 10,
                          runSpacing: 6,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            _LegendDot(
                              color: AminaVisualLanguage.forestDeep,
                              label: l10n.dashboardTrendPointCount(logs.length),
                            ),
                            if (targetConfigured)
                              _LegendBand(label: l10n.dashboardTrendTargetBand)
                            else
                              _LegendIcon(
                                icon: Icons.tune_rounded,
                                label: l10n.dashboardTrendTargetMissing,
                              ),
                            if (medications.isNotEmpty)
                              _LegendDot(
                                color: const Color(0xFFC9852B),
                                label: l10n.dashboardTrendMedicationEvents(
                                  medications.length,
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Text(
                          l10n.dashboardTrendNoInterpolation,
                          style: TextStyle(
                            fontSize: 10.8,
                            height: 1.35,
                            color: AminaVisualLanguage.secondary(context),
                          ),
                        ),
                        const SizedBox(height: 12),
                        _TrendSelectionCard(
                          log: selected,
                          unit: widget.unit,
                          value: _formatValue(selected.bloodSugar),
                          locale: locale,
                        ),
                      ],
                    );
                  },
                ),
            ],
          ),
        );
      },
    );
  }

  LogEntryData _selectedLog(List<LogEntryData> logs) {
    final selectedId = _selectedLogId;
    if (selectedId == null) return logs.last;
    return logs.firstWhere(
      (log) => log.id == selectedId,
      orElse: () => logs.last,
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
  static const double _left = 42;
  static const double _right = 8;
  static const double _top = 10;
  static const double _bottom = 28;

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

  DateTime _loggedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final plotWidth = math.max(1.0, width - _left - _right);
        return Semantics(
          label: AppLocalizations.of(context)!.dashboardTrendPointCount(logs.length),
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTapDown: (details) {
              final dx = details.localPosition.dx.clamp(_left, width - _right);
              final fraction = ((dx - _left) / plotWidth).clamp(0.0, 1.0);
              final targetMs = start.millisecondsSinceEpoch +
                  ((end.millisecondsSinceEpoch - start.millisecondsSinceEpoch) *
                          fraction)
                      .round();
              var nearest = logs.first;
              var nearestDistance =
                  (_loggedAt(nearest).millisecondsSinceEpoch - targetMs).abs();
              for (final log in logs.skip(1)) {
                final distance =
                    (_loggedAt(log).millisecondsSinceEpoch - targetMs).abs();
                if (distance < nearestDistance) {
                  nearest = log;
                  nearestDistance = distance;
                }
              }
              onSelect(nearest.id);
            },
            child: CustomPaint(
              painter: _TrendPainter(
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

class _TrendPainter extends CustomPainter {
  final List<LogEntryData> logs;
  final List<MedicationEventData> medications;
  final DateTime start;
  final DateTime end;
  final double? low;
  final double? high;
  final int selectedLogId;
  final String unit;
  final String locale;
  final bool isDark;

  const _TrendPainter({
    required this.logs,
    required this.medications,
    required this.start,
    required this.end,
    required this.low,
    required this.high,
    required this.selectedLogId,
    required this.unit,
    required this.locale,
    required this.isDark,
  });

  DateTime _loggedAt(LogEntryData log) => log.loggedAt ?? log.createdAt;

  String _valueLabel(double mgDl) => unit == 'mmol/L'
      ? (mgDl / 18.0).toStringAsFixed(1)
      : mgDl.toStringAsFixed(0);

  @override
  void paint(Canvas canvas, Size size) {
    const left = 42.0;
    const right = 8.0;
    const top = 10.0;
    const bottom = 28.0;
    final rect = Rect.fromLTRB(left, top, size.width - right, size.height - bottom);
    if (rect.width <= 0 || rect.height <= 0 || logs.isEmpty) return;

    final values = <double>[
      ...logs.map((log) => log.bloodSugar),
      if (low != null) low!,
      if (high != null) high!,
    ];
    var minY = values.reduce(math.min);
    var maxY = values.reduce(math.max);
    final rawSpan = maxY - minY;
    final padding = math.max(15.0, rawSpan * .12);
    minY = math.max(0.0, minY - padding);
    maxY += padding;
    if (maxY - minY < 20) {
      final center = (maxY + minY) / 2;
      minY = math.max(0.0, center - 10);
      maxY = center + 10;
    }

    double yFor(double value) =>
        rect.bottom - ((value - minY) / (maxY - minY)) * rect.height;
    double xFor(DateTime time) {
      final total = end.millisecondsSinceEpoch - start.millisecondsSinceEpoch;
      if (total <= 0) return rect.left;
      final elapsed = time.millisecondsSinceEpoch - start.millisecondsSinceEpoch;
      return rect.left + (elapsed / total).clamp(0.0, 1.0) * rect.width;
    }

    final gridPaint = Paint()
      ..color = (isDark ? Colors.white : const Color(0xFF123E35))
          .withValues(alpha: .09)
      ..strokeWidth = 1;
    final axisText = TextStyle(
      fontSize: 9.5,
      color: (isDark ? Colors.white : const Color(0xFF42655D))
          .withValues(alpha: .78),
    );

    if (low != null && high != null && low! < high!) {
      final targetTop = yFor(high!).clamp(rect.top, rect.bottom);
      final targetBottom = yFor(low!).clamp(rect.top, rect.bottom);
      canvas.drawRect(
        Rect.fromLTRB(rect.left, targetTop, rect.right, targetBottom),
        Paint()..color = AminaVisualLanguage.mintSurface.withValues(alpha: .72),
      );
    }

    for (final fraction in const [0.0, .5, 1.0]) {
      final y = rect.top + rect.height * fraction;
      canvas.drawLine(Offset(rect.left, y), Offset(rect.right, y), gridPaint);
      final value = maxY - (maxY - minY) * fraction;
      final painter = TextPainter(
        text: TextSpan(text: _valueLabel(value), style: axisText),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: left - 6);
      painter.paint(canvas, Offset(left - painter.width - 6, y - painter.height / 2));
    }

    final range = end.difference(start);
    final xTimes = [
      start,
      start.add(Duration(milliseconds: range.inMilliseconds ~/ 2)),
      end,
    ];
    for (var i = 0; i < xTimes.length; i++) {
      final time = xTimes[i];
      final label = range.inHours <= 24
          ? DateFormat('HH:mm', locale).format(time)
          : DateFormat('d MMM', locale).format(time);
      final painter = TextPainter(
        text: TextSpan(text: label, style: axisText),
        textDirection: TextDirection.ltr,
      )..layout();
      final x = rect.left + rect.width * (i / 2);
      final dx = i == 0
          ? x
          : i == 2
              ? x - painter.width
              : x - painter.width / 2;
      painter.paint(canvas, Offset(dx, rect.bottom + 7));
    }

    final medicationPaint = Paint()..color = const Color(0xFFC9852B);
    for (final event in medications) {
      final x = xFor(event.takenAt);
      canvas.drawLine(
        Offset(x, rect.top),
        Offset(x, rect.top + 10),
        medicationPaint..strokeWidth = 1.5,
      );
      canvas.drawCircle(Offset(x, rect.top + 2), 2.5, medicationPaint);
    }

    final pointPaint = Paint()..color = AminaVisualLanguage.forestDeep;
    final selectedPaint = Paint()..color = AminaVisualLanguage.actionGreen;
    for (final log in logs) {
      final point = Offset(xFor(_loggedAt(log)), yFor(log.bloodSugar));
      final selected = log.id == selectedLogId;
      if (selected) {
        canvas.drawCircle(
          point,
          7,
          Paint()..color = AminaVisualLanguage.mintSurface,
        );
      }
      canvas.drawCircle(point, selected ? 4.8 : 3.6, selected ? selectedPaint : pointPaint);
    }
  }

  @override
  bool shouldRepaint(covariant _TrendPainter oldDelegate) {
    return oldDelegate.logs != logs ||
        oldDelegate.medications != medications ||
        oldDelegate.start != start ||
        oldDelegate.end != end ||
        oldDelegate.low != low ||
        oldDelegate.high != high ||
        oldDelegate.selectedLogId != selectedLogId ||
        oldDelegate.unit != unit ||
        oldDelegate.locale != locale ||
        oldDelegate.isDark != isDark;
  }
}

class _TrendSelectionCard extends StatelessWidget {
  final LogEntryData log;
  final String unit;
  final String value;
  final String locale;

  const _TrendSelectionCard({
    required this.log,
    required this.unit,
    required this.value,
    required this.locale,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final at = log.loggedAt ?? log.createdAt;
    final tags = <String>[
      if (log.glycemicContext != null)
        ?l10n.dashboardTrendContextLabel(log.glycemicContext!),
      if (log.mealType != null) ?l10n.dashboardTrendContextLabel(log.mealType!),
      if (log.isStressed) ?l10n.dashboardTrendContextLabel('stress'),
      if (log.isActive) ?l10n.dashboardTrendContextLabel('activity'),
      if (log.isSick) ?l10n.dashboardTrendContextLabel('illness'),
      if (log.isTired || (log.fatigueLevel ?? 0) > 0)
        ?l10n.dashboardTrendContextLabel('fatigue'),
    ].whereType<String>().toSet().toList(growable: false);

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
                value,
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
              children: tags.map((tag) => _ContextPill(label: tag)).toList(),
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
        Flexible(
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
