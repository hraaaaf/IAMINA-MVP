import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'd22_glucose_quantity_candidate.dart';

/// D22 Web-only interactive UI proposal. All values are illustrative and
/// ephemeral: this component must never persist legacy or clinical targets.
class D22TargetDialPreview extends StatefulWidget {
  const D22TargetDialPreview({
    super.key, required this.unit, required this.onUnitChanged,
  });
  final String unit;
  final ValueChanged<String> onUnitChanged;

  @override
  State<D22TargetDialPreview> createState() => _D22TargetDialPreviewState();
}

class _D22TargetDialPreviewState extends State<D22TargetDialPreview> {
  double _low = 95;
  double _high = 165;
  bool _editingLow = true;
  static const _min = 60.0;
  static const _max = 280.0;
  String _copy(String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr, 'ar' => ar, _ => en,
      };
  String _format(double mg) => widget.unit == 'mmol/L'
      ? (mg / d22CandidateMgDlPerMmolL).toStringAsFixed(1)
      : mg.round().toString();
  double get _active => _editingLow ? _low : _high;

  void _update(double fraction) {
    final mg = (_min + fraction.clamp(0.0, 1.0) * (_max - _min))
        .roundToDouble();
    setState(() {
      if (_editingLow) {
        _low = mg.clamp(_min, _high - 10).toDouble();
      } else {
        _high = mg.clamp(_low + 10, _max).toDouble();
      }
    });
  }

  void _gesture(Offset point, Size size) {
    final center = Offset(size.width / 2, size.height - 13);
    final relative = point - center;
    if (relative.dy > 16) return;
    var angle = math.atan2(relative.dy, relative.dx);
    if (angle < 0) angle += math.pi * 2;
    _update((angle - math.pi) / math.pi);
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final cs = t.colorScheme;
    final label = _editingLow
        ? _copy('Minimum', 'Minimum', 'الحد الأدنى')
        : _copy('Maximum', 'Maximum', 'الحد الأقصى');
    return Container(
      key: const Key('d22-dial-preview'),
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 16),
      decoration: BoxDecoration(
        color: cs.surfaceContainerLow,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: cs.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(children: [
            Expanded(child: Text(
              _copy('APERÇU INTERACTIF', 'INTERACTIVE PREVIEW', 'معاينة تفاعلية'),
              style: t.textTheme.labelSmall?.copyWith(
                color: cs.onSurfaceVariant,
                fontWeight: FontWeight.w800, letterSpacing: 0.8,
              ),
            )),
            OutlinedButton(
              key: const Key('d22-dial-unit-toggle'),
              onPressed: () => widget.onUnitChanged(
                widget.unit == 'mg/dL' ? 'mmol/L' : 'mg/dL',
              ),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(0, 44),
                padding: const EdgeInsets.symmetric(horizontal: 10),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Text('mg/dL', style: TextStyle(
                  fontSize: 12, fontWeight: widget.unit == 'mg/dL'
                      ? FontWeight.w800 : FontWeight.w400,
                )),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 5),
                  child: Icon(Icons.swap_horiz, size: 17),
                ),
                Text('mmol/L', style: TextStyle(
                  fontSize: 12, fontWeight: widget.unit == 'mmol/L'
                      ? FontWeight.w800 : FontWeight.w400,
                )),
              ]),
            ),
          ]),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(child: _tab(
              const Key('d22-dial-select-min'),
              _copy('Minimum', 'Minimum', 'الحد الأدنى'),
              _low, _editingLow, () => setState(() => _editingLow = true),
            )),
            const SizedBox(width: 10),
            Expanded(child: _tab(
              const Key('d22-dial-select-max'),
              _copy('Maximum', 'Maximum', 'الحد الأقصى'),
              _high, !_editingLow, () => setState(() => _editingLow = false),
            )),
          ]),
          const SizedBox(height: 12),
          LayoutBuilder(builder: (context, constraints) {
            final w = math.min(350.0, constraints.maxWidth);
            final size = Size(w, w * 0.54);
            return Center(child: GestureDetector(
              key: const Key('d22-dial-arc-gesture'),
              behavior: HitTestBehavior.opaque,
              onTapDown: (d) => _gesture(d.localPosition, size),
              onPanUpdate: (d) => _gesture(d.localPosition, size),
              child: SizedBox(
                width: size.width, height: size.height,
                child: CustomPaint(
                  key: const Key('d22-dial-arc'),
                  painter: _HalfDialPainter(
                    low: (_low - _min) / (_max - _min),
                    high: (_high - _min) / (_max - _min),
                    editingLow: _editingLow,
                  ),
                  child: Align(
                    alignment: const Alignment(0, 0.65),
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      Text(_format(_active),
                        key: const Key('d22-dial-active-value'),
                        style: t.textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      Text(label + ' · ' + widget.unit,
                        style: t.textTheme.labelSmall?.copyWith(
                          color: cs.onSurfaceVariant,
                        ),
                      ),
                    ]),
                  ),
                ),
              ),
            ));
          }),
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              activeTrackColor: cs.primary,
              inactiveTrackColor: cs.outlineVariant,
              thumbColor: cs.primary,
            ),
            child: Slider(
              key: const Key('d22-dial-accessible-slider'),
              value: _active,
              min: _min, max: _max, divisions: 220,
              label: _format(_active) + ' ' + widget.unit,
              semanticFormatterCallback: (v) =>
                  label + ' ' + _format(v) + ' ' + widget.unit,
              onChanged: (v) => _update((v - _min) / (_max - _min)),
            ),
          ),
          Text(
            _copy(
              'Fais glisser le curseur ou touche le demi-cercle.',
              'Drag the slider or tap the semicircle.',
              'حرّك المؤشر أو المس نصف الدائرة.',
            ),
            textAlign: TextAlign.center,
            style: t.textTheme.bodySmall?.copyWith(
              color: cs.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            _copy(
              'Maquette uniquement : valeurs non enregistrées. Les couleurs ne sont pas un avis médical.',
              'Visual demo only: values are not saved. Colors are not a medical assessment.',
              'معاينة فقط: القيم غير محفوظة، والألوان ليست تقييماً طبياً.',
            ),
            key: const Key('d22-dial-nonclinical-disclaimer'),
            textAlign: TextAlign.center,
            style: t.textTheme.bodySmall?.copyWith(
              color: cs.onSurfaceVariant, fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }

  Widget _tab(Key key, String label, double value, bool selected,
      VoidCallback onTap) {
    final cs = Theme.of(context).colorScheme;
    return Material(
      color: selected ? cs.primaryContainer : cs.surface,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        key: key,
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 5),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: selected ? cs.primary : cs.outlineVariant,
              width: selected ? 1.5 : 1,
            ),
          ),
          child: Column(children: [
            Text(label, style: TextStyle(
              fontSize: 12, color: cs.onSurfaceVariant,
            )),
            const SizedBox(height: 4),
            Text(_format(value) + ' ' + widget.unit, style: TextStyle(
              fontWeight: FontWeight.w800, fontSize: 15, color: cs.onSurface,
            )),
          ]),
        ),
      ),
    );
  }
}

class _HalfDialPainter extends CustomPainter {
  const _HalfDialPainter({
    required this.low, required this.high, required this.editingLow,
  });
  final double low;
  final double high;
  final bool editingLow;
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height - 13);
    final radius = math.min(size.width / 2 - 23, size.height - 29);
    final rect = Rect.fromCircle(center: center, radius: radius);
    const colors = [
      Color(0xFFD94F55), Color(0xFFF2A44B), Color(0xFF34AB84),
    ];
    for (var i = 0; i < colors.length; i++) {
      canvas.drawArc(rect, math.pi + i * math.pi / 3,
        math.pi / 3 + 0.002, false, Paint()
          ..color = colors[i]
          ..style = PaintingStyle.stroke
          ..strokeWidth = 21,
      );
    }
    void marker(double fraction, bool active) {
      final theta = math.pi + fraction * math.pi;
      final pos = Offset(center.dx + radius * math.cos(theta),
          center.dy + radius * math.sin(theta));
      canvas.drawCircle(pos, active ? 13 : 9,
          Paint()..color = Colors.white);
      canvas.drawCircle(pos, active ? 8 : 5,
          Paint()..color = const Color(0xFF183B45));
    }
    marker(low, editingLow);
    marker(high, !editingLow);
  }
  @override
  bool shouldRepaint(covariant _HalfDialPainter other) =>
      low != other.low || high != other.high ||
      editingLow != other.editingLow;
}
