import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Visual reference only, NOT the patient's prescribed glucose targets.
/// The five bands always show: red / amber / green / amber / red.
Color d22IllustrativeGlucoseArcColor(double mg) {
  if (mg < 70 || mg > 180) return const Color(0xFFCF475A);
  if (mg < 90 || mg > 160) return const Color(0xFFF0A447);
  return const Color(0xFF18A781);
}

/// A segmented dial deliberately gives more touch space to the central band.
/// Values remain physically expressed in mg/dL; this is presentation only.
/// Inverse and forward functions share the same breakpoints to avoid drift.
const _d22MgKnots = <double>[40, 70, 90, 160, 180, 320];
const _d22ArcKnots = <double>[0, .15, .29, .71, .85, 1];

double d22DialFractionForMgdl(double mg) {
  final value = mg.clamp(_d22MgKnots.first, _d22MgKnots.last).toDouble();
  for (var i = 0; i < _d22MgKnots.length - 1; i++) {
    if (value <= _d22MgKnots[i + 1]) {
      final t = (value - _d22MgKnots[i]) /
          (_d22MgKnots[i + 1] - _d22MgKnots[i]);
      return _d22ArcKnots[i] +
          t * (_d22ArcKnots[i + 1] - _d22ArcKnots[i]);
    }
  }
  return 1;
}

double d22DialMgdlForFraction(double fraction) {
  final value = fraction.clamp(0.0, 1.0).toDouble();
  for (var i = 0; i < _d22ArcKnots.length - 1; i++) {
    if (value <= _d22ArcKnots[i + 1]) {
      final t = (value - _d22ArcKnots[i]) /
          (_d22ArcKnots[i + 1] - _d22ArcKnots[i]);
      return _d22MgKnots[i] +
          t * (_d22MgKnots[i + 1] - _d22MgKnots[i]);
    }
  }
  return _d22MgKnots.last;
}

/// Actual reading input — keeps the existing journal save pipeline intact.
/// Tap/drag the half-ring, use +/- or tap the prominent CENTRAL number for
/// keyboard entry. No redundant second horizontal slider.
class GlucoseHalfDialInput extends StatelessWidget {
  const GlucoseHalfDialInput({
    super.key,
    required this.controller,
    required this.unit,
    required this.valueMgdl,
    required this.onTextChanged,
    required this.onValueSelected,
    required this.onToggleUnit,
  });

  final TextEditingController controller;
  final String unit;
  final double? valueMgdl;
  final ValueChanged<String> onTextChanged;
  final ValueChanged<double> onValueSelected;
  final VoidCallback? onToggleUnit;

  static const double minScale = 40;
  static const double maxScale = 320;

  String _copy(BuildContext context, String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr,
        'ar' => ar,
        _ => en,
      };

  String _display(double mg) =>
      unit == 'mmol/L'
          ? (mg / 18.0).toStringAsFixed(1)
          : mg.round().toString();

  void _selectArc(Offset localPoint, Size size) {
    final center = Offset(size.width / 2, size.height - 18);
    final rel = localPoint - center;
    final radius = math.min(size.width / 2 - 30, size.height - 35);
    // Ignore gestures on the center input and below the semicircle.
    // Limit the valid touch annulus to the visible band + 16px tolerance.
    if (rel.dy > 14 || (rel.distance - radius).abs() > 34) return;
    var radians = math.atan2(rel.dy, rel.dx);
    if (radians < 0) radians += math.pi * 2;
    if (radians < math.pi || radians > 2 * math.pi) return;
    final fraction = (radians - math.pi) / math.pi;
    final mg = d22DialMgdlForFraction(fraction).roundToDouble();
    if (mg != valueMgdl) {
      onValueSelected(mg);
      HapticFeedback.selectionClick();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final selected = valueMgdl?.clamp(minScale, maxScale).toDouble();
    final displayed = selected ?? 140.0;
    final step = unit == 'mmol/L' ? 1.8 : 1.0;

    void adjust(int direction) {
      final mg = ((selected ?? 140) + direction * step)
          .clamp(minScale, maxScale)
          .toDouble();
      onValueSelected(mg);
      HapticFeedback.selectionClick();
    }

    return Column(
      key: const Key('glucose-half-dial-input'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                _copy(context, 'SAISIE DIRECTE', 'DIRECT INPUT', 'إدخال مباشر'),
                style: theme.textTheme.labelSmall?.copyWith(
                  color: colors.onSurfaceVariant,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1,
                ),
              ),
            ),
            OutlinedButton(
              key: const Key('glucose-half-dial-unit-toggle'),
              onPressed: onToggleUnit,
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(0, 46),
                padding: const EdgeInsets.symmetric(horizontal: 12),
                side: BorderSide(color: colors.outlineVariant),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(13),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(unit, style: const TextStyle(
                    fontWeight: FontWeight.w800, fontSize: 13,
                  )),
                  const SizedBox(width: 7),
                  const Icon(Icons.swap_horiz_rounded, size: 19),
                  Text(unit == 'mg/dL' ? 'mmol/L' : 'mg/dL',
                      style: const TextStyle(fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        LayoutBuilder(builder: (context, limits) {
          final width = math.min(limits.maxWidth, 354.0);
          final size = Size(width, width * .59);
          return Center(
            child: SizedBox(
              key: const Key('glucose-half-dial-gesture'),
              width: size.width,
              height: size.height,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Positioned.fill(
                    child: GestureDetector(
                      key: const Key('glucose-half-dial-touch-surface'),
                      behavior: HitTestBehavior.opaque,
                      onTapDown: (event) =>
                          _selectArc(event.localPosition, size),
                      onPanStart: (event) =>
                          _selectArc(event.localPosition, size),
                      onPanUpdate: (event) =>
                          _selectArc(event.localPosition, size),
                      child: Semantics(
                        label: _copy(context,
                          'Sélecteur de glycémie par demi-cercle',
                          'Semicircle glucose input',
                          'محدد الغلوكوز نصف الدائري',
                        ),
                        value: valueMgdl == null
                            ? _copy(context, 'Aucune valeur', 'No value', 'لا قيمة')
                            : _display(valueMgdl!) + ' ' + unit,
                        increasedValue:
                            _display((displayed + step).clamp(minScale, maxScale).toDouble()) + ' ' + unit,
                        decreasedValue:
                            _display((displayed - step).clamp(minScale, maxScale).toDouble()) + ' ' + unit,
                        onIncrease: () => adjust(1),
                        onDecrease: () => adjust(-1),
                        child: CustomPaint(
                          key: const Key('glucose-half-dial-arc'),
                          painter: _PremiumGlucoseArcPainter(
                            fraction: d22DialFractionForMgdl(displayed),
                            hasValue: selected != null,
                            outline: colors.outlineVariant,
                            dark: theme.brightness == Brightness.dark,
                          ),
                        ),
                      ),
                    ),
                  ),
                  // Central editing surface does NOT forward taps to the arc.
                  Positioned(
                    left: 38,
                    right: 38,
                    bottom: 0,
                    child: Container(
                      key: const Key('glucose-half-dial-edit-center'),
                      padding: const EdgeInsets.fromLTRB(6, 8, 6, 6),
                      decoration: BoxDecoration(
                        color: colors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: colors.outlineVariant,
                          width: 1.2,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: .05),
                            blurRadius: 18,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          _stepButton(
                            key: const Key('glucose-half-dial-minus'),
                            icon: Icons.remove_rounded,
                            tooltip: _copy(context, 'Diminuer', 'Decrease', 'إنقاص'),
                            onPressed: () => adjust(-1),
                            color: colors,
                          ),
                          const SizedBox(width: 2),
                          Expanded(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                TextField(
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
                                    fontSize: 35,
                                    height: 1.08,
                                    letterSpacing: -1.2,
                                    fontWeight: FontWeight.w800,
                                    color: colors.onSurface,
                                  ),
                                  decoration: const InputDecoration(
                                    hintText: '—',
                                    isDense: true,
                                    contentPadding: EdgeInsets.zero,
                                    border: InputBorder.none,
                                  ),
                                  onChanged: onTextChanged,
                                ),
                                const SizedBox(height: 2),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(unit, style: theme.textTheme.labelSmall?.copyWith(
                                      color: colors.onSurfaceVariant,
                                      fontWeight: FontWeight.w700,
                                    )),
                                    const SizedBox(width: 4),
                                    Icon(Icons.edit_rounded,
                                        color: colors.onSurfaceVariant,
                                        size: 12),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 2),
                          _stepButton(
                            key: const Key('glucose-half-dial-plus'),
                            icon: Icons.add_rounded,
                            tooltip: _copy(context, 'Augmenter', 'Increase', 'زيادة'),
                            onPressed: () => adjust(1),
                            color: colors,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _boundaryLabel(context, colors,
                _copy(context, 'Repère bas', 'Lower guide', 'الحد المرجعي الأدنى'),
                _display(70)),
            _boundaryLabel(context, colors,
                _copy(context, 'Repère haut', 'Upper guide', 'الحد المرجعي الأعلى'),
                _display(180)),
          ],
        ),
        const SizedBox(height: 13),
        Text(
          _copy(context,
            'Glisse sur l’arc ou touche le nombre pour le modifier.',
            'Drag the arc or tap the number to edit it.',
            'حرّك المؤشر على القوس أو المس الرقم لتعديله.',
          ),
          key: const Key('glucose-half-dial-instruction'),
          textAlign: TextAlign.center,
          style: theme.textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w600,
            color: colors.onSurface,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          _copy(context,
            'Rouge hors repères · orange aux limites · vert au centre. Repères généraux, pas ta cible personnelle.',
            'Red outside guides · amber at boundaries · green between. General guides, not your personal target.',
            'الأحمر خارج الحدود والبرتقالي قربها والأخضر بينهما. مؤشرات عامة وليست هدفك الشخصي.',
          ),
          key: const Key('glucose-half-dial-guide-note'),
          textAlign: TextAlign.center,
          style: theme.textTheme.bodySmall?.copyWith(
            fontSize: 11,
            height: 1.4,
            color: colors.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _boundaryLabel(BuildContext context, ColorScheme colors,
      String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: colors.onSurfaceVariant, fontSize: 10,
        )),
        Text(value + ' ' + unit,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: colors.onSurface,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }

  Widget _stepButton({
    required Key key, required IconData icon, required String tooltip,
    required VoidCallback onPressed, required ColorScheme color,
  }) {
    return IconButton(
      key: key,
      tooltip: tooltip,
      onPressed: onPressed,
      icon: Icon(icon, size: 19),
      color: color.onSurface,
      style: IconButton.styleFrom(
        backgroundColor: color.surfaceContainerHighest,
        minimumSize: const Size(38, 42),
        padding: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}

class _PremiumGlucoseArcPainter extends CustomPainter {
  const _PremiumGlucoseArcPainter({
    required this.fraction,
    required this.hasValue,
    required this.outline,
    required this.dark,
  });

  final double fraction;
  final bool hasValue;
  final Color outline;
  final bool dark;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height - 18);
    final radius = math.min(size.width / 2 - 30, size.height - 35);
    final rect = Rect.fromCircle(center: center, radius: radius);
    const segments = 210;

    // Recessed track, then 5 contiguous colored bands.
    canvas.drawArc(rect, math.pi, math.pi, false, Paint()
      ..color = outline.withValues(alpha: .38)
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 32);

    for (var i = 0; i < segments; i++) {
      final f = (i + .5) / segments;
      final color = d22IllustrativeGlucoseArcColor(
          d22DialMgdlForFraction(f));
      canvas.drawArc(
        rect,
        math.pi + i * math.pi / segments,
        math.pi / segments + .005,
        false,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = 25,
      );
    }

    // Visual separators indicate the exact 70, 90, 160, 180 boundaries.
    for (final mg in [70.0, 90.0, 160.0, 180.0]) {
      final a = math.pi + d22DialFractionForMgdl(mg) * math.pi;
      final pos = Offset(
        center.dx + radius * math.cos(a),
        center.dy + radius * math.sin(a),
      );
      canvas.drawCircle(pos, 2.0,
          Paint()..color = Colors.white.withValues(alpha: .9));
    }

    if (!hasValue) return;
    final theta = math.pi + fraction * math.pi;
    final cursor = Offset(
      center.dx + radius * math.cos(theta),
      center.dy + radius * math.sin(theta),
    );
    final haloColor = dark ? const Color(0xFF142C2A) : const Color(0xFF164F47);
    canvas.drawCircle(cursor, 22, Paint()
      ..color = haloColor.withValues(alpha: .16)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 7));
    canvas.drawCircle(cursor, 16, Paint()..color = Colors.white);
    canvas.drawCircle(cursor, 12, Paint()..color = haloColor);
    canvas.drawCircle(cursor, 4, Paint()..color = Colors.white);
  }

  @override
  bool shouldRepaint(covariant _PremiumGlucoseArcPainter old) =>
      fraction != old.fraction || hasValue != old.hasValue ||
      outline != old.outline || dark != old.dark;
}
