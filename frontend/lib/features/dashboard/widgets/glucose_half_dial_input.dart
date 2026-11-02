import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Measurement entry. Colors are illustrative 70-180 mg/dL reference markers,
/// NOT personalized targets. Save continues through the existing journal flow.
class GlucoseHalfDialInput extends StatelessWidget {
  const GlucoseHalfDialInput({
    super.key, required this.controller, required this.unit,
    required this.valueMgdl, required this.onTextChanged,
    required this.onValueSelected, required this.onToggleUnit,
  });
  final TextEditingController controller;
  final String unit;
  final double? valueMgdl;
  final ValueChanged<String> onTextChanged;
  final ValueChanged<double> onValueSelected;
  final VoidCallback? onToggleUnit;
  static const double minScale = 40;
  static const double maxScale = 320;
  String _local(BuildContext c, String fr, String en, String ar) =>
    switch(Localizations.localeOf(c).languageCode) {
      'fr' => fr, 'ar' => ar, _ => en,
    };
  String _display(double v) =>
    unit == 'mmol/L' ? (v / 18.0).toStringAsFixed(1) : v.round().toString();

  void _select(Offset p, Size size) {
    final rel = p - Offset(size.width / 2, size.height - 11);
    // Only drag on the colored ARC. Tapping the central numeric TextField
    // must not silently overwrite the reading being edited.
    final radius = math.min(size.width / 2 - 21, size.height - 25);
    if (rel.dy > 18 || (rel.distance - radius).abs() > 30) return;
    var a = math.atan2(rel.dy, rel.dx);
    if (a < 0) a += math.pi * 2;
    final t = ((a - math.pi) / math.pi).clamp(0.0, 1.0);
    onValueSelected((minScale + t * (maxScale - minScale)).roundToDouble());
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final shown = valueMgdl?.clamp(minScale, maxScale).toDouble() ?? 140.0;
    return Column(
      key: const Key('glucose-half-dial-input'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Align(
          alignment: AlignmentDirectional.centerEnd,
          child: OutlinedButton(
            key: const Key('glucose-half-dial-unit-toggle'),
            onPressed: onToggleUnit,
            style: OutlinedButton.styleFrom(
              minimumSize: const Size(0, 44),
              padding: const EdgeInsets.symmetric(horizontal: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              Text(unit, style: const TextStyle(
                fontSize: 13, fontWeight: FontWeight.w800,
              )),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 6),
                child: Icon(Icons.swap_horiz_rounded, size: 19),
              ),
              Text(unit == 'mg/dL' ? 'mmol/L' : 'mg/dL',
                style: const TextStyle(fontSize: 12)),
            ]),
          ),
        ),
        LayoutBuilder(builder: (context, constraints) {
          final w = math.min(constraints.maxWidth, 330.0);
          final s = Size(w, w * 0.54);
          return Center(child: GestureDetector(
            key: const Key('glucose-half-dial-gesture'),
            behavior: HitTestBehavior.opaque,
            onTapDown: (e) => _select(e.localPosition, s),
            onPanUpdate: (e) => _select(e.localPosition, s),
            child: SizedBox(
              width: s.width, height: s.height,
              child: CustomPaint(
                key: const Key('glucose-half-dial-arc'),
                painter: _GlucoseArcPainter(
                  position: (shown - minScale) / (maxScale - minScale),
                  hasValue: valueMgdl != null,
                  outline: cs.outlineVariant,
                ),
                child: Align(
                  alignment: const Alignment(0, 0.68),
                  child: SizedBox(
                    width: 144,
                    child: TextField(
                      key: const Key('glucose-input'),
                      controller: controller,
                      textAlign: TextAlign.center,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: [
                        FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
                      ],
                      style: TextStyle(
                        fontSize: 37, fontWeight: FontWeight.w800,
                        color: cs.onSurface,
                      ),
                      decoration: const InputDecoration(
                        hintText: '—',
                        isDense: true,
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.fromLTRB(6, 4, 6, 4),
                      ),
                      onChanged: onTextChanged,
                    ),
                  ),
                ),
              ),
            ),
          ));
        }),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(_local(context, 'Min repère', 'Guide min', 'الحد المرجعي الأدنى') +
              ' ' + _display(70), style: TextStyle(
                fontSize: 11, color: cs.onSurfaceVariant,
              )),
          Text(_local(context, 'Max repère', 'Guide max', 'الحد المرجعي الأعلى') +
              ' ' + _display(180), style: TextStyle(
                fontSize: 11, color: cs.onSurfaceVariant,
              )),
        ]),
        Slider(
          key: const Key('glucose-half-dial-slider'),
          min: minScale, max: maxScale, divisions: 280,
          value: shown, label: _display(shown) + ' ' + unit,
          semanticFormatterCallback: (v) => _display(v) + ' ' + unit,
          onChanged: (v) => onValueSelected(v.roundToDouble()),
        ),
        Text(_local(context,
          'Rouge hors repères · orange aux limites · vert au centre. Ces couleurs ne définissent pas ta cible personnelle.',
          'Red outside guides · orange at boundaries · green in the middle. Colors are not personal targets.',
          'الأحمر خارج الحدود والبرتقالي قربها والأخضر بالوسط. هذه الألوان ليست هدفك الشخصي.',
        ),
          key: const Key('glucose-half-dial-guide-note'),
          textAlign: TextAlign.center,
          style: TextStyle(
            color: cs.onSurfaceVariant, fontSize: 11.5, height: 1.3,
          ),
        ),
      ],
    );
  }
}

class _GlucoseArcPainter extends CustomPainter {
  const _GlucoseArcPainter({
    required this.position, required this.hasValue, required this.outline,
  });
  final double position;
  final bool hasValue;
  final Color outline;
  static Color colorAt(double mg) {
    if (mg < 70 || mg > 180) return const Color(0xFFD84752);
    if (mg < 90 || mg > 160) return const Color(0xFFF1A34B);
    return const Color(0xFF27A87D);
  }
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height - 11);
    final radius = math.min(size.width / 2 - 21, size.height - 25);
    final rect = Rect.fromCircle(center: center, radius: radius);
    const n = 140;
    for (var i = 0; i < n; i++) {
      final v = GlucoseHalfDialInput.minScale +
          (i + .5) / n *
          (GlucoseHalfDialInput.maxScale - GlucoseHalfDialInput.minScale);
      canvas.drawArc(rect, math.pi + i * math.pi / n,
        math.pi / n + .004, false, Paint()
        ..color = colorAt(v)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 20,
      );
    }
    if (!hasValue) return;
    final a = math.pi + position * math.pi;
    final pos = Offset(
      center.dx + radius * math.cos(a),
      center.dy + radius * math.sin(a),
    );
    canvas.drawCircle(pos, 15, Paint()..color = outline);
    canvas.drawCircle(pos, 12, Paint()..color = Colors.white);
    canvas.drawCircle(pos, 7,
      Paint()..color = const Color(0xFF173F42));
  }
  @override
  bool shouldRepaint(covariant _GlucoseArcPainter other) =>
    position != other.position ||
    hasValue != other.hasValue ||
    outline != other.outline;
}
