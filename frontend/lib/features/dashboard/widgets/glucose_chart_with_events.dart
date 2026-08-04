import 'dart:math' as math;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/clinical_card.dart';
import '../../../data/drift/database.dart';
import 'agp_chart.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Public widget
// ─────────────────────────────────────────────────────────────────────────────

class GlucoseChartWithEvents extends StatefulWidget {
  final List<LogEntryData> logs;
  final double low;
  final double high;
  final String unit;

  const GlucoseChartWithEvents({
    super.key,
    required this.logs,
    required this.low,
    required this.high,
    required this.unit,
  });

  @override
  State<GlucoseChartWithEvents> createState() => _GlucoseChartWithEventsState();
}

class _GlucoseChartWithEventsState extends State<GlucoseChartWithEvents> {
  int    _hoursFilter = 0;
  String? _mealFilter;
  int    _touchedIndex = -1;

  List<LogEntryData> get _filteredLogs {
    var logs = widget.logs;
    if (_hoursFilter != 0) {
      final cutoff = DateTime.now().subtract(Duration(hours: _hoursFilter));
      logs = logs.where((l) => (l.loggedAt ?? l.createdAt).isAfter(cutoff)).toList();
    }
    if (_mealFilter != null) {
      logs = logs.where((l) => l.mealType == _mealFilter).toList();
    }
    return logs;
  }

  @override
  Widget build(BuildContext context) {
    final logs = _filteredLogs;

    if (widget.logs.isEmpty) {
      return ClinicalCard(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            CardHead(title: 'Profil glycémique ambulatoire', meta: widget.unit),
            const SizedBox(height: 40),
            const Icon(Icons.show_chart, color: AminaTheme.ink300, size: 40),
            const SizedBox(height: 8),
            const Text('Aucune donnée', style: TextStyle(color: AminaTheme.ink400, fontSize: 13)),
            const SizedBox(height: 40),
          ],
        ),
      );
    }

    return ClinicalCard(
      padding: const EdgeInsets.all(0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: Row(
              children: [
                Expanded(child: CardHead(title: 'Profil glycémique ambulatoire', meta: widget.unit)),
                // Live badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AminaTheme.goodBg,
                    borderRadius: BorderRadius.circular(100),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 6, height: 6,
                        decoration: const BoxDecoration(color: AminaTheme.teal500, shape: BoxShape.circle),
                      ),
                      const SizedBox(width: 4),
                      const Text('en direct', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AminaTheme.goodFg)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Temporal filter chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                _TimeChip(label: 'Tout', value: 0,  selected: _hoursFilter == 0,  onTap: () => setState(() => _hoursFilter = 0)),
                const SizedBox(width: 6),
                _TimeChip(label: '24h',  value: 24, selected: _hoursFilter == 24, onTap: () => setState(() => _hoursFilter = 24)),
                const SizedBox(width: 6),
                _TimeChip(label: '12h',  value: 12, selected: _hoursFilter == 12, onTap: () => setState(() => _hoursFilter = 12)),
                const SizedBox(width: 6),
                _TimeChip(label: '6h',   value: 6,  selected: _hoursFilter == 6,  onTap: () => setState(() => _hoursFilter = 6)),
                const SizedBox(width: 6),
                _TimeChip(label: '3h',   value: 3,  selected: _hoursFilter == 3,  onTap: () => setState(() => _hoursFilter = 3)),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // Medical nomenclature filter chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                _MealChip(label: 'Tous',             value: null,             selected: _mealFilter == null,             onTap: () => setState(() => _mealFilter = null)),
                const SizedBox(width: 6),
                _MealChip(label: 'À jeun',           value: 'À jeun',         selected: _mealFilter == 'À jeun',         onTap: () => setState(() => _mealFilter = 'À jeun')),
                const SizedBox(width: 6),
                _MealChip(label: 'Post-prandial',    value: 'Post-prandial',  selected: _mealFilter == 'Post-prandial',  onTap: () => setState(() => _mealFilter = 'Post-prandial')),
                const SizedBox(width: 6),
                _MealChip(label: 'Avant le coucher', value: 'Avant le coucher', selected: _mealFilter == 'Avant le coucher', onTap: () => setState(() => _mealFilter = 'Avant le coucher')),
                const SizedBox(width: 6),
                _MealChip(label: 'En-cas',           value: 'En-cas',         selected: _mealFilter == 'En-cas',         onTap: () => setState(() => _mealFilter = 'En-cas')),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // AGP Chart
          if (logs.length >= 2)
            SizedBox(
              height: 220,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(4, 0, 16, 0),
                child: _AgpChart(
                  logs: logs,
                  low: widget.low,
                  high: widget.high,
                  touchedIndex: _touchedIndex,
                  onTouch: (i) => setState(() => _touchedIndex = i),
                ),
              ),
            )
          else
            const SizedBox(
              height: 220,
              child: Center(child: Text('Données insuffisantes pour le profil AGP', style: TextStyle(fontSize: 12, color: AminaTheme.ink400))),
            ),

          // Event overlays legend
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: _EventLegend(logs: logs),
          ),

          // AGP legend
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: Wrap(
              spacing: 16, runSpacing: 6,
              children: [
                _LegendItem(color: Color(0xFF1A3A2E), label: 'Médiane'),
                _LegendItem(color: Color(0xFF3CC3A0), label: '25–75%', opacity: 0.5),
                _LegendItem(color: Color(0xFF3CC3A0), label: '5–95%',  opacity: 0.2),
                _LegendItem(color: Color(0xFFE4A85B), label: 'Cible 70–180', dashed: true),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// AGP Chart — CustomPainter (proper percentile bands + colored zones)
// ─────────────────────────────────────────────────────────────────────────────

class _AgpChart extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low, high;
  final int touchedIndex;
  final ValueChanged<int> onTouch;

  const _AgpChart({
    required this.logs,
    required this.low,
    required this.high,
    required this.touchedIndex,
    required this.onTouch,
  });

  Map<int, List<double>> _groupByHour() {
    final map = <int, List<double>>{};
    for (final log in logs) {
      final h = (log.loggedAt ?? log.createdAt).hour;
      map.putIfAbsent(h, () => []).add(log.bloodSugar);
    }
    return map;
  }

  static double _percentile(List<double> sorted, double p) {
    if (sorted.isEmpty) return 0;
    final idx = (p / 100 * (sorted.length - 1)).clamp(0.0, (sorted.length - 1).toDouble());
    final lower = sorted[idx.floor()];
    final upper = sorted[idx.ceil()];
    return lower + (upper - lower) * (idx - idx.floor());
  }

  @override
  Widget build(BuildContext context) {
    final byHour = _groupByHour();
    final isDark = context.watch<TweaksNotifier>().isDark;

    // Build per-hour percentiles using the shared AgpPoint data class
    final List<AgpPoint> points = [];
    for (var h = 0; h < 24; h++) {
      final values = List<double>.from(byHour[h] ?? [])..sort();
      if (values.isEmpty) continue;
      points.add(AgpPoint(
        hour: h.toDouble(),
        p5:   _percentile(values, 5),
        p25:  _percentile(values, 25),
        p50:  _percentile(values, 50),
        p75:  _percentile(values, 75),
        p95:  _percentile(values, 95),
      ));
    }

    if (points.length < 3) {
      return _SimpleLineChart(logs: logs, low: low, high: high);
    }

    final allVals = logs.map((l) => l.bloodSugar).toList();
    final minY = (allVals.reduce(math.min) - 20).clamp(0.0, double.infinity);
    final maxY = allVals.reduce(math.max) + 30;

    return LayoutBuilder(builder: (context, constraints) {
      return SizedBox(
        height: 220,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Y-axis labels
            SizedBox(
              width: 36,
              child: AgpYAxis(
                minY: minY, maxY: maxY, isDark: isDark,
                labels: const [54, 108, 162, 216, 270],
              ),
            ),
            // Chart area
            Expanded(
              child: Column(
                children: [
                  Expanded(
                    child: ClipRect(
                      child: CustomPaint(
                        painter: AgpPainter(
                          points: points,
                          minY: minY,
                          maxY: maxY,
                          low: low,
                          high: high,
                          isDark: isDark,
                          gridLines: const [54.0, 108.0, 162.0, 216.0, 270.0],
                        ),
                      ),
                    ),
                  ),
                  // X-axis labels
                  SizedBox(
                    height: 20,
                    child: AgpXAxis(isDark: isDark),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Simple fallback line chart (when not enough hour buckets for AGP)
// ─────────────────────────────────────────────────────────────────────────────

class _SimpleLineChart extends StatelessWidget {
  final List<LogEntryData> logs;
  final double low, high;

  const _SimpleLineChart({required this.logs, required this.low, required this.high});

  @override
  Widget build(BuildContext context) {
    final sorted = logs.reversed.toList();
    final spots  = sorted.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value.bloodSugar)).toList();
    final allVals = logs.map((l) => l.bloodSugar).toList();
    final minY = (allVals.reduce(math.min) - 20).clamp(0, double.infinity).toDouble();
    final maxY = allVals.reduce(math.max) + 30;

    return LineChart(
      LineChartData(
        minY: minY, maxY: maxY,
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (_) => const FlLine(color: AminaTheme.ink100, strokeWidth: 1),
        ),
        borderData: FlBorderData(show: false),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 36,
              getTitlesWidget: (v, _) => Text(v.toInt().toString(), style: const TextStyle(fontSize: 10, color: AminaTheme.ink400)),
            ),
          ),
          bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles:   const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        extraLinesData: ExtraLinesData(horizontalLines: [
          HorizontalLine(y: low,  color: const Color(0xFFE4A85B).withValues(alpha: 0.7), strokeWidth: 1.5, dashArray: [6, 4]),
          HorizontalLine(y: high, color: const Color(0xFFE4A85B).withValues(alpha: 0.7), strokeWidth: 1.5, dashArray: [6, 4]),
        ]),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            curveSmoothness: 0.35,
            color: AminaTheme.teal500,
            barWidth: 2,
            isStrokeCapRound: true,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, _, __, ___) {
                final v = spot.y;
                final color = v < 70 || v > 250
                    ? AminaTheme.dangerRed
                    : (v < low || v > high ? AminaTheme.accentAmber : AminaTheme.teal500);
                return FlDotCirclePainter(radius: 3, color: color, strokeWidth: 0);
              },
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                colors: [AminaTheme.teal500.withValues(alpha: 0.12), AminaTheme.teal500.withValues(alpha: 0.0)],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Event Legend (meal + insulin overlay indicators)
// ─────────────────────────────────────────────────────────────────────────────

class _EventLegend extends StatelessWidget {
  final List<LogEntryData> logs;
  const _EventLegend({required this.logs});

  @override
  Widget build(BuildContext context) {
    final mealCount    = logs.where((l) => l.mealType != null && l.mealType!.isNotEmpty).length;
    final insulinCount = logs.where((l) => (l.insulinUnits ?? 0) > 0).length;

    return Row(
      children: [
        if (mealCount > 0) ...[
          const Text('🍽', style: TextStyle(fontSize: 13)),
          const SizedBox(width: 4),
          Text('$mealCount repas', style: const TextStyle(fontSize: 11, color: AminaTheme.ink500)),
          const SizedBox(width: 16),
        ],
        if (insulinCount > 0) ...[
          const Text('💉', style: TextStyle(fontSize: 13)),
          const SizedBox(width: 4),
          Text('$insulinCount insuline', style: const TextStyle(fontSize: 11, color: AminaTheme.ink500)),
        ],
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Chips
// ─────────────────────────────────────────────────────────────────────────────

class _TimeChip extends StatelessWidget {
  final String label;
  final int value;
  final bool selected;
  final VoidCallback onTap;

  const _TimeChip({required this.label, required this.value, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
        decoration: BoxDecoration(
          color: selected ? AminaTheme.teal500 : AminaTheme.ink50,
          borderRadius: BorderRadius.circular(100),
          border: Border.all(color: selected ? AminaTheme.teal500 : AminaTheme.ink200),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            color: selected ? Colors.white : AminaTheme.ink600,
          ),
        ),
      ),
    );
  }
}

class _MealChip extends StatelessWidget {
  final String  label;
  final String? value;
  final bool    selected;
  final VoidCallback onTap;

  const _MealChip({required this.label, required this.value, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: selected ? AminaTheme.teal50 : Colors.transparent,
          borderRadius: BorderRadius.circular(100),
          border: Border.all(color: selected ? AminaTheme.teal500 : AminaTheme.ink200),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            color: selected ? AminaTheme.teal700 : AminaTheme.ink500,
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Legend item
// ─────────────────────────────────────────────────────────────────────────────

class _LegendItem extends StatelessWidget {
  final Color   color;
  final String  label;
  final double  opacity;
  final bool    dashed;

  const _LegendItem({
    required this.color,
    required this.label,
    this.opacity = 1.0,
    this.dashed  = false,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        dashed
            ? CustomPaint(
                size: const Size(20, 2),
                painter: _DashPainter(color: color.withValues(alpha: opacity)),
              )
            : Container(
                width: 20, height: 8,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: opacity),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
        const SizedBox(width: 5),
        Text(label, style: const TextStyle(fontSize: 10, color: AminaTheme.ink500)),
      ],
    );
  }
}

class _DashPainter extends CustomPainter {
  final Color color;
  const _DashPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = color..strokeWidth = 1.5;
    const dash = 4.0;
    const gap  = 3.0;
    double x = 0;
    while (x < size.width) {
      canvas.drawLine(Offset(x, size.height / 2), Offset(math.min(x + dash, size.width), size.height / 2), paint);
      x += dash + gap;
    }
  }

  @override
  bool shouldRepaint(_DashPainter old) => old.color != color;
}